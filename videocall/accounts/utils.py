from django.conf import settings
from .models import User
import jwt
import string, random



# dummy class
class PostDataClass(object):
    pass


class Utils():
    @staticmethod
    def generate_key(length):
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def first_run():


        user = User(pk=1)
        user.first_name = settings.DEFAULT_ADMIN_FIRST_NAME
        user.last_name = settings.DEFAULT_ADMIN_LAST_NAME
        user.username = settings.DEFAULT_ADMIN_USERNAME
        user.email = settings.DEFAULT_ADMIN_EMAIL
        user.set_password(settings.DEFAULT_ADMIN_PASSWORD)
        user.is_superuser = True
        user.is_staff = True
        user.save()



    @staticmethod
    def encode_data(data,key):
        return jwt.encode(data, key, algorithm='HS256')

    @staticmethod
    def decode_data(data,key):
        try:
            return jwt.decode(data, key, algorithms=['HS256'])
        except:
            return None

    @staticmethod
    def make_sure_mysql_usable():
        from django.db import connection, connections
        # mysql is lazily connected to in django.
        # connection.connection is None means
        # you have not connected to mysql before
        if connection.connection and not connection.is_usable():
            # destroy the default mysql connection
            # after this line, when you use ORM methods
            # django will reconnect to the default mysql
            del connections._connections.default

    @staticmethod
    def get_token(request, token=None):
        if token is None and hasattr(request,'data'):
            token = request.data.get('token', None)
        if token is None:
            token = request.GET.get('token', None)
        if token is None:
            token = request.POST.get('token', None)
        if token is None:
            if 'HTTP_AUTHORIZATION' in request.META:
                token_name, token = request.META['HTTP_AUTHORIZATION'].split()
                if token_name != 'Token' and token_name != 'token':
                    token = None
        return token