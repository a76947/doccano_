import json
from channels.generic.websocket import AsyncWebsocketConsumer

# Store messages in memory (replace with database in production)
chat_messages = {}

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.room_group_name = f'chat_{self.project_id}'

        # Initialize message list for this project if it doesn't exist
        if self.project_id not in chat_messages:
            chat_messages[self.project_id] = []

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Send existing messages when user connects
        if self.project_id in chat_messages:
            for message in chat_messages[self.project_id]:
                await self.send(text_data=json.dumps(message))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        user = text_data_json.get('user', 'Anonymous')
        message = text_data_json.get('message')
        
        # Store the message
        if self.project_id not in chat_messages:
            chat_messages[self.project_id] = []
        
        message_obj = {'user': user, 'text': message}
        chat_messages[self.project_id].append(message_obj)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_obj
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps(message))