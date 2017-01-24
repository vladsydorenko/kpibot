import requests

from django.conf import settings
from django.utils.translation import ugettext as _

from timetable.exceptions import MultipleResults, SendError


class APIEntity:
    def __init__(self, name=None, resource_id=None):
        if name and resource_id:
            self.name = name
            self.resource_id = resource_id
        elif name:
            self.name = name
            self._get_entity_id(name)
        elif resource_id:
            self.resource_id = resource_id
            self.name = self._get_entity_name()
        else:
            raise Exception("Entity name or id was not passed")

    def _get_entity_id(self, name):
        """Get information about entity from API"""
        params = {
            'search': name,
        }
        response = requests.get(settings.TIMETABLE_URL + self.endpoint, params)
        data = response.json()
        if data['count'] == 0:
            raise SendError(_(self.error_message_404))
        if data['count'] > 1:
            # If API returned more than 1 entity, we create list of all 
            # returned entities and let user to choose what entity he want
            # to use.
            entities = [entity['name'] for entity in data['results']]
            raise MultipleResults(entities)
        else:
            self.resource_id = data['results'][0]['id']
            self.name = data['results'][0]['name']

    def _get_entity_name(self):
        response = requests.get(settings.TIMETABLE_URL + self.endpoint +
                                str(self.resource_id))
        if response.status_code == 404:
            raise Exception("Wrong entity id - {}".format(self.resource_id))

        return response.json()['name']


class Group(APIEntity):
    def __init__(self, *args, **kwargs):
        self.endpoint = "/groups/"
        self.error_message_404 = _("Подобной группы нет в базе. " +
                                   "Проверьте правильность ввода")
        super().__init__(*args, **kwargs)


class Teacher(APIEntity):
    def __init__(self, *args, **kwargs):
        self.endpoint = "/teachers/"
        self.error_message_404 = _("""Преподавателя, соответствующего подобному
 запросу нет в базе. Проверьте правильность ввода""")
        super().__init__(*args, **kwargs)
