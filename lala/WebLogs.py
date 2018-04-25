from datetime import datetime

import re
import time
import subprocess as sp
import urllib
import os
import gzip
from io import BytesIO
import socket

import pygeoip
import pandas
import proglog
from pdf_reports import pug_to_html, write_report

from .conf import conf

import numpy as np
from matplotlib import cm
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

try:
    import cartopy
    import cartopy.io.shapereader as shpreader
    import cartopy.crs as ccrs
    shpfilename = shpreader.natural_earth(resolution='110m',
                                          category='cultural',
                                          name='admin_0_countries')
    reader = shpreader.Reader(shpfilename)
    countries = list(reader.records())
    name_to_geometry = {
        country.attributes[e]: country.geometry
        for country in countries
        for e in ('ADM0_A3', 'BRK_NAME')
    }
    name_to_extent = {
        name: geometry.bounds
        for name, geometry in name_to_geometry.items()
    }
    CARTOPY_INSTALLED = True

except ImportError:
    name_to_geometry = None
    name_to_extent = None
    cartopy = None
    ccrs = None
    CARTOPY_INSTALLED = False


if not os.path.exists(conf['geolite_path']):
    response = urllib.request.urlopen(conf['geolite_url'])
    geolite_gz = response.read()
    geolite_bites = BytesIO(geolite_gz)
    with gzip.open(geolite_bites, 'rb') as f:
        geolite_content = f.read()
    if not os.path.exists(conf['data_dir']):
        os.makedirs(conf['data_dir'])
    with open(conf['geolite_path'], 'wb') as f:
        f.write(geolite_content)

geoip = pygeoip.GeoIP(conf['geolite_path'])

durations = {
    'second': 1,
    'minute': 60,
    'hour': 60 * 60,
    'day': 60 * 60 * 24,
    'week': 60 * 60 * 24 * 7,
    'month': 60 * 60 * 24 * 30,
    'year': 60 * 60 * 24 * 365,
}
def time_of_last(num, duration):
    """Returns the EPOCH time (in seconds) of XX ago (relative to the present).

    Examples
    --------

    >>> time_of_last(2, 'week') # => EPOCH time of two weeks ago
    >>> time_of_last(5, 'hour') # => EPOCH time of five hours ago
    """
    return time.time() - num * durations[duration]

def get_remote_file_content(filename='/var/log/nginx/access.log',
                            host='localhost', user='root', decode='utf8',
                            target=None):
    """
    Parameters
    ----------

    filename
      path to the file in the host machine

    host
      IP address or domain name of the host.

    user
      Username on the host.

    decode
      If not None, the file content received from the server will be
      decoded into a string using this format.
    """
    proc = sp.Popen(['ssh', '%s@%s' % (user, host), 'cat %s' % filename],
                    stderr=sp.PIPE, stdout=sp.PIPE)
    out, err = proc.communicate()
    if len(err):
        raise IOError(err)
    if decode is not None:
        out = out.decode(decode)
    if target is not None:
        with open(target, "w") as f:
            f.write(out)
    return out

def init_map(figsize=(12, 8),  extent=(-150, 60, -25, 60)):
    """Initialize a world map with the given dimensions.

    ``figsize`` is the figure's size in inches. ``extent`` is the boundaries
    of the map, in its own PlateCarree coordinates.
    """
    if not CARTOPY_INSTALLED:
        raise ImportError('This feature requires Cartopy installed.')
    ax = plt.axes(projection=cartopy.crs.PlateCarree())
    ax.add_feature(cartopy.feature.LAND)
    ax.add_feature(cartopy.feature.OCEAN)
    ax.add_feature(cartopy.feature.COASTLINE)
    ax.add_feature(cartopy.feature.BORDERS, linestyle='-', alpha=.5)

    ax.set_extent(extent)
    ax.figure.set_size_inches(figsize)
    return ax

