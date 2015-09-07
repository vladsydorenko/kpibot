from django.conf.urls import patterns, include, url
from django.contrib import admin
from request_handler import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'kpi_rozklad_bot.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    #url(r'^lalka/$', views.lalka, name='lalka'),
    url(r'^$', views.index, name='index'),
)
