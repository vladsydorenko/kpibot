days = {
    1: ["mon", "pn"],
    2: ["tue", "vt"],
    3: ["wed", "sr"],
    4: ["thu", "cht"],
    5: ["fri", "pt"],
    6: ["sat", "sb"],
    7: ["sun", "vs"]
}

# Set all possible commands and max. arguments quantity
commands = {
    "/authors": 0,
    "/changelang": 1,
    "/help": 0,
    "/next": 2,
    "/now": 2,
    "/remind": 0,
    "/setgroup": 1,
    "/setteacher": 3,
    "/start": 0,
    "/time": 0,
    "/today": 2,
    "/tomorrow": 2,
    "/tt": 5,
    "/week": 0,
    "/where": 1,
    "/who": 1,
    "/teacher": 3,
}

no_timetable_commands = [
    "/authors",
    "/changelang",
    "/help",
    "/remind",
    "/start",
    "/time",
    "/week"
]

types = {
    0: 'Лек',
    1: 'Прак',
    2: 'Лаб'
}

time = """
1. 08:30 - 10:05\n
2. 10:25 - 12:00\n
3. 12:20 - 13:55\n
4. 14:15 - 15:50\n
5. 16:10 - 17:45
"""
