import requests
from abc import ABCMeta

from django.conf import settings
from django.utils.translation import ugettext as _

from kpibot.utils.exceptions import MultipleResults, SendError


class APIEntity(metaclass=ABCMeta):
    def __init__(self, name=None, _id=None):
        self.endpoint = "/"
        self.error_message_404 = ""

        if name:
            self.name = name
            self.id = self._get_entity_id()
        elif _id:
            self.id = _id
            self.name = self._get_entity_name()
        else:
            raise Exception("Entity name or id was not passed")

    def _get_entity_id(self):
        """Get information about entity from API"""
        params = {
            'search': self.name,
        }
        response = requests.get(settings.TIMETABLE_URL + self.endpoint, params)
        data = response.json()
        if data['count'] == 0:
            raise SendError(_(self.error_message_404))
        if data['count'] > 1:
            # If API returned more than 1 entity, that starts with passed
            # entity, we creates list of all returned entities and let user to 
            # choose what entity he want to use.
            entities = [entity['name'] for entity in data['results']]
            raise MultipleResults(entities)
        else:
            return data['results'][0]['id']

    def _get_entity_name(self):
        response = requests.get(settings.TIMETABLE_URL + self.endpoint +\
            str(self._id))


class Group(APIEntity):
    def __init__(self, *args, **kwargs):
        self.endpoint = "/groups/"
        self.error_message_404 = _("Подобной группы нет в базе. " +
                                   "Проверьте правильность ввода")
        super().__init__(*args, **kwargs)


class Teacher(APIEntity):
    def __init__(self, *args, **kwargs):
        self.endpoint = "/teachers/"
        self.error_message_404 = _("Преподавателя, соответствующего подобному " +
                                   "запросу нет в базе. " +
                                   "Проверьте правильность ввода")
        super().__init__(*args, **kwargs)
