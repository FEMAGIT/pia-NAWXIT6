
from django.shortcuts import render, redirect
from .models import  User,VideoUser, UserWhitToken;
from django.core.exceptions import PermissionDenied
from .utils import Utils


def superuser_only(function):

    def _inner(request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('home')
        return function(request, *args, **kwargs)

    return _inner


def token_required(function):
    def wrap(request,token=None, *args, **kwargs):
        token = Utils.get_token(request, token)
        if token is None:
            raise PermissionDenied
        else:
            videouser=VideoUser.getVideoUserByToken(token=token)
        if videouser:
            request.smartglass = None
            request.videouser = videouser
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap

def video_token_required(function):
    def wrap(request,token=None, *args, **kwargs):
        token = Utils.get_token(request, token)
        if token is None:
            raise PermissionDenied
        else:
            userWhitToken = UserWhitToken.objects.filter(key=token).first()
            request.smartglass = None
            request.videouser = None
            if userWhitToken and userWhitToken.isTokenValid:
                request.userWhitToken =userWhitToken
                if hasattr(userWhitToken, 'smartglass'):
                    request.smartglass = userWhitToken.smartglass
                elif hasattr(userWhitToken, 'videouser'):
                    request.videouser = userWhitToken.videouser
                request.token = userWhitToken.key
                return function(request, *args, **kwargs)
            else:
                raise PermissionDenied


    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap