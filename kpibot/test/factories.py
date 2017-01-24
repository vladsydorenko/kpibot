import factory
from timetable.models import Chat
from timetable.parameters import Parameters
from timetable.entities import Teacher, Group


class ChatFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Chat

    id = factory.Sequence(lambda n: n)


class ParametersFactory(factory.Factory):
    class Meta:
        model = Parameters
    command = "/test"
    parameters = []


class GroupFactory(factory.Factory):
    class Meta:
        model = Group
    name = "КВ-32"
    resource_id = 553


class TeacherFactory(factory.Factory):
    class Meta:
        model = Teacher