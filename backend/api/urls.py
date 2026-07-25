from django.urls import path, re_path
from . import views

urlpatterns = [
    # Public endpoints (support with or without trailing slash)
    re_path(r'^languages/?$', views.get_languages, name='get_languages'),
    re_path(r'^site-settings/?$', views.get_site_settings, name='get_site_settings'),
    re_path(r'^videos/?$', views.get_videos, name='get_videos'),
    re_path(r'^videos/play/(?P<video_id>\d+)/?$', views.play_video, name='play_video'),
    re_path(r'^view-events/?$', views.log_view_event, name='log_view_event'),

    # Admin Auth & Settings endpoints
    re_path(r'^admin/login/?$', views.admin_login, name='admin_login'),
    re_path(r'^admin/me/?$', views.admin_me, name='admin_me'),
    re_path(r'^admin/site-settings/?$', views.update_site_settings, name='update_site_settings'),

    # Admin Video Management endpoints
    re_path(r'^admin/videos/?$', views.admin_videos, name='admin_videos'),
    re_path(r'^admin/videos/(?P<video_id>\d+)/?$', views.admin_edit_video, name='admin_edit_video'),
    re_path(r'^admin/videos/(?P<video_id>\d+)/toggle/?$', views.admin_toggle_video, name='admin_toggle_video'),
    re_path(r'^admin/languages/?$', views.admin_add_language, name='admin_add_language'),

    # Admin Analytics endpoints
    re_path(r'^admin/analytics/summary/?$', views.admin_analytics_summary, name='admin_analytics_summary'),
    re_path(r'^admin/analytics/export/?$', views.admin_analytics_export, name='admin_analytics_export'),
]
