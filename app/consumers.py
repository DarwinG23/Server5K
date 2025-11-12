import urllib.parse
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async


@database_sync_to_async
def get_user_from_token(token):
    from rest_framework_simplejwt.authentication import JWTAuthentication
    auth = JWTAuthentication()
    validated = auth.get_validated_token(token)
    return auth.get_user(validated)


class JuezConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Expect token in querystring: ?token=...
        qs = self.scope.get('query_string', b'').decode()
        params = urllib.parse.parse_qs(qs)
        token = params.get('token', [None])[0]
        if not token:
            await self.close()
            return

        try:
            user = await get_user_from_token(token)
        except Exception:
            await self.close()
            return

        self.user = user

        # Validate that user has juez_profile
        if not hasattr(self.user, 'juez_profile'):
            await self.close()
            return

        self.juez_id = str(self.scope['url_route']['kwargs'].get('juez_id'))
        if str(self.user.juez_profile.id) != self.juez_id:
            await self.close()
            return

        self.group_name = f'juez_{self.juez_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        except Exception:
            pass

    async def receive_json(self, content, **kwargs):
        # Optionally handle messages from client
        # For now, ignore or echo
        await self.send_json({'received': content})

    async def carrera_iniciada(self, event):
        await self.send_json({
            'type': 'carrera.iniciada',
            'data': event.get('data', {})
        })
