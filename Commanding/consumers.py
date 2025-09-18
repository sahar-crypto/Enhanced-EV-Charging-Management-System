import logging
import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from Users.models import Customer
from Charging.models import EVCharger
from Commanding.models import Transaction, StatusLog, HeartbeatLog
from django.db import transaction
from ocpp.routing import on
from ocpp.v16 import ChargePoint as cp
from ocpp.v16.enums import RegistrationStatus, AuthorizationStatus
from ocpp.v16 import call_result
from django.utils.timezone import now
from django.conf import settings

logger = logging.getLogger(__name__)
connected_chargers = {}

class ChargePoint(cp):
    def __init__(self, id, connection):
        super().__init__(id, connection)
        self.id = id

    @on('BootNotification')
    async def on_boot_notification(self, charge_point_model, **kwargs):
        interval = getattr(settings, "HEARTBEAT_INTERVAL", 10)
        logger.info(f"[{self.id}] BootNotification from model '{charge_point_model}'")
        return call_result.BootNotification(
            current_time=now().isoformat(),
            interval=interval,
            status=RegistrationStatus.accepted
        )

    @on('Heartbeat')
    async def on_heartbeat(self):
        logger.info(f"[{self.id}] Received Heartbeat")
        return call_result.Heartbeat(current_time=now().isoformat())

    @on('StatusNotification')
    async def on_status_notification(self, status, connector_id, **kwargs):
        logger.info(f"[{self.id}] StatusNotification: {status} for connector {connector_id}")
        return call_result.StatusNotification()

    @on('StartTransaction')
    async def on_start_transaction(self, id_tag, connector_id, meter_start, timestamp, **kwargs):
        logger.info(f"[{self.id}] StartTransaction from {id_tag} on connector {connector_id}")
        # In a real system, validate the id_tag and generate a real transaction_id
        return call_result.StartTransaction(
            transaction_id=1,
            id_tag_info={
                'status': AuthorizationStatus.accepted.value
            }
        )

    @on('StopTransaction')
    async def on_stop_transaction(self, meter_stop, timestamp, transaction_id, **kwargs):
        logger.info(f"[{self.id}] StopTransaction for transaction {transaction_id}")
        return call_result.StopTransaction()

class BaseConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        self.charger_id = None
        self.station_id = None
        self.user = None
        self.group_name = None
        super().__init__(*args, **kwargs)

    async def broadcast_status(self, event):

        logger.info("Broadcasting status to all connected consumers.")
        await self.send_json({
            'event': 'status_update',
            'charger_id': event['charger_serial_number'],
            'status': event['status'],
        })

    async def broadcast_heartbeat(self, event):

        logger.info("Broadcasting heartbeat to all connected consumers.")
        await self.send_json({
            'event': 'heartbeat_update',
            'charger_id': event['charger_serial_number'],
            'time': event['time'],
        })

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
        logger.info(f"Heartbeat saved for charger {serial_number}: {data}")

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
    def update_charger_status(self, serial_number, status='available'):

        charger, _ = EVCharger.objects.get_or_create(serial_number=serial_number)
        charger.status = status
        charger.save()

        StatusLog.objects.create(charger=charger, status=status)
        logger.info(f"Updated charger {serial_number} status to {status}")

    @database_sync_to_async
    def get_latest_status(self, charger_id):
        try:
            return EVCharger.objects.get(
                serial_number=charger_id
            ).status
        except EVCharger.DoesNotExist:
            return "Unknown"

