import factory
from timetable.models import Chat


class ChatFactory(factory.Factory):
    class Meta:
        model = Chat

    id = factory.Sequence(lambda n: n)
