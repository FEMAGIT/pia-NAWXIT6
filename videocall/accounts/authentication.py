from .models import User, UserWhitToken
from channels.auth import AuthMiddlewareStack
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections



class UserAppPasswordAuthentication:
    def authenticate(self, request, username=None, password=None):
        if username and password :
            try:
                user = User.objects.get(username=username)
                if user.check_password(password):
                    return user
                else:
                    return None
            except User.DoesNotExist:
                return None
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class WebSocketTokenAuthMiddleware:
    """
    Token authorization middleware for Django Channels 2
    """

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        token_name, token_key = None, None
        headers = dict(scope['headers'])
        if b'authorization' in headers:
            token_name, token_key = headers[b'authorization'].decode().split()
        elif scope['query_string'].startswith(b'Token'):
            token_name, token_key = scope['query_string'].decode().split('=')
        elif scope['query_string'].startswith(b'token'):
            token_name, token_key = scope['query_string'].decode().split('=')
        if token_name and token_key:
            try:
                if token_name == 'Token' or token_name == 'token':
                    ##Utils.make_sure_mysql_usable()
                    close_old_connections()
                    userWhitToken = UserWhitToken.objects.filter(key=token_key).first()
                    if userWhitToken and userWhitToken.isTokenValid:
                        scope['userWhitToken'] = userWhitToken
                        if hasattr(userWhitToken, 'smartglass'):
                            scope['smartglass'] = userWhitToken.smartglass
                        elif hasattr(userWhitToken, 'videouser'):
                            scope['videouser'] = userWhitToken.videouser
            except UserWhitToken.DoesNotExist:
                print('UserWhitToken.DoesNotExist '+ token_key )
                pass
        return self.inner(scope)



TokenAuthMiddlewareStack = lambda inner: WebSocketTokenAuthMiddleware(AuthMiddlewareStack(inner))

