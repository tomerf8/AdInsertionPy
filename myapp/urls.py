from django.conf.urls import patterns, url

from myapp import views

urlpatterns = patterns('',
                       
    url(r'^$', views.index),
    
    url(r'^web/$', views.website),
    url(r'^web/(?P<page>.*)$', views.website),
     
    url(r'^site_media/(?P<requested_hash>.*)$', views.service_algo, name='service_algo'),
    
    url(r'^init/$', views.initSetup, name='index'),
    
    url(r'^direct/(?P<requested_file>.*)$', views.direct_serv, name='direct_serv'),
      
    url(r'^download_mpd/$', views.download_mpd, name='download_mpd'),
    
)
