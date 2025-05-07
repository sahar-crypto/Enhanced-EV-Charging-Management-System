import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import StatusLog
from Charging.models import EVCharger


class ChargingStationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.serial_number = self.scope['url_route']['kwargs']['serial_number']
        self.group_name = f'ev_charger_{self.serial_number}'

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        print(f"Charger {self.serial_number} connected.")

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"Station {self.serial_number} disconnected.")

    # To send a message to the station from Django view
    async def send_command(self, event):
        command = event['command']
        await self.send(text_data=json.dumps({
            'command': command
        }))

    async def receive(self, text_data):
        data = json.loads(text_data)
        print(f"Received from station {self.serial_number}: {data}")
        status = data.get('status')

        # Find or create the charger instance
        charger, created = EVCharger.objects.get_or_create(serial_number=self.serial_number)

        # Save the status change
        StatusLog.objects.create(
            charger=charger,
            status=status,
        )
        # Example: Broadcast the status update to other subscribers
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            'charging',  # This group could be used for real-time dashboard updates
            {
                'type': 'broadcast_status',
                'charger_serial_number': self.serial_number,
                'status_data': data
            }
        )

    async def broadcast_status(self, event):
        await self.send(text_data=json.dumps({
            'event': 'status_update',
            'charger_serial_number': event['charger_serial_number'],
            'data': event['status_data'],
        }))

