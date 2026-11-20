from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import *
from django.db.models import Q
from rest_framework.authtoken.models import Token


class customConsumer(AsyncWebsocketConsumer):


    async def generateSelfDescriptor(self):
        if self.smartglass:
            des = {
                "id": self.smartglass.id,
                "name": self.smartglass.name,
                "online": self.userWhitToken.is_online,
                "busy": self.userWhitToken.is_busy,
                "calling": self.userWhitToken.is_calling
            }
        else:
            des = {
                "id": self.videouser.id,
                "name": self.videouser.name,
                "online": self.videouser.is_online,
                "busy": self.videouser.is_busy,
                "calling": self.videouser.is_calling
            }
        return des

    async def generateRemoteDescriptor(self,user_to_call):
        des = {
            "id": user_to_call.id,
            "name": user_to_call.name,
            "online": user_to_call.is_online,
            "busy": user_to_call.is_busy,
            "calling": user_to_call.is_calling
        }
        return des

    async def generateRemoteDescriptorBrodcastUser(self):
        des = {
            "id": -1,
        }
        return des



    async def auth(self):
        token_name, token_key = None, None
        headers = dict(self.scope['headers'])
        if b'authorization' in headers:
            token_name, token_key = headers[b'authorization'].decode().split()
        elif self.scope['query_string'].startswith(b'Token'):
            token_name, token_key = self.scope['query_string'].decode().split('=')
        if token_name and token_key:
            if token_name == 'Token':
                user = await self.get_userBytoken(token_key=token_key)
                if user:
                    self.scope['user'] = user


    @database_sync_to_async
    def get_user(self, id=None):
        return UserWhitToken.objects.filter(id=id).first()

    @database_sync_to_async
    def get_smartglasses(self):
        return SmartGlass.all_valid()

    @database_sync_to_async
    def start_UserWhitToken(self):
        self.userWhitToken.is_online = True
        self.userWhitToken.is_busy = False
        self.userWhitToken.is_calling = False
        self.userWhitToken.save()


    @database_sync_to_async
    def reset_UserWhitToken(self):
        self.userWhitToken.is_online = False
        self.userWhitToken.is_busy = False
        self.userWhitToken.is_calling = False
        self.userWhitToken.save()


    @database_sync_to_async
    def set_UserWhitToken(self, online=None, busy=None, calling=None, userWhitToken=None ):
        if not userWhitToken:
            userWhitToken=self.userWhitToken
            self.userWhitToken = self.updateUser(busy, calling, online, userWhitToken)
            return  self.userWhitToken
        else:
            return self.updateUser(busy, calling, online, userWhitToken)

    def updateUser(self, busy, calling, online, userWhitToken):
        if online != None:
            userWhitToken.is_online = online
        if busy != None:
            userWhitToken.is_busy = busy
        if calling != None:
            userWhitToken.is_calling = calling
        userWhitToken.save()
        return userWhitToken

    @database_sync_to_async
    def set_online(self, online =False):
        self.userWhitToken.is_online = online
        self.userWhitToken.save()

    @database_sync_to_async
    def set_busy(self, busy=False):
        self.userWhitToken.is_busy = busy
        self.userWhitToken.save()


    @database_sync_to_async
    def set_calling(self, calling=False):
        self.userWhitToken.is_calling = calling
        self.userWhitToken.save()


    @database_sync_to_async
    def create_group(self, room_group_name='', single_user=True):
        return Group.objects.get_or_create(name=room_group_name, singleUser=single_user)


    @database_sync_to_async
    def exist_group(self, room_group_name=''):
        return Group.objects.filter(name=room_group_name).first()

    @database_sync_to_async
    def remove_group(self, room_group_name=''):
        return Group.objects.filter(name=room_group_name).delete()

    @database_sync_to_async
    def get_groups(self):
        return Group.objects.values_list('name', flat=True)

    @database_sync_to_async
    def is_online(self, contact=None):
        if contact:
            userWhitToken = UserWhitToken.objects.filter(id=str(contact.id)).first()
        else:
            userWhitToken = UserWhitToken.objects.filter(id=str(self.userWhitToken.id)).first()
        if userWhitToken:
            online = userWhitToken.is_online
            busy = False
            calling = False
            if online:
                busy = userWhitToken.is_busy
                calling = userWhitToken.is_calling
            return online, busy, calling
        else:
            False,False,False