class MonitoringConsumer(BaseConsumer):

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
        # Extract token from the authorization header
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

        # 🔁 Get the latest status and send it
        status = await self.get_latest_status(self.charger_id)
        await self.send_json({"status": status})
        await self.send_json({"message": f"Connected to charger {self.charger_id}"})
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

    async def receive_json(self, content, **kwargs):
        """
        Receives and processes JSON-decoded data sent from a charging station.

        Args:
            content (list or dict): Decoded JSON content from the charging station.
        """
        logger.info("Receiving data from charging station.")

        try:
            msg = content  # Already decoded from JSON

            if isinstance(msg, list) and len(msg) > 0:
                message_type = msg[0]
            else:
                logger.warning(f"Unexpected message format: {msg}")
                return

            if message_type != 2:
                logger.warning(f"Unsupported message type: {msg}")
                return

            # Route the message through your internal handler
            await self.charge_point.route_message(json.dumps(msg))
            logger.debug(f"Message received: {msg}")
            # Unpack action and payload
            action = msg[2]
            payload = msg[3] if len(msg) > 3 else {}

            if action == "Heartbeat":
                await self.save_heartbeat(self.charger_id, payload)
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'broadcast_heartbeat',
                        'charger_serial_number': self.charger_id,
                        'time': str(now().isoformat()),
                    }
                )
                logger.info(f"Broadcasted heartbeat to group {self.group_name}")
            elif action in ["StartTransaction", "StopTransaction"]:
                await self.save_transaction(self.charger_id, action)
                if action == "StartTransaction":
                    status = "Charing"
                else:
                    status = "Available"
                await self.update_charger_status(self.charger_id, status)
            elif action in ["StatusNotification", "DiagnosticsStatusNotification"]:
                status = payload.get("status")
                await self.save_status(self.charger_id, status, payload)
                await self.update_charger_status(self.charger_id, status)

            # Get latest charger info
            status = await self.get_latest_status(self.charger_id)

            # Broadcast status to group
            if self.channel_layer is not None:
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'broadcast_status',
                        'charger_serial_number': self.charger_id,
                        'status': status,
                    }
                )
                logger.info(f"Broadcasted status to group {self.group_name}")
            else:
                logger.error("Channel layer is not configured.")

        except Exception as e:
            logger.error(f"[{self.charger_id}] Error processing message: {e}")
            await self.send_json({'error': str(e)})

class CommandingConsumer(BaseConsumer):

    async def connect(self):
        self.station_id = self.scope['url_route']['kwargs']['station_code']
        self.charger_id = self.scope['url_route']['kwargs']['serial_number']
        self.group_name = f'ev_charger_{self.charger_id}'
        await self.accept()
        logger.info(f"Connected to commanding consumer for charger {self.charger_id}")

    async def receive_json(self, content, **kwargs):
        command = content.get("action")
        target_charger = self.charger_id
        logger.info(f"Sending command {command} to charger {target_charger}")

        # Route the message through your internal handler
        await self.charge_point.route_message(json.dumps(content))
        try:
            charger = EVCharger.objects.get(serial_number=target_charger)
        except EVCharger.DoesNotExist:
            logger.error(f"Charger {target_charger} does not exist.")
            return
        # Check if the charger is already busy or available
        if command.lower() == 'remotestarttransaction' and charger.status == 'charging':
            logger.info(f"Charger {target_charger} is already charging, ignoring command.")
            await self.send_json({
                'error': 'target charger is busy, cannot start charging.',
            })
            return
        elif command.lower() == 'remotestoptransaction' and charger.status == 'available':
            logger.info(f"Charger {target_charger} is already available, ignoring command.")
            await self.send_json({
                'error': 'target charger is already idle, cannot stop charging.',
            })
            return
        # If the command is compatible with the charger status, send it
        else:
            try:
                await self.save_transaction(target_charger, command)
                # Update charger status based on command
                cmd = command.lower()
                if 'start' in cmd:
                    status = 'charging'
                elif 'stop' in cmd:
                    status = 'available'
                else:
                    logger.error(f"Command {command} not supported for charger {target_charger}.")
                await self.update_charger_status(target_charger, status)
                await self.charge_point.route_message(content)

                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'broadcast_status',
                        'charger_serial_number': self.charger_id,
                        'status': status,
                    }
                )
                logger.info(f"Command sent to charger {target_charger}: {command}")
            except Exception as e:
                logger.error(f"Error sending command to charger {target_charger}: {e}")
                await self.send_json({'error': str(e)})