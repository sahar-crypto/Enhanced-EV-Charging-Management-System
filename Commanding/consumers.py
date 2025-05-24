import logging
import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from Users.models import Customer
from Charging.models import EVCharger
from Commanding.models import Transaction, StatusLog, HeartbeatLog
from django.db import transaction
from ocpp.routing import on
from ocpp.v16 import ChargePoint as cp
from ocpp.v16.enums import RegistrationStatus
from ocpp.v16 import call_result
from datetime import datetime


logger = logging.getLogger(__name__)
connected_chargers = {}

class ChargePoint(cp):
    @on('BootNotification')
    async def on_boot_notification(self, charge_point_model, charge_point_vendor, **kwargs):
        logger.info(f"[{self.id}] BootNotification from model '{charge_point_model}', vendor '{charge_point_vendor}'")
        return call_result.BootNotificationPayload(
            current_time=datetime.now().isoformat(),
            interval=10,
            status=RegistrationStatus.accepted
        )

    @on('Heartbeat')
    async def on_heartbeat(self):
        logger.info(f"[{self.id}] Received Heartbeat")
        return call_result.HeartbeatPayload(current_time=datetime.now().isoformat())

class ChargingConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        self.charger_id = None
        self.user = None
        self.group_name = None
        super().__init__(*args, **kwargs)
    async def connect(self):
        """
        Connects the WebSocket to an EV station using the station code provided in the URL. It retrieves,
        validates, and decodes an authorization token presented in the headers, authenticating a user and
        adding them to a communication group specific to the station. If the user is authenticated, the WebSocket
        connection is accepted with or without a specified protocol, depending on the request.

        Attributes:
            station_id (str): The ID of the electric vehicle station extracted from the URL route.
            group_name (str): The name of the communication group for the specific station, formatted as
                'ev_station_<station_id>'.
            user (User or AnonymousUser): The user associated with the WebSocket connection, determined based
                on the validity of the authorization token.
        """
        self.station_id = self.scope['url_route']['kwargs']['station_code']
        self.charger_id = self.scope['url_route']['kwargs']['serial_number']
        self.group_name = f'ev_charger_{self.charger_id}'
        # Extract token from Authorization header
        token = None
        for header in self.scope['headers']:
            if header[0] == b'authorization':
                token = header[1].decode().split(' ')[1]  # Extract token part from 'Bearer <token>'
                break

        # if not token:
        #     await self.close()
        #     return

        logger.info(f"Token received: {'*' * 10}")

        try:
            # Decode and validate the token
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            self.user = await database_sync_to_async(get_user_model().objects.get)(id=user_id)
            self.scope['user'] = self.user
            logger.info(f"User authenticated: {self.user.username} with ID {user_id}")
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            self.scope['user'] = AnonymousUser()
            self.user = AnonymousUser()

        # Check if the user is authenticated
        # if not self.scope['user'].is_authenticated:
        #     logger.error(f"User is not authenticated, closing connection.")
        #     await self.close()
        #     return
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        logger.info(f"Scope user: {self.user}, Charger ID: {self.charger_id}")
        subprotocols = self.scope.get("subprotocols", [])
        if "ocpp1.6" in subprotocols:
            await self.accept(subprotocol="ocpp1.6")
        else:
            await self.accept()

        # Initialize ChargePoint instance and register router
        self.charge_point = ChargePoint(self.charger_id, self)

        # Store the charge point globally for later access
        connected_chargers[self.charger_id] = self.charge_point

        await self.send(text_data=f"Connected to charger {self.charger_id}")
        logger.info(f"Charger {self.charger_id} connected.")

    async def disconnect(self, close_code):

        """
        Disconnects the current WebSocket connection and performs associated cleanup.
        This method is typically called when a WebSocket client disconnects. It handles
        removing the WebSocket connection from the associated channel group and logs
        the disconnection event or a configuration error if the channel layer is not
        properly set.

        Parameters:
            close_code: int
                The close code that indicates the reason for the WebSocket disconnection.
        """
        if self.charger_id in connected_chargers:
            del connected_chargers[self.charger_id]

        if self.channel_layer is not None:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"Station {self.charger_id} disconnected.")
        else:
            logger.error("Channel layer is not configured.")

    async def receive(self, text_data):

        """
        Receives and processes data sent from a charging station. The method decodes
        and processes incoming JSON messages, discriminating different operation statuses,
        and carries out appropriate handling or delegations. It also interfaces with
        a configured channel layer to broadcast updates about charging station statuses
        to a group, provided setup is available.

        Args:
            text_data (str): The JSON-encoded string sent from a charging station containing
                details like serial number, status, and potentially additional data.

        Raises:
            Exception: For various errors encountered during the processing of the received message,
                such as JSON decoding issues, missing data, or unexpected operation states.
        """
        logger.info("Receiving data from charging station.")
        try:
            msg = json.loads(text_data)
            message_type = msg[0]
            if message_type != 2:
                logger.warning(f"Unsupported message type: {message_type}")
                return
            await self.charge_point.route_message(msg)
            action = msg[2]
            payload = msg[3]
            if message_type == 2 and action == "Heartbeat":
                await self.save_heartbeat(self.charger_id, payload)
            elif message_type == 2 and action in ["StartTransaction", "StopTransaction"]:
                await self.save_transaction(self.charger_id, action)
            elif message_type == 2 and action in ["StatusNotification", "DiagnosticsStatusNotification"]:
                await self.save_status(self.charger_id, action, payload)
                await self.update_charger_status(self.charger_id, action)

            if self.channel_layer is not None:
                await self.channel_layer.group_send(
                    'charging_dashboard',
                    {
                        'type': 'broadcast_status',
                        'charger_serial_number': self.charger_id,
                        'status_data': msg
                    }
                )
            else:
                logger.error("Channel layer is not configured.")
        except Exception as e:
            logger.error(f"[{self.charger_id}] Error processing message: {e}")
            await self.send(text_data=json.dumps({'error': str(e)}))

    async def send_command(self, event):

        """
        Sends a command to an electric vehicle charger for execution, handling command
        validation, charger state, and updating necessary records. Commands can either
        start or stop charging based on the charger's activity state.

        Sections:
        Args:
            event: dict
                An event dictionary containing the 'command' to execute and optionally
                the 'target_charger' serial number.

        Raises:
            No explicit exceptions are raised. Errors are logged and serialized JSON
            error responses are sent back to the client.
        """
        command = event['command']
        target_charger = event.get('target_charger')
        group_name = f'ev_charger_{target_charger}'
        try:
            charger = EVCharger.objects.get(serial_number=target_charger)
        except EVCharger.DoesNotExist:
            logger.error(f"Charger {target_charger} does not exist.")
            return
        # Check if the charger is already busy or available
        if command.lower() == 'remotestarttransaction' and charger.activity == 'charging':
            logger.info(f"Charger {target_charger} is already charging, ignoring command.")
            await self.send(text_data=json.dumps({
                'error': 'target charger is busy, cannot start charging.',
            }))
            return
        elif command.lower() == 'remotestoptransaction' and charger.activity == 'idle':
            logger.info(f"Charger {target_charger} is already available, ignoring command.")
            await self.send(text_data=json.dumps({
                'error': 'target charger is already idle, cannot stop charging.',
            }))
            return
        # If the command is compatible with the charger status, send it
        else:
            await self.send(text_data=json.dumps({
                'event': 'command_received',
                'command': command,
                'target_charger': target_charger
            }))
        try:
            await self.channel_layer.group_send(
                group_name,
                {
                    'type': 'send',
                    'event': 'command_received',
                    'command': command,
                    'target_charger': target_charger
                }
            )
            await self.save_transaction(target_charger, command)
            await self.update_charger_status(target_charger, command)
            logger.info(f"Command sent to charger {target_charger}: {command}")
        except Exception as e:
            logger.error(f"Error sending command to charger {target_charger}: {e}")
            await self.send(text_data=json.dumps({'error': str(e)}))

    async def broadcast_status(self, event):

        logger.info("Broadcasting status to all connected consumers.")
        await self.send(text_data=json.dumps({
            'event': 'status_update',
            'charger_id': event['charger_serial_number'],
            'data': event['status_data'],
        }))

    @database_sync_to_async
    def save_status(self, serial_number, status, payload):
        with transaction.atomic():
            charger, _ = EVCharger.objects.get_or_create(serial_number=serial_number)
            StatusLog.objects.create(charger=charger,
                                     status=status,
                                     payload=payload)
            logger.info(
                f"Status update received from charger {serial_number}: {status} - {payload}"
            )

    @database_sync_to_async
    def save_heartbeat(self, serial_number, data):
        charger, _ = EVCharger.objects.get_or_create(serial_number=serial_number)
        HeartbeatLog.objects.create(charger=charger, payload=data)
        logger.info(f"Heartbeat received from charger {serial_number}: {data}")

    @database_sync_to_async
    def save_transaction(self, serial_number, command):
        if not hasattr(self, 'user') or self.user is None or not self.user.is_authenticated:
            logger.error("Cannot save transaction: No authenticated user")
            return

        try:
            customer = Customer.objects.get(user=self.user)
        except Customer.DoesNotExist:
            logger.error(f"No Customer found for user {self.user}")
            return

        try:
            charger = EVCharger.objects.get(serial_number=serial_number)
        except EVCharger.DoesNotExist:
            logger.error(f"No charger found with serial number {serial_number}")
            return

        with transaction.atomic():
            Transaction.objects.create(
                charger=charger,
                command=command,
                customer=customer
            )

        logger.info(f"Transaction saved for charger {serial_number} with command {command}")

    @database_sync_to_async
    def update_charger_status(self, serial_number, command):
        # Update charger status based on command
        cmd = command.lower()
        if 'start' in cmd:
            status = 'busy'
            activity = 'charging'
            connected = True
        elif 'stop' in cmd:
            status = 'available'
            activity = 'idle'
            connected = False
        else:
            status = 'unknown'
            activity = 'unknown'
            connected = False

        charger, _ = EVCharger.objects.get_or_create(serial_number=serial_number)
        charger.status = status
        charger.activity = activity
        charger.connected = connected
        charger.save()

        StatusLog.objects.create(charger=charger, status=status)
        logger.info(f"Updated charger {serial_number} status to {status} based on command {command}")
