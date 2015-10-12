from huey.djhuey import crontab, periodic_task
from request_handler.models import Chat
from request_handler.timetable import TeacherTimetable, GroupTimetable

@periodic_task(crontab(hour='5', minute='20'))
@periodic_task(crontab(hour='7', minute='10'))
@periodic_task(crontab(hour='9', minute='5'))
@periodic_task(crontab(hour='11', minute='0'))
@periodic_task(crontab(hour='12', minute='55'))
def lesson_reminder():
    all_chats = Chat.objects.all()
    for chat in all_chats:
        if chat.remind:
            if chat.group_id == 0:
                tt = TeacherTimetable(chat.chat_id, '/now')
            else:
                tt = GroupTimetable(chat.chat_id, '/now')

            if tt.now_has_lesson():
                tt.now()
                tt.where()