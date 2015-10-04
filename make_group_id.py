import sys, os
sys.path.append('/home/kpibot/kpibot/kpibot')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from django.conf import settings
from request_handler.models import Chat
import requests

chats = Chat.objects.all()

for chat in chats:
    if chat.group != "":
        raw_data = requests.get("http://api.rozklad.org.ua/v2/groups/%s" % chat.group)
        data = raw_data.json()
        if data['statusCode'] == 200:
            chat.group_id = data['data']['group_id']
            print (chat.group + " - " + str(chat.group_id) + " OK")
            chat.save()
        else:
            print (chat.group + " FAIL")