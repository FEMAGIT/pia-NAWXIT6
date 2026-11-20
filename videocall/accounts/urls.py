from django.urls import path
from accounts.views import *

from .models import Group, UserWhitToken


urlpatterns = [
    # path('', home, name='home'),
    # path('home/', home, name='home'),
    #
    # path('login/', login_user, name='login'),
    # path('logout/', logout_user, name='logout'),
    #
    # path('new_user_registration/', new_user, name='new_user_registration'),
    #
    #
    # path('user_list/', user_list, name='user_list'),
    # path('video_user_list/', video_user_list, name='video_user_list'),
    #
    #
    # path('delete_user_ajax/', delete_user_ajax, name='delete_user_ajax'),
    #
    # path('users/<int:pk>/', user_modify, name='user'),
    #
    # path('change_password/', change_password, name='change_password'),
    # path('reset_password/', reset_password, name='reset_password'),
    # path('reset_password/<str:uidb64>/<str:token>/', password_reset_confirm, name='password_reset_confirm'),
    #



    path('video_chat/', video_chat, name='video_chat'),
    path('video_chat/<str:token>/', video_chat, name='video_chat'),

    path('video_chat_ext/', video_chat_ext, name='video_chat_ext'),
    path('video_chat_ext/<str:token>/', video_chat_ext, name='video_chat_ext'),


    path('session/', session, name='session'),

    path('login/', api_login, name='api_login'),

    path('smartglass_login/', api_smartglass_login, name='api_smartglass_login'),

    path('user_info/', api_user_info, name='api_user_info'),

    path('generate_user_video_token/', generate_user_video_token, name='generate_user_video_token'),

    path('generate_smartglass_video_token/', generate_smartglass_video_token, name='generate_smartglass_video_token'),

    path('check_token/', check_token, name='check_token'),

    path('upload_file/', upload_file, name='upload_file'),

]
try:
    UserWhitToken.objects.all().update(is_online=False)
    Group.objects.all().delete()
except:
    pass
