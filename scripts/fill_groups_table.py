import sys, os
sys.path.append('/home/kpibot/kpibot-test/kpibot')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import django
django.setup()
from request_handler.models import Group
import requests

API_URL = "http://api.rozklad.hub.kpi.ua/groups/?format=json&limit=100&offset=%s"

raw_data = requests.get(API_URL % "-1")
total_count = int(raw_data.json()['count'])
Group.objects.all().delete()

for i in range(int(total_count / 100) + 1):
    raw_data = requests.get(API_URL % str(i*100))
    data = raw_data.json()['results']
    for group in data:
        Group(group_id = group['id'], group_name = group['name']).save()

