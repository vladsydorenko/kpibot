from django.contrib import admin

# Register your models here.
from .models import Chat, Group
admin.site.register(Chat)
admin.site.register(Group)