import asyncio
import os
from dotenv import load_dotenv
from .client import ChargingStationClient

# Load .env file
load_dotenv()


def run_simulator():
    ws_url = os.getenv("WS_URL")
    charger_id = os.getenv("CHARGER_ID")

    if not ws_url or not charger_id:
        raise Exception("Missing WS_URL or CHARGER_ID in environment variables.")

    client = ChargingStationClient(charger_id, ws_url)
    asyncio.run(client.connect())
