import telegram
from django.conf import settings

bot = telegram.Bot(token=settings.BOT_TOKEN)
