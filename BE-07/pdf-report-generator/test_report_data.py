import json
from report_data import get_report_data

data = get_report_data()
print(json.dumps(data, indent = 2))