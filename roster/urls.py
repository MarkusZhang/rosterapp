from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf.urls.static import static

from roster.settings import STATIC_URL,STATIC_ROOT

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^account/', include('account.urls')),
    #url(r'^notification/', include('notification.urls')),
    url(r'^schedule/', include('scheduleinfo.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
