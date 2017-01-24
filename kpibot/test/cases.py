import json

from django.test import TestCase, Client

from kpibot.test.factories import ChatFactory


class TelegramBotTestCase(TestCase):
    """Basic test case for telegram chat bots."""

    def setUp(self):
        self.client = Client()
        self.chat = ChatFactory(language="ru")
        self.command = "/test"

    @property
    def payload(self):
        return json.dumps({
            'message': {
                'chat': {
                    'id': self.chat.id,
                },
                'from': {
                    'id': "12345",
                },
                'text': self.command,
            }
        })