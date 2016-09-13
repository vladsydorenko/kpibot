from unittest.mock import patch
from django.utils.translation import activate, get_language
from kpibot.utils.test.cases import TelegramBotTestCase


class LocalizationTestCase(TelegramBotTestCase):
    @patch('kpibot.utils.bot.sendMessage')
    def test_russian_locale(self, sm_mock):
        self.chat.language = "ru"
        self.chat.save()
        self.command = "/week"
        activate("en")

        self.client.post("/", self.payload, content_type="application/json")
        current_language = get_language()
        self.assertEqual(current_language, "ru")

    @patch('kpibot.utils.bot.sendMessage')
    def test_ukrainian_locale(self, sm_mock):
        self.chat.language = "uk"
        self.chat.save()
        self.command = "/week"
        activate("en")

        self.client.post("/", self.payload, content_type="application/json")
        current_language = get_language()
        self.assertEqual(current_language, "uk")
