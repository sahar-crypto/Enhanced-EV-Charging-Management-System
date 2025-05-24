from fastapi import FastAPI
import asyncio
from ocpp_client import ChargingStationClient

app = FastAPI()
client = ChargingStationClient("SIMULATOR_01", "ws://host.docker.internal:8000/ws")

@app.get("/connect")
async def connect():
    asyncio.create_task(client.connect())
    return {"status": "connecting"}

@app.get("/disconnect")
async def disconnect():
    await client.disconnect()
    return {"status": "disconnected"}

@app.post("/status/{status}")
async def send_status(status: str):
    await client.send_status(status)
    return {"sent": status}
