from celery.task.schedules import crontab
from celery.decorators import periodic_task
from request_handler.models import Chat
from request_handler.timetable import TeacherTimetable, GroupTimetable

@periodic_task(run_every=(crontab(hour='8', minute='20')))
@periodic_task(run_every=(crontab(hour='10', minute='10')))
@periodic_task(run_every=(crontab(hour='12', minute='5')))
@periodic_task(run_every=(crontab(hour='14', minute='0')))
@periodic_task(run_every=(crontab(hour='15', minute='55')))
@periodic_task(run_every=(crontab(minute='*')))
def lesson_reminder():
    all_chats = Chat.objects.all()
    for chat in all_chats:
        if chat.remind:
            if chat.group_id == 0:
                tt = TeacherTimetable(chat.chat_id, '/now')
            else:
                tt = GroupTimetable(chat.chat_id, '/now')

            tt.now()
            tt.where()