from .consumers_class_occ import customConsumer
import json
from channels import exceptions

VIDEOUSER= 'videouser'
SMARTGLASS = 'smartglass'
SYSTEM = 'system'
TYPE = 'type'
CONTACTS = 'contacts'
CALL = 'contact'
CONTACT_REFRESH = 'contact_refresh'
CLOSE_CALL = 'close_call'
ACCEPT_CALL = 'accept_call'
REFUSE_CALL = 'refuse_call'
STATUS = 'status'
CALLED ='called'
ACCEPTED_CALL = 'accepted_call'
USER_GONE_OFFLINE = 'user_offline'

# Connessione di sistema piu' recente per ciascun utente (userWhitToken.id -> channel_name).
# Quando un utente si riconnette, la connessione vecchia viene chiusa: senza questo
# controllo la sua disconnect() rimetteva online=False sopra lo stato della nuova.
# Vale perche' tutti i WebSocket sono serviti da un solo processo daphne (videocal):
# con piu' processi servirebbe uno stato condiviso (es. Redis).
_CONNESSIONE_ATTIVA = {}


class systemConsumer(customConsumer):

    async def connect(self):
        if 'userWhitToken' in self.scope :
            self.userWhitToken = self.scope['userWhitToken']
            _CONNESSIONE_ATTIVA[self.userWhitToken.id] = self.channel_name
            self.smartglass = None
            self.videouser = None
            self.subGroupName = 'None'
            if 'smartglass'in self.scope:
                self.smartglass = self.scope['smartglass']
                self.subGroupName = SMARTGLASS
                self.originGroupName = self.subGroupName + '_' + str(self.smartglass.creator.external_id)
                self.creatorGroupName = VIDEOUSER + '_' + str(self.smartglass.creator.external_id)
            elif 'videouser' in self.scope:
                self.videouser = self.scope['videouser']
                self.subGroupName= VIDEOUSER
                self.originGroupName=self.subGroupName+'_'+ str(self.videouser.external_id)
                self.createdGroupName = SMARTGLASS + '_' + str(self.videouser.external_id)
            self.room_group_name = str(self.userWhitToken.id)
            await self.disconnect_group(self.room_group_name)
            # Join System room group
            await self.channel_layer.group_add(
                SYSTEM,
                self.channel_name
            )

            await self.channel_layer.group_add(
                self.subGroupName,
                self.channel_name
            )
            await self.channel_layer.group_add(
                self.originGroupName,
                self.channel_name
            )
            # Join personal room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()
            await self.create_group(self.room_group_name)
            await self.start_UserWhitToken()
            if self.smartglass:
                await self.sendSmartGlassRefresh()
            await self.srtatusQuery()
        else:
            exceptions.DenyConnection


    async def sendSmartGlassRefresh(self):

        msg =await self.generateSelfDescriptor()
        await self.sendSmartGlassRefreshMsg(msg)

    async def sendSmartGlassRefreshMsg(self, msg):
        data = {
            TYPE: CONTACT_REFRESH,
            'msg': msg,
        }
        await self.channel_layer.group_send(
            VIDEOUSER,
            {
                'type': 'chat_message',
                'message': data
            }
        )

    async def sendUserGoneOffline(self):
        msg = await self.generateSelfDescriptor()
        data = {
            TYPE: USER_GONE_OFFLINE,
            'msg': msg,
        }
        await self.channel_layer.group_send(
            SMARTGLASS,
            {
                'type': 'chat_message',
                'message': data
            }
        )



    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self,'room_group_name'):
            # Lo stato dell'utente si azzera solo se questa e' ancora la sua connessione
            # piu' recente; se nel frattempo si e' riconnesso, lo stato e' della nuova.
            if _CONNESSIONE_ATTIVA.get(self.userWhitToken.id) == self.channel_name:
                del _CONNESSIONE_ATTIVA[self.userWhitToken.id]
                await self.remove_group(self.room_group_name)
                await self.reset_UserWhitToken()
                if self.smartglass:
                    await self.sendSmartGlassRefresh()
                else:
                    await self.sendUserGoneOffline()

            await self.channel_layer.group_discard(
                self.subGroupName,
                self.channel_name
            )
            # Senza questo il gruppo videouser_<id> / smartglass_<id> accumula
            # connessioni chiuse e gli squilli vanno anche a pagine non piu' aperte.
            if hasattr(self, 'originGroupName'):
                await self.channel_layer.group_discard(
                    self.originGroupName,
                    self.channel_name
                )
            await self.channel_layer.group_discard(
                SYSTEM,
                self.channel_name
            )
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )


    async def message_for_server(self, message):
        try:
            packet = json.loads(message)
            if (TYPE in packet):
                type = packet.get(TYPE)
                if type == CONTACTS:
                    await self.smartglassesMessageHandler()
                elif type == CALL:
                    await self.callMessageHandler(packet)
                elif type == CONTACT_REFRESH:
                    await self.smartglassRefreshMessageHandler(packet)
                elif type == CLOSE_CALL:
                    await self.closeCallMessageHandler(packet)
                elif type == ACCEPT_CALL:
                    await self.acceptCallMessageHandler(packet)
                elif type == REFUSE_CALL:
                    await self.refuseCallMessageHandler(packet)
                elif type == STATUS:
                    await self.statusMessageHandler(packet)
        except json.decoder.JSONDecodeError:
            pass

    async def statusMessageHandler(self, packet):
        busy = packet['msg']['busy']

        if self.smartglass:
            calling = packet['msg']['calling']
            await self.set_UserWhitToken(online=True,busy=busy, calling=calling)
            await self.sendSmartGlassRefresh()
        else:
            await self.set_UserWhitToken(online=True,busy=busy)


    async def smartglassRefreshMessageHandler(self, packet):
        smartglass_to_call_id = int(packet['msg']['id'])
        smartglass_to_call = await  self.get_smartglass(id=smartglass_to_call_id)

        msg = {
            "id": smartglass_to_call.id,
            "name": smartglass_to_call.name,
            "online": smartglass_to_call.is_online,
            "busy": smartglass_to_call.is_busy,
            "calling": smartglass_to_call.is_calling
        }
        data = {
            TYPE: 'contact',
            'msg': msg
        }
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': data
            }
        )

    async def refuseCallMessageHandler(self, packet):
        user_to_call_id = int(packet['msg']['id'])
        user_to_call = await  self.get_user(id=user_to_call_id)
        if self.smartglass:
            if user_to_call.is_online:
                await self.set_UserWhitToken(online=True, busy=packet['msg']['busy'], calling=False)
                from_user =await self.generateSelfDescriptor()
                to_user =await self.generateRemoteDescriptor(user_to_call)
                msg = {
                    "from": from_user,
                    "to": to_user,
                }
                data = {
                    TYPE: REFUSE_CALL,
                    'msg': msg
                }
                await self.channel_layer.group_send(
                    str(user_to_call.id),
                    {
                        'type': 'chat_message',
                        'message': data
                    }
                )
            else:
                pass

    async def acceptCallMessageHandler(self, packet):
        user_to_call_id = int(packet['msg']['id'])
        user_to_call = await  self.get_user(id=user_to_call_id)

        if user_to_call.is_online:
            await self.set_UserWhitToken(online=True, busy=packet['msg']['busy'],calling=False)
            from_user =await self.generateSelfDescriptor()
            to_user =await self.generateRemoteDescriptor(user_to_call)
            await self.set_UserWhitToken(online=True, busy=True, calling=False)
            user_to_call= await self.set_UserWhitToken(online=True, busy=True, calling=False, userWhitToken= user_to_call)
            if self.smartglass:
                await self.sendSmartGlassRefresh()
            else:
                msg_refresh = await self.generateRemoteDescriptor(user_to_call)
                await self.sendSmartGlassRefreshMsg(msg_refresh)
            if self.userWhitToken.id < user_to_call_id:
                name = str(self.userWhitToken.id) + '_' + str(user_to_call.id)
            else:
                name = str(packet['msg']['id']) + '_' + str(self.userWhitToken.id)
            ws_room_name = '/ws/chat/' + name + '/'

            msg = {
                "from": from_user,
                "to": to_user,
                'ws_room_url': ws_room_name,
            }
            data = {
                TYPE: ACCEPT_CALL,
                'msg': msg
            }

            await self.channel_layer.group_send(
                str(user_to_call.id),
                {
                    'type': 'chat_message',
                    'message': data
                }
            )
            msg = {
                "from": to_user,
                "to":  from_user ,
                'ws_room_url': ws_room_name,
            }
            data = {
                TYPE: ACCEPTED_CALL,
                'msg': msg
            }
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': data
                }
            )

        else:
            await self.set_UserWhitToken(online=False, busy=packet['msg']['busy'], calling=False)
            to_user = await self.generateSelfDescriptor()
            from_user =await self.generateRemoteDescriptor(user_to_call)

            msg = {
                "from": from_user,
                "to": to_user,
            }
            data = {
                TYPE: CLOSE_CALL,
                'msg': msg
            }
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': data
                }
            )



    async def closeCallMessageHandler(self, packet):
        if self.smartglass:
            await self.smartglassCloseCall(packet)
        else:
            await self.userCloseCall(packet)

    async def smartglassCloseCall(self, packet):
        to_user = await self.generateRemoteDescriptorBrodcastUser()
        await self.set_UserWhitToken(online=True, busy=packet['msg']['busy'], calling=False)
        from_user = await self.generateSelfDescriptor()
        msg = {
            "from": from_user,
            "to": to_user,
        }
        data = {
            TYPE: CLOSE_CALL,
            'msg': msg
        }
        await self.channel_layer.group_send(
            VIDEOUSER,
            {
                'type': 'chat_message',
                'message': data
            }
        )


    async def userCloseCall(self, packet):
        user_to_call_id = int(packet['msg']['id'])
        user_to_call = await  self.get_user(id=user_to_call_id)
        if user_to_call.is_online:
            await self.set_UserWhitToken(online=True, busy=packet['msg']['busy'])
            to_user =await self.generateRemoteDescriptor(user_to_call)
            from_user =await self.generateSelfDescriptor()
            msg = {
                "from": from_user,
                "to": to_user,
            }
            data = {
                TYPE: CLOSE_CALL,
                'msg': msg
            }
            await self.channel_layer.group_send(
                str(user_to_call.id),
                {
                    'type': 'chat_message',
                    'message': data
                }
            )

    async def smartglassesMessageHandler(self):
        smartglasses = await self.get_smartglasses()
        data = []
        for smartglass in smartglasses:
            item = {

                "id": smartglass.id,
                "name": smartglass.name,
                "online": smartglass.is_online,
                "busy": smartglass.is_busy,
                "calling": smartglass.is_calling

            }
            data.append(item)
        data = {
            TYPE: CONTACTS,
            'msg': data,
        }
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': data
            }
        )

    async def callMessageHandler(self, packet):
        if self.smartglass:
            await self.smartglassCall()

        else:
            await self.userCall(packet)

    async def smartglassCall(self):
        ##if not user_to_call_is_busy:
        await self.set_UserWhitToken(online=True, busy=True, calling=True)
        from_user = await self.generateSelfDescriptor()
        to_user = await self.generateRemoteDescriptorBrodcastUser()
        msg = {
            "from": from_user,
            "to": to_user,
        }
        data = {
            TYPE: CALLED,
            'msg': msg
        }
        await self.channel_layer.group_send(
            self.creatorGroupName,
            {
                'type': 'chat_message',
                'message': data,
            }
        )


    async def userCall(self, packet):
        user_to_call_id = int(packet['msg']['id'])
        user_to_call = await  self.get_user(id=user_to_call_id)
        if user_to_call and user_to_call.is_online and (not user_to_call.is_busy):
            if self.userWhitToken.id < user_to_call_id:
                name = str(self.userWhitToken.id) + '_' + str(user_to_call.id)
            else:
                name = str(packet['msg']['id']) + '_' + str(self.userWhitToken.id)
            ws_room_name = '/ws/chat/' + name + '/'
            msg = {
                'ws_room_url': ws_room_name,
                "id": user_to_call_id,
            }
            data = {
                TYPE: CALL,
                'msg': msg
            }
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': data
                }
            )
            ##if not user_to_call_is_busy:
            await self.set_UserWhitToken(online=True, busy=packet['msg']['busy'])
            from_user = await self.generateSelfDescriptor()

            to_user = await self.generateRemoteDescriptor(user_to_call)
            msg = {
                "from": from_user,
                "to": to_user,
                "ws_room_url": ws_room_name,
            }

            data = {
                TYPE: CALLED,
                'msg': msg
            }
            await self.channel_layer.group_send(
                str(user_to_call.id),
                {
                    'type': 'chat_message',
                    'message': data
                }
            )
        else:
            to_user = await self.generateRemoteDescriptor(user_to_call)
            msg = {
                'error': 'user offline',
                'user': to_user
            }
            data = {
                TYPE: 'contact',
                'error': True,
                'msg': msg,
            }
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': data
                }
            )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        if ('cmd' in text_data_json):
            cmd = text_data_json.get('cmd')
            if cmd == 'ping':
                data = {
                    'cmd': 'pong',
                }
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': data
                    }
                )
            elif cmd == 'pong':
                pass
        else:
            message = text_data_json['msg']
            await self.message_for_server(message)


    async def disconnect_group(self, g_name):

            group_to_delete=await self.exist_group(room_group_name=g_name)
            if group_to_delete:
                await self.remove_group(g_name)
            await self.channel_layer.group_send(
                g_name,
                {
                    'type': 'disconnect_now',
                }
            )




    # Receive message from room group
    async def disconnect_now(self, event):
        if self.smartglass:
            await self.sendSmartGlassRefresh()
        # Nello scope c'e' solo una delle due chiavi: con `del` andava sempre in
        # KeyError e la connessione vecchia restava iscritta ai gruppi.
        self.scope.pop('smartglass', None)
        self.scope.pop('videouser', None)
        await self.channel_layer.group_discard(
            SYSTEM,
            self.channel_name
        )
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.disconnect(0)
        await self.close(1000)

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps(
            message
        ))


    async def srtatusQuery(self):
        data = {
            TYPE: STATUS,
        }
        await self.channel_layer.group_send(
            SYSTEM,
            {
                'type': 'chat_message',
                'message': data
            }
        )




class chatConsumer(customConsumer):


    async def connect(self):
        if 'userWhitToken' in self.scope:
            self.userWhitToken = self.scope['userWhitToken']
            self.room_name = self.scope['url_route']['kwargs']['room_name']
            self.room_group_name = self.room_name
            users =self.room_name.split('_')
            if str(self.userWhitToken.id) in users:
                # Join room group
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
                await self.create_group(self.room_group_name, single_user = False)




    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        self.disconnect_group(self.room_group_name)


    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': text_data_json
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps(
            message
        ))

    async def disconnect_group(self, g_name):
        group_to_delete = await self.exist_group(room_group_name=g_name)
        if group_to_delete:
            await self.remove_group(g_name)
        await self.channel_layer.group_send(
            g_name,
            {
                'type': 'disconnect_now',
            }
        )

    # Receive message from room group
    async def disconnect_now(self, event):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.disconnect(0)
        await self.close(1000)
