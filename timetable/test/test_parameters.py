from django.test import TestCase

from timetable.parameters import Parameters


class ParametersTestCase(TestCase):
    def test_parse_group_valid(self):
        valid_groups = {
            'кв-32': 'кв-32',
            'лн-51м': 'лн-51м',
            'лн-51с(махнв)': 'лн-51с(махнв)',
            'kv-32': 'кв-32',
            'kv32m': 'кв-32м',
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
        self.assertTrue("Код группы не задан." in parameters.errors)

    def test_setteacher_valid_name(self):
        teachers_name = "петров иван иванович"
        parameters = Parameters('/setteacher', teachers_name.split())
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

    def test_week_parameter_valid(self):
        parameters = Parameters('/tt', ['w1'])
        self.assertTrue(parameters.is_valid())
        self.assertEqual(parameters.week, 1)

        parameters = Parameters('/tt', ['w2'])
        self.assertTrue(parameters.is_valid())
        self.assertEqual(parameters.week, 2)

    def test_auto_week_parameter(self):
        parameters = Parameters('/tt', ['w'])
        self.assertTrue(parameters.is_valid())
        self.assertTrue(hasattr(parameters, 'week'))

    def test_week_parameter_invalid(self):
        parameters = Parameters('/tt', ['w5'])
        self.assertFalse(parameters.is_valid())
        self.assertEqual(parameters.errors[0], "Неправильный параметр")

    def test_print_teacher_param(self):
        parameters = Parameters('/tt', ['t'])
        self.assertTrue(parameters.is_valid())
        self.assertTrue(parameters.print_teacher)

    def test_day_number_param(self):
        parameters = Parameters('/tt', ['mon'])
        self.assertTrue(parameters.is_valid())
        self.assertEqual(parameters.day, 1)

        parameters = Parameters('/tt', ['fri'])
        self.assertTrue(parameters.is_valid())
        self.assertEqual(parameters.day, 5)

    def test_invalid_parameter(self):
        parameters = Parameters('/setteacher', 'sdf$xcd')
        self.assertFalse(parameters.is_valid())
        self.assertEqual(parameters.errors[0], "Неправильный параметр")
