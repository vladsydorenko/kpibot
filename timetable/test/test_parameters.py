from django.test import TestCase

from timetable.parameters import Parameters


class ParametersTestCase(TestCase):
    def test_parse_group_valid(self):
        valid_groups = {
            'Кв-32': 'кв-32',
            'лн-51м': 'лн-51м',
            'лн-51с(махнв)': 'лн-51с(махнв)',
            'kv-32': 'кв-32',
            'KV32m': 'кв-32м',
            'тпс31м': 'тпс-31м',
            'tps42s(mahnv)': 'тпс-42с(махнв)'
        }

        for group, expected_result in valid_groups.items():
            parameters = Parameters('/setgroup', [group])
            self.assertTrue(parameters.is_valid())
            self.assertEqual(parameters.group_name, expected_result)

    def test_parse_group_invalid_parameter(self):
        parameters = Parameters('/setgroup', ['123'])
        self.assertFalse(parameters.is_valid())
        self.assertEqual(parameters.errors[0],
                         "Обязательный параметр не задан.")

    def test_setteacher_valid_name(self):
        teachers_name = "Петров Иван Иванович"
        parameters = Parameters('/setteacher', [teachers_name])
        self.assertTrue(parameters.is_valid())
        self.assertEqual(parameters.teachers_name, teachers_name)

    def test_setteacher_valid_id(self):
        teacher_id = "345"
        parameters = Parameters('/setteacher', [teacher_id])
        self.assertTrue(parameters.is_valid())
        self.assertEqual(parameters.teacher_id, int(teacher_id))

    def test_setteacher_invalid_parameters(self):
        parameters = Parameters('/setteacher', ['КВ-32'])
        self.assertFalse(parameters.is_valid())
        self.assertEqual(parameters.errors[0],
                         "Имя или id преподавателя не заданы.")

    def test_invalid_parameter(self):
        parameters = Parameters('/setteacher', 'sdf$xcd')
        self.assertFalse(parameters.is_valid())
        self.assertEqual(parameters.errors[0], "Неправильный параметр")
