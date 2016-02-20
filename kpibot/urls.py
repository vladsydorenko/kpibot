from django.conf.urls import patterns, include, url
from django.contrib import admin
from request_handler import views

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', views.index, name='index'),
    url(r'^test/', views.test),
)
