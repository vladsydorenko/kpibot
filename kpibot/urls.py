from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from timetable import views

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', views.CommandDispatcherView.as_view(), name='index'),
]

if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += [
        url(r'^rosetta/', include('rosetta.urls')),
    ]
