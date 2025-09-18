import os
from dotenv import load_dotenv
from client import ChargingStationClient
import logging

# Load .env file
load_dotenv()
logger = logging.getLogger(__name__)

def run_simulator():
    # ws_url = os.getenv("WS_URL", "ws://localhost:9000/ws/charging/station/DTS-CC-001/")
    # charger_id = os.getenv("CHARGER_ID", "CHG001")
    ws_url = "ws://localhost:9000/ws/charging/station/DTS-CC-001/"
    charger_id = "CHG001"

    if not ws_url or not charger_id:
        raise Exception("Missing WS_URL or CHARGER_ID in environment variables.")

    # Print the actual values being used
    logger.info(f"Connecting with WS_URL: {ws_url} and CHARGER_ID: {charger_id}")

    try:
        client = ChargingStationClient(charger_id, ws_url)
        client.connect()

        # Keep the main thread alive to allow background threads to run
        print("Simulator running. Press Ctrl+C to exit.")

    except KeyboardInterrupt:
        print("Shutting down simulator.")
        client.disconnect()

    except Exception as e:
        print(f"Error occurred while connecting to system. Error: {e}")