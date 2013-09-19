from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.contrib import admin
admin.autodiscover()


handler500 = 'mapentity.views.handler500'


urlpatterns = patterns('',

    url(r'^$',        'geotrek.core.views.home', name='home'),
    url(r'^login/$',  'django.contrib.auth.views.login', name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': settings.ROOT_URL + '/'}, name='logout',),

    url(r'', include('geotrek.common.urls', namespace='common', app_name='common')),
    url(r'', include('geotrek.core.urls', namespace='core', app_name='core')),
    url(r'', include('geotrek.land.urls', namespace='land', app_name='land')),
    url(r'', include('geotrek.infrastructure.urls', namespace='infrastructure', app_name='infrastructure')),
    url(r'', include('geotrek.maintenance.urls', namespace='maintenance', app_name='maintenance')),
    url(r'', include('geotrek.trekking.urls', namespace='trekking', app_name='trekking')),

    url(r'', include('mapentity.urls', namespace='mapentity', app_name='mapentity')),
    url(r'^paperclip/', include('paperclip.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()