class WebLogs(pandas.DataFrame):
    "Custom Pandas dataframe class for reading web logs."
    def __init__(self, *args, **kw):
        super(WebLogs, self).__init__(*args, **kw)

    @property
    def _constructor(self):
        return WebLogs

    @staticmethod
    def from_nginx_weblogs(filepath=None, log_lines=None):
        """Return a dataframe of access log entries, from lines of NGINX logs.

        The log_lines are a list of strings, each representing one access
        logged by NGINX.
        """
        if log_lines is None:
            with open(filepath, 'r') as f:
                log_lines = f.read().split("\n")
        regexpr = r'(.*) -(.*) - \[(.*)\] "(.*)" (\d+) (\d+) "(.*)" "(.*)"'
        regexpr = re.compile(regexpr)
        errored_lines = []
        records = []
        for i, line in enumerate(log_lines):
            match = re.match(regexpr, line)
            fields = ('IP', 'stuff', 'date', 'request', 'response', 'status',
                      'referrer', 'browser')
            if match is None:
                errored_lines.append(i)
            else:
                records.append(dict(zip(fields, match.groups())))
        weblogs = WebLogs.from_records(records)
        weblogs['parsed_date'] = [
            datetime.strptime(s, '%d/%b/%Y:%H:%M:%S %z')
            for s in weblogs['date']
        ]
        weblogs['timestamp'] = [x.timestamp()
                                for x in weblogs['parsed_date']]
        fields = ['country_name', 'city', 'country_code3', 'latitude',
                  'longitude']
        d = {f: [] for f in fields}
        for ip in weblogs.IP:
            rec = geoip.record_by_addr(ip)
            if rec is None:
                rec = {field: None for field in fields}
            for field in fields:
                d[field].append(rec[field])
        for field in fields:
            weblogs[field] = d[field]

        methods, urls, https = zip(*[
            request.split()
            if len(request.split()) == 3
            else (None, None, None)
            for request in weblogs.request
        ])
        for name, data in [('method', methods),
                           ('url', urls),
                           ('http', https)]:
            weblogs[name] = data

        return weblogs, errored_lines

    @staticmethod
    def from_weblogs_spreadsheet(filepath=None):
        if filepath.lower().endswith((".csv")):
            dataframe = pandas.read_csv(filepath)
        else:
            dataframe = pandas.read_excel(filepath)
        return WebLogs(dataframe)


    def identify_ips_domains(self, logger='bar', known_ips=None):
        """Add a `ip_owner` column to self."""
        if isinstance(known_ips, pandas.DataFrame):
            known_ips = {
                row.IP: row.domain
                for i, row in known_ips.iterrows()
            }
        if known_ips is None:
            known_ips = {}
        if logger == 'bar':
            logger = proglog.TqdmProgressBarLogger()

        ips_domains = {}
        for ip in logger.iter_bar(ip=list(set(self.IP))):
            if ip in known_ips:
                ips_domains[ip] = known_ips[ip]
            else:
                try:
                    ips_domains[ip] = known_ips[ip] = socket.getfqdn(ip)
                except socket.herror:
                    ips_domains[ip] = 'Unknown'
        self.loc[:, 'domain'] = [ips_domains[ip] for ip in self.IP]
        return known_ips

    def blacklist_ips(self, ips_blacklist):
        """Return a new version of self minus the blacklisted ips."""
        ips_set = set(self.IP)
        blacklisted_ips = set([
           ip for ip in ips_set
           if ip in ips_blacklist
        ])
        return self[[
            ip not in blacklisted_ips
            for ip in self.IP
        ]]

    def entries_last(self, num, duration):
        """Returns the weblogs of the latest entries up to XX ago.

        Examples
        --------

        >>> # Filter out all entries more than 1 hour old
        >>> last_hour_weblogs = self.entries_last(1, 'hour')
        >>> # Filter out all entries more than 5 days old
        >>> last_days_weblogs = self.entries_last(5, 'days')
        """
        return self[self.timestamp >= time_of_last(num, duration)]

    def filter_by_text_search(self, terms, are_in=None, not_in=None):
        """Return a filtered version of self based on searched terms.
        """

        if not_in is not None:
            field = not_in
            def filtr(v):
                return (v is not None) and isinstance(v, str) and not any([
                    term in v for term in terms
                ])
        else:
            field = are_in
            def filtr(v):
                return (v is not None) and isinstance(v, str) and any([
                    term in v for term in terms
                ])
        field_dict = {
            val: filtr(val)
            for val in set(self[field])
        }
        indices = [field_dict[v] for v in self[field]]
        return self[indices]

    def cluster_dates(self, max_interval=60):
        dates_intervals = [[self.parsed_date[0], self.parsed_date[0]]]
        for date in self.parsed_date[1:]:
            interval = (date - dates_intervals[-1][-1]).total_seconds()
            if interval < max_interval:
                dates_intervals[-1][-1] = date
            else:
                dates_intervals.append([date, date])
        return dates_intervals

    def visitors_and_visits(self, max_visits_interval=60, per='IP'):
        return {
            ip: df.cluster_dates(max_interval=max_visits_interval)
            for ip, df in self.groupby(per)
            if ip is not None
        }

    def most_frequent_visitors(self, criterion='n_visits', n_visitors='all',
                               max_visits_interval=60, per='IP'):
        visitors = self.visitors_and_visits(
            max_visits_interval=max_visits_interval, per=per)
        if n_visitors == 'all':
            n_visitors = len(visitors.keys())

        criterion_function = {
            'n_visits': lambda visits: len(visits),
            'time_spent': lambda visits: sum([(v[1] - v[0]).total_seconds()
                                              for v in visits]) / 60.0
        }[criterion]

        return sorted([
            (criterion_function(visits), visitor)
            for visitor, visits in visitors.items()
        ])[::-1][:n_visitors]

    def visitors_locations(self):
        return {
            ip: " ".join([
                df.iloc[0].city if df.iloc[0].city else "",
                df.iloc[0].country_name if df.iloc[0].country_name else ""
            ])
            for ip, df in self.groupby('IP')
        }


    def countries_colormap(self, mini='auto', maxi='auto', ax=None):
        """Plot a colormap of different countries, return the Matplotlib ax.

        Parameters
        ----------
        country_values
          A list of couples (coutry_name, value)

        mini, maxi
          Extreme values leading to read or white colors. Leave to auto to adjust
          this range to the values of country_values.

        ax
          A Matplotlib ax with a representation of the world. If None, one is
          created automatically
        """
        if not CARTOPY_INSTALLED:
            raise ImportError('This feature requires Cartopy installed.')
        country_values = self.country_name.value_counts()
        countries = country_values.index
        values = country_values.values
        if mini == 'auto':
            mini = values.min()
        if maxi == 'auto':
            maxi = values.max()
        values = (values - mini) / (maxi - mini)
        country_values = zip(countries, values)

        if ax is None:
            ax = init_map(figsize=(12, 8), extent=(-150, 60, -25, 60))
        for (country_name, value) in country_values:
            if country_name not in name_to_geometry:
                continue
            color = cm.YlOrBr(value)
            ax.add_geometries(name_to_geometry[country_name], ccrs.PlateCarree(),
                              facecolor=color)
        return ax


    def plot_geo_positions(self, ax=None, country_colors=True):
        """Plot circles on a map around positions of the entries in the access log.

        Parameters
        ----------

        ax
          Matplotlib ax with a representation of the world.
        """
        if not CARTOPY_INSTALLED:
            raise ImportError('This feature requires Cartopy installed.')
        if ax is None:
            ax = init_map(figsize=(12, 8), extent=(-150, 60, -25, 60))
        if country_colors:
            self.countries_colormap(mini='auto', maxi='auto', ax=ax)

        counts = [
            (len(dataframe_), ll)
            for (ll, dataframe_) in self.groupby(['longitude', 'latitude'])
        ]
        counts, xy = zip(*(sorted(counts)[::-1]))
        counts = 1.0 * np.array(counts)
        counts = np.maximum(5, 600 * counts / counts.max())
        xx, yy = [list(e) for e in zip(*xy)]
        ax.scatter(xx, yy, c='w', s=counts, zorder=2000, linewidths=2,
                   edgecolor='k', transform=ccrs.Geodetic())
        return ax


    def plot_piechart(self, column, ax=None):
        """Plot circles on a map around positions of the entries in the access log.

        Parameters
        ----------

        column
           name of the column to plot

        ax
          Matplotlib ax on which to plot the pie chart. If None, one is created
          automatically.
        """
        count = self[column].value_counts()
        if ax is None:
            fig, ax = plt.subplots(1)
        ax = count.plot(kind='pie', ax=ax)
        ax.set_aspect('equal')
        ax.set_ylabel('')
        return ax, count


    def plot_timeline(self, bins_per_day=4, ax=None):
        """Plot a time profile of access.

        Parameters
        ----------

        bins_per_day
           number of time points per day.

        ax
          Matplotlib ax on which to plot the profile. If None, one is created
          automatically.
        """
        mini, maxi = self['timestamp'].min(), self['timestamp'].max()
        bins = int(bins_per_day * (maxi - mini) / durations['day'])
        if ax is None:
            fig, ax = plt.subplots(1, figsize=(12, 3))
        self['timestamp'].plot(kind='hist', bins=bins, alpha=0.6)
        x_ticks = ax.get_xticks()
        xlabels = [datetime.fromtimestamp(int(x)).strftime('%Y-%m-%d')
                   for x in x_ticks]
        ax.set_xticklabels(xlabels, rotation=45)
        ax.set_xlim(mini, maxi)
        ax.set_ylabel('occurences')
        return ax



    def plot_most_frequent_visitors(self, plot_ips=True, n_visitors='all',
                                    criterion='n_visits'):
        visitors_locations = self.visitors_locations()
        most_frequent = self.most_frequent_visitors(
            criterion=criterion, n_visitors=n_visitors)
        label = {
            'n_visits': 'Number of visits',
            'time_spent': 'Time spent (mins)'
        }[criterion]
        fig, ax = plt.subplots(1)
        scores, visitors = zip(*most_frequent)
        if visitors_locations is not None:
            visitors = [
                v + " - " + visitors_locations[v]
                for v in visitors
            ]
        ticks = list(range(len(scores)))[::-1]
        ax.bar(left=1, height=0.5, bottom=ticks, width=scores,
               tick_label=visitors if plot_ips else None,
               orientation='horizontal', alpha=0.6)

        # Hide the right and top spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        # Only show ticks on the left and bottom spines
        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')
        ax.set_xlabel(label)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        if not plot_ips:
            ax.set_ylabel('Visitors')
        return ax

    def write_report(self, template_path=None, template_string=None,
                  target=None, stylesheets=(), **context):
        html = pug_to_html(path=template_path,
                           string=template_string,
                           weblogs=self, **context)
        return write_report(html, target=target, extra_stylesheets=stylesheets)
