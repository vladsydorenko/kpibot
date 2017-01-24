import responses

from django.test import TestCase
from django.conf import settings

from timetable.exceptions import SendError, MultipleResults
from timetable.entities import Group, Teacher
from timetable.test.fixtures import group_fixture, teacher_fixture,\
    group_fixture_search, teacher_fixture_search, empty_response


class EntitiesTestCase(TestCase):
    @responses.activate
    def test_get_group_by_name_success(self):
        responses.add(responses.GET, settings.TIMETABLE_URL + '/groups/',
                      json=group_fixture_search, status=200)

        group = Group(name='кв-32')
        self.assertEqual(group.resource_id,
                         group_fixture_search['results'][0]['id'])

    @responses.activate
    def test_get_group_by_id_success(self):
        responses.add(responses.GET, settings.TIMETABLE_URL + '/groups/575',
                      json=group_fixture, status=200)

        group = Group(resource_id=575)
        self.assertEqual(group.name, "кв-32")

    @responses.activate
    def test_get_teacher_by_name_success(self):
        responses.add(responses.GET, settings.TIMETABLE_URL + '/teachers/',
                      json=teacher_fixture_search, status=200)

        teacher = Teacher(name='пересада')
        self.assertEqual(teacher.resource_id,
                         teacher_fixture_search['results'][0]['id'])

    @responses.activate
    def test_get_teacher_by_id_success(self):
        responses.add(responses.GET, settings.TIMETABLE_URL + '/teachers/575',
                      json=teacher_fixture, status=200)

        teacher = Teacher(resource_id=575)
        self.assertEqual(teacher.name, "Пересада Сергій Михайлович")

    @responses.activate
    def test_get_group_by_name_404(self):
        responses.add(responses.GET, settings.TIMETABLE_URL + '/groups/',
                      json=empty_response, status=200)

        with self.assertRaises(SendError):
            Group(name="test")

    @responses.activate
    def test_get_group_by_id_404(self):
        responses.add(responses.GET, settings.TIMETABLE_URL + '/groups/575',
                      status=404)

        with self.assertRaises(Exception):
            Group(resource_id=575)

    @responses.activate
    def test_get_group_by_name_multiple_results(self):
        group_fixture_search_mul = group_fixture_search.copy()
        group_fixture_search_mul['count'] = 5
        responses.add(responses.GET, settings.TIMETABLE_URL + '/groups/',
                      json=group_fixture_search_mul, status=200)

        with self.assertRaises(MultipleResults):
            Group(name="kv-32")
