from unittest.mock import patch

from timetable.timetable import KPIHubTimetable
from timetable.test.fixtures import one_lesson_fixture, timetable_fixture,\
    api_response_timetable_fixture, api_response_one_lesson_fixture
from kpibot.test.cases import TelegramBotTestCase
from kpibot.test.factories import ParametersFactory, GroupFactory


class TimetableTestCase(TelegramBotTestCase):
    @patch('requests.models.Response.json',
           return_value=api_response_one_lesson_fixture)
    @patch('kpibot.settings.BOT.sendMessage')
    def test_run_one_lesson(self, sm_mock, gt_mock):
        parameters = ParametersFactory()
        parameters.week = one_lesson_fixture['week'],
        parameters.day = one_lesson_fixture['day'],
        parameters.number = one_lesson_fixture['number']
        group = GroupFactory()

        timetable = KPIHubTimetable(self.chat, group, parameters)
        timetable.execute('/now')

        self.assertTrue(sm_mock.called)
