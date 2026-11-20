from django.conf.urls import url, include
from django.urls import path
from django.conf import settings

from accounts.views import home

urlpatterns = [
    ##url(r'^auth/',include('accounts.urls')),
    url(r'^video/api/', include('accounts.urls')),
    path('', home, name='home'),
#    url(r'', include('ticketing.urls')),
]
