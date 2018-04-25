import os
from lala import WebLogs

example_logs_path = os.path.join('data', 'example_logs.txt')
template_path = os.path.join('data', 'example_template.pug')

weblogs, errored_lines = WebLogs.from_nginx_weblogs(example_logs_path)

print ("Now identifying IP addresses")
weblogs.identify_ips_domains()

print ("Now writing the report")
weblogs.write_report(template_path=template_path, target="report_example.pdf")
