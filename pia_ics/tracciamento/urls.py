from django.urls import path
from .views import ScanQRCodeView, ProcessQRCodeView

app_name = 'tracciamento'

urlpatterns = [
    path('scanqrcode/', ScanQRCodeView.as_view(), name='scanqrcode'),
    path('processqrcode/', ProcessQRCodeView.as_view(), name='processqrcode'),
]
