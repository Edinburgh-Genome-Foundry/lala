import os
import matplotlib
matplotlib.use("Agg")
from lala import WebLogs

access_log_path = os.path.join('tests', 'data', "test_logs.txt")
template_path = os.path.join('tests', 'data', "template.pug")

def test_basics(tmpdir):

    # LOAD ALL RECORDS TO ANALYSE AND AVAILABLE PRIMERS
    weblogs, errored_lines = WebLogs.from_nginx_weblogs(access_log_path)

    # PLOT COUNTRIES PIE CHART
    ax, country_values = weblogs.plot_piechart('country_name')

    # PLOT COUNTRIES MAP
    weblogs.plot_geo_positions()

    # PLOT UK CONNECTIONS TIMELINE
    ag_weblogs = weblogs[weblogs.country_name == 'Argentina']
    ax = ag_weblogs.plot_timeline(bins_per_day=2)

    # COMPUTE THE VISITORS/VISITS
    visitors = weblogs.visitors_and_visits()
    assert len(visitors) == 88

    # visitors_locations = weblogs.visitors_locations()
    most_frequent_visitors = weblogs.most_frequent_visitors(n_visitors=5)
    assert len(most_frequent_visitors) == 5
    weblogs.plot_most_frequent_visitors()

    sub_weblogs = weblogs[-50:]
    sub_weblogs.identify_ips_domains()
    filtered_weblogs = sub_weblogs.filter_by_text_search(
        terms=['googlebot', 'spider.yandex', 'baidu', 'msnbot'],
        not_in='domain'
    )
    assert len(filtered_weblogs) == 50

def test_template(tmpdir):
    # LOAD ALL RECORDS TO ANALYSE AND AVAILABLE PRIMERS
    weblogs, errored_lines = WebLogs.from_nginx_weblogs(access_log_path)
    sub_weblogs = weblogs[-50:]
    sub_weblogs.identify_ips_domains()
    target_path = os.path.join(str(tmpdir), "output.pdf")
    # print(sub_weblogs.request)
    sub_weblogs.write_report(template_path=template_path, target=target_path)
