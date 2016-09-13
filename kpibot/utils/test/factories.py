import factory
from timetable.models import Chat


class ChatFactory(factory.Factory):
    class Meta:
        model = Chat

    category = "group"
    id = factory.Sequence(lambda n: n)
