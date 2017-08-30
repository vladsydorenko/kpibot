from django.conf import settings
import requests


class KPIHubAPIClient:
    @classmethod
    def _find_entity(cls, endpoint, name):
        params = {
            'search': name
        }
        response = requests.get(settings.TIMETABLE_URL + endpoint, params)
        data = response.json()

        return data['results']

    @classmethod
    def find_group(cls, name):
        return cls._find_entity('/groups/', name)

    @classmethod
    def find_teacher(cls, name):
        return cls._find_entity('/teachers/', name)

    @classmethod
    def get_timetable(cls, query_parameters):
        response = requests.get(settings.TIMETABLE_URL + '/lessons', query_parameters)
        return response.json()['results']

    @classmethod
    def get_teacher(cls, teachers_id):
        response = requests.get(settings.TIMETABLE_URL + '/teachers/{}'.format(teachers_id))
        return response.json()

    @classmethod
    def get_room(cls, room_id):
        response = requests.get(settings.TIMETABLE_URL + '/rooms/{}'.format(room_id))
        return response.json()

    @classmethod
    def get_building(cls, building_id):
        response = requests.get(settings.TIMETABLE_URL + '/buildings/{}'.format(building_id))
        return response.json()
