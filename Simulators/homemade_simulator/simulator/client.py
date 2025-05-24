import asyncio
import websockets
import json
import uuid
import logging

logger = logging.getLogger(__name__)

class ChargingStationClient:
    def __init__(self, charger_id, ws_url):
        self.charger_id = charger_id
        self.ws_url = ws_url
        self.ws = None
        self.connected = False

    async def connect(self):
        self.ws = await websockets.connect(f"{self.ws_url}{self.charger_id}/")
        self.connected = True
        logger.info("Connected to backend.")
        asyncio.create_task(self.send_heartbeat())
        asyncio.create_task(self.listen())

    async def disconnect(self):
        if self.ws:
            await self.ws.close()
            self.connected = False
            logger.info("Backend disconnected.")

    async def send_heartbeat(self):
        while True:
            try:
                msg = [
                    2, str(uuid.uuid4()), "Heartbeat", {}
                ]
                msg = json.stringify(msg)
                await self.ws.send(json.dumps(msg))
                logger.info("Sent Heartbeat")
                await asyncio.sleep(10)
            except:
                break

    async def send_status(self, status):
        msg = [
            2, str(uuid.uuid4()), "StatusNotification",
            {
                "connectorId": 1,
                "status": status,
                "timestamp": "2025-01-01T00:00:00Z"
            }
        ]
        msg = json.stringify(msg)
        await self.ws.send(json.dumps(msg))
        logger.info(f"Sent Status: {status}")

    async def listen(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                logger.info("Received command:", data)
                await self.handle_command(data)
        except Exception as e:
            logger.error("Error:", e)

    async def handle_command(self, message):
        msg_type = message[0]
        unique_id = message[1]
        action = message[2]

        if msg_type == 2:
            # Accept any command with empty payload
            response = json.stringify([3, unique_id, {}])
            await self.ws.send(json.dumps(response))
            logger.info(f"Acknowledged {action}")
