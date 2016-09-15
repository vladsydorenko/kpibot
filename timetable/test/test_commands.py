from unittest.mock import patch
from timetable.models import Chat
from kpibot.utils.test.cases import TelegramBotTestCase

POSSIBLE_COMMANDS = [
    "/authors", "/changelang", "/help", "/next", "/now", "/setgroup",
    "/setteacher", "/start", "/time", "/today", "/tomorrow",
    "/tt", "/week", "/where", "/who", "/teacher"
]


class KPIBotSimpleCommandsTestCase(TelegramBotTestCase):
    @patch('kpibot.utils.bot.sendMessage')
    def test_changelang_ru_ua(self, sm_mock):
        self.chat.language = "ru"
        self.chat.save()
        self.command = "/changelang"

        self.client.post("/", self.payload, content_type="application/json")

        self.assertEqual(Chat.objects.first().language, "uk")

    @patch('kpibot.utils.bot.sendMessage')
    def test_changelang_ua_ru(self, sm_mock):
        self.chat.language = "uk"
        self.chat.save()
        self.command = "/changelang"

        self.client.post("/", self.payload, content_type="application/json")

        self.assertEqual(Chat.objects.first().language, "ru")

    def test_week(self):
        pass

    def test_who(self):
        pass

    def test_teacher(self):
        pass

    def test_next(self):
        pass

    def test_now(self):
        pass

    def test_setteacher(self):
        pass

    def test_setgroup(self):
        pass

    def test_today(self):
        pass

    def test_tomorrow(self):
        pass


class TTTestCase(TelegramBotTestCase):
    def test_tt_full(self):
        pass

    def test_tt_week(self):
        pass
