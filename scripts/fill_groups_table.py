import sys, os
sys.path.append('/home/kpibot/kpibot/kpibot')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from django.conf import settings
from request_handler.models import Group
import requests

API_URL = "http://api.rozklad.org.ua/v2/groups/?filter={\"offset\":%s}"

raw_data = requests.get(API_URL % "-1")
total_count = int(raw_data.json()['meta']['total_count'])

for i in range(int(total_count / 100) + 1):
    raw_data = requests.get(API_URL % str(i*100))
    data = raw_data.json()['data']
    for group in data:
        obj = Group(group_id = group['group_id'], group_name = group['group_full_name'])
        obj.save()

