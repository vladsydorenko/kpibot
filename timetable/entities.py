import requests

from django.conf import settings
from django.utils.translation import ugettext as _

from timetable.exceptions import MultipleResults, SendError


class APIEntity:
    def __init__(self, name=None, resource_id=None):
        if name and not resource_id:
            resource_id = self._get_entity_id(name)
        elif not name and resource_id:
            name = self._get_entity_name(resource_id)
        elif not any(name, resource_id):
            raise Exception("Entity name or id was not passed")

        self.name = name
        self.resource_id = resource_id

    @classmethod
    def _get_entity_id(cls, name):
        """Get information about entity from API"""
        params = {
            'search': name,
        }
        response = requests.get(settings.TIMETABLE_URL + cls.endpoint, params)
        data = response.json()

        if data['count'] == 0:
            raise SendError(_(cls.error_message_404))
        elif data['count'] == 1:
            return data['results'][0]['id']
        else:
            # If API returned more than 1 entity, we create list of all
            # returned entities and let user to choose what entity he want
            # to use.
            entities = [entity['name'] for entity in data['results']]
            raise MultipleResults(entities)

    @classmethod
    def _get_entity_name(cls, resource_id):
        response = requests.get(settings.TIMETABLE_URL + cls.endpoint +
                                str(resource_id))
        if response.status_code == 404:
            raise Exception("Wrong entity id - {}".format(resource_id))

        return response.json()['name']


class Group(APIEntity):
    endpoint = "/groups/"
    error_message_404 = _("Подобной группы нет в базе. Проверьте правильность ввода")


class Teacher(APIEntity):
    endpoint = "/teachers/"
    error_message_404 = _("Преподавателя, соответствующего подобному запросу нет в базе. Проверьте правильность ввода")
