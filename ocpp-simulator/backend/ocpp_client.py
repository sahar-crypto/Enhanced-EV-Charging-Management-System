import asyncio
import websockets
import json
import uuid

class ChargingStationClient:
    def __init__(self, station_id, ws_url):
        self.station_id = station_id
        self.ws_url = ws_url
        self.ws = None

    async def connect(self):
        self.ws = await websockets.connect("ws://backend:9000/ws/charging/station/DTS-CC-001/CHG001/")
        print("Connected to backend.")
        asyncio.create_task(self.send_heartbeat())
        asyncio.create_task(self.listen())

    async def disconnect(self):
        if self.ws:
            await self.ws.close()
            print("Disconnected.")

    async def send_heartbeat(self):
        while True:
            try:
                msg = [
                    2, str(uuid.uuid4()), "Heartbeat", {}
                ]
                await self.ws.send(json.dumps(msg))
                print("Sent Heartbeat")
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
        await self.ws.send(json.dumps(msg))
        print(f"Sent Status: {status}")

    async def listen(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                print("Received command:", data)
                await self.handle_command(data)
        except Exception as e:
            print("Error:", e)

    async def handle_command(self, message):
        msg_type = message[0]
        unique_id = message[1]
        action = message[2]

        if msg_type == 2:
            # Accept any command with empty payload
            response = [3, unique_id, {}]
            await self.ws.send(json.dumps(response))
            print(f"Acknowledged {action}")
