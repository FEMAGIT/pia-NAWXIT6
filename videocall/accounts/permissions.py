# Custom permissions

from rest_framework import permissions
from accounts.models import *
from .utils import Utils
import json

class IsAppRequest(permissions.BasePermission):
    """
    Global permission check requests from only registered app.
    """
    message = 'Invalid Application API_KEY'

    def has_permission(self, request, view):
        perm = False
        if hasattr(request, 'app'):
            perm = True
        return perm

class HasPermission(permissions.BasePermission):
    """
    Global permission check requests from only registered app.
    """
    message = 'Invalid Application API_KEY'

    def has_permission(self, request, view):
        perm = False
        if hasattr(request, 'app'):
            perm = True
        return perm