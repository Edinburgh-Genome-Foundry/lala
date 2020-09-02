.. image:: https://raw.githubusercontent.com/Edinburgh-Genome-Foundry/lala/master/docs/_static/images/logo.png
   :width: 200 px
   :alt: alternate text
   :align: center

|

.. image:: https://travis-ci.org/Edinburgh-Genome-Foundry/lala.svg?branch=master
   :target: https://travis-ci.org/Edinburgh-Genome-Foundry/lala
   :alt: Travis CI build status

.. image:: https://coveralls.io/repos/github/Edinburgh-Genome-Foundry/lala/badge.svg?branch=master
   :target: https://coveralls.io/github/Edinburgh-Genome-Foundry/lala?branch=master


Lala is a Python library for access log analysis. It provides a set of methods to retrieve, parse and analyze access logs (only from NGINX for now), and makes it easy to plot geo-localization or time-series data. Think of it as a simpler, Python-automatable version of Google Analytics, to make reports like this:

.. image:: https://raw.githubusercontent.com/Edinburgh-Genome-Foundry/lala/master/docs/_static/images/report.jpeg
   :width: 550 px
   :alt: alternate text
   :align: center


Usage
-----

.. code:: python

    from lala import WebLogs
    weblogs, errored_lines = WebLogs.from_nginx_weblogs('access_logs.txt')

Similarly, to fetch logs on a distant server (for which you have access keys)
you would write:

.. code:: python

    from lala import get_remote_file_content, WebLogs

    logs= lala.get_remote_file_content(
        host="cuba.genomefoundry.org", user='root',
        filename='/var/log/nginx_cuba/access.log'
    )
    weblogs, errors = WebLogs.from_nginx_weblogs(logs.split('\n'))

Now ``weblogs`` is a scpecial kind of `Pandas <https://pandas.pydata.org/>`_ dataframe where each row is one server access, with fields such as ``IP``, ``date``, ``referrer``, ``country_name``, etc.

.. image:: https://raw.githubusercontent.com/Edinburgh-Genome-Foundry/lala/master/docs/_static/images/dataframe_example.png
   :width: 800 px
   :alt: alternate text
   :align: center

The web logs can therefore be analyzed using any of Pandas' built-in filtering and plotting functions. The ``WebLogs`` class also provides additional methods which are particularly useful to analyse web logs, for instance to plot pie-charts:

.. code:: python

    ax, country_values = weblogs.plot_piechart('country_name')

.. image:: https://raw.githubusercontent.com/Edinburgh-Genome-Foundry/lala/master/examples/basic_example_piechart.png
   :width: 300 px
   :alt: alternate text
   :align: center

Next we plot the location (cities) providing the most connexions:

.. code:: python

    ax = weblogs.plot_geo_positions()

.. image:: https://raw.githubusercontent.com/Edinburgh-Genome-Foundry/lala/master/examples/basic_example_worldmap.png
   :width: 700 px
   :alt: alternate text
   :align: center

We can also restrict the entries to the UK, and plot a timeline of connexions:

.. code:: python

    uk_entries = weblogs[weblogs.country_name == 'United Kingdom']
    ax = uk_entries.plot_timeline(bins_per_day=2)

.. image:: https://raw.githubusercontent.com/Edinburgh-Genome-Foundry/lala/master/examples/basic_example_timeline.png
   :width: 700 px
   :alt: alternate text
   :align: center

Here is how to get the visitors a list of visitors and visits, sort out the most frequent visitors, find their locations, and plot it all:

.. code:: python

    visitors = weblogs.visitors_and_visits()
    visitors_locations = weblogs.visitors_locations()
    frequent_visitors = weblogs.most_frequent_visitors(n_visitors=5)
    ax = weblogs.plot_most_frequent_visitors(n_visitors=5)

.. image:: https://raw.githubusercontent.com/Edinburgh-Genome-Foundry/lala/master/examples/basic_example_frequent_visitors.png
   :width: 450 px
   :alt: alternate text
   :align: center

Lala can do more, such as identifying the domain name of the visitors, which can be used to filter out the robots of search engines:


.. code:: python

    weblogs.identify_ips_domains()
    filtered_entries = weblogs.filter_by_text_search(
        terms=['googlebot', 'spider.yandex', 'baidu', 'msnbot'],
        not_in='domain'
    )

Lala also plays nicely with the `PDF Reports <https://github.com/Edinburgh-Genome-Foundry/pdf_reports>`_ library to let you define report templates such as `this one <https://github.com/Edinburgh-Genome-Foundry/lala/blob/master/examples/data/example_template.pug>`_ (written in Pug), and then generate `this PDF report <https://github.com/Edinburgh-Genome-Foundry/lala/blob/master/examples/report_example.pdf>`_ with the following code:

.. code:: python

    weblogs.write_report(template_path="path/to/template.pug",
                         target="report_example.pdf")

Installation
-------------

You can install lala through PIP

.. code:: bash

    sudo pip install python-lala

Alternatively, you can unzip the sources in a folder and type

.. code:: bash

    sudo python setup.py install

For plotting maps you will need Cartopy which is not always easy to install - it may depend on your system. If you are on Ubuntu 16+, first install the dependencies with:

.. code:: bash

    sudo apt-get install libproj-dev proj-bin proj-data libgeos-dev
    sudo pip install cython

License = MIT
--------------

lala is an open-source software originally written at the `Edinburgh Genome Foundry <http://genomefoundry.org>`_ by `Zulko <https://github.com/Zulko>`_ and `released on Github <https://github.com/Edinburgh-Genome-Foundry/lala>`_ under the MIT licence (Copyright 2018 Edinburgh Genome Foundry).

Everyone is welcome to contribute!
