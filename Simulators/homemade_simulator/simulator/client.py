# region Imports
import websocket as ws
import json
import uuid
import threading
import time
import logging
from datetime import datetime
import random
# endregion

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def generate_random_readings():
    """
    Generate realistic random meter readings:
    - energy in Wh
    - power in W
    - current in A
    - voltage in V
    """

    # Voltage: residential/EV chargers usually ~220–240V (single-phase) or ~380–415V (three-phase)
    voltage = round(random.uniform(220, 240), 3)

    # Current: EV chargers usually between 6A and 32A for single-phase
    current = round(random.uniform(6, 32), 3)

    # Power (P = V * I, in W)
    power = round(voltage * current, 3)

    # Energy: assume cumulative meter reading, simulate random session size (0.1–50 kWh => 100–50,000 Wh)
    energy = round(random.uniform(100, 50000), 3)

    return {
        "energy_Wh": energy,
        "power_W": power,
        "current_A": current,
        "voltage_V": voltage
    }


class ChargingPointClient:
    def __init__(self, charger_barcode, ws_url):
        self.charger_barcode = charger_barcode
        self.ws_url = f"{ws_url}{charger_barcode}/"
        logger.debug(f"Constructed websocket URL: {self.ws_url}")
        self.ws = None

        self.connected = False
        self.heartbeat_thread = None
        self.meter_values_thread = None

    def on_open(self, ws):
        logger.info("Connected to backend.")
        self.connected = True
        self.send_boot_notification()
        self.heartbeat_thread = threading.Thread(target=self.send_heartbeat, daemon=True)
        self.heartbeat_thread.start()
        self.meter_values_thread = threading.Thread(target=self.send_meter_values, daemon=True)
        self.meter_values_thread.start()

    def on_message(self, ws, message):
        logger.info(f"Received message: {message}")
        try:
            data = json.loads(message)
            self.handle_message(data)
        except Exception as e:
            logger.exception(f"Error processing received message: {e}")

    def on_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        self.disconnect()
        logger.info(f"Connection closed: {close_msg}")

    def connect(self):
        logger.info(f"Connecting to {self.ws_url}")
        try:
            self.ws = ws.WebSocketApp(
                self.ws_url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )

            # Run the WebSocketApp in a thread
            threading.Thread(target=self.ws.run_forever, daemon=True).start()

        except Exception as e:
            logger.exception(f"Error connecting to WebSocket: {e}")
            self.disconnect()

    def disconnect(self):
        if self.ws:
            self.ws.close()
            self.connected = False
            logger.info("Disconnected from backend.")

    def send(self, message):
        if self.connected:
            self.ws.send(json.dumps(message))
        else:
            logger.warning("WebSocket is not connected.")

    def send_heartbeat(self):
        """
        A function to send periodic heartbeats every 2 mins to the charging station management system.
        """
        while self.connected:
            try:
                msg = [2, str(uuid.uuid4()), 'Heartbeat', {}]
                self.send(msg)
                logger.info("Sent Heartbeat")
                time.sleep(120)
            except Exception as e:
                logger.exception(f"Error sending Heartbeat: {e}")
                break

    def send_meter_values(self):
        """
        A function to send randomly generated meter values to the charging station management system.

        Attributes:
            - model (str): The model of the charging point.
            - barcode (str): The barcode of the charging point.
        """
        while self.connected:
            try:
                data = generate_random_readings()
                msg = [
                    2,
                    str(uuid.uuid4()),
                    "MeterValues",
                    {
                        "connectorId": 1,
                        "transactionId": 101,
                        "meterValue": [
                            {
                                "timestamp": datetime.now(),
                                "sampledValue": [
                                    {"measurand": "Energy.Active.Import.Register", "unit": "Wh", "value": data["energy_Wh"]},
                                    {"measurand": "Power.Active.Import", "unit": "W", "value": data["power_W"]},
                                    {"measurand": "Current.Import", "unit": "A", "value": data["current_A"]},
                                    {"measurand": "Voltage", "unit": "V", "value": data["voltage_V"]},
                                ]
                            }
                        ]
                    }
                ]
                self.send(msg)
                logger.info(f"Sent meter values for charger: {self.charger_barcode} - {data}")
                time.sleep(30)
            except Exception as e:
                logger.exception(f"Error sending MeterValues: {e}")
                break

    def send_boot_notification(self):
        """
        A function to send a boot notification to the charging station management system.
        """
        msg = [
            2,
            str(uuid.uuid4()),
            "BootNotification",
            {
                "chargePointVendor": "ABB",
                "chargePointModel": "Terra AC Wallbox",
                "chargePointSerialNumber": self.charger_barcode,
                "firmwareVersion": "1.8.32",
                "iccid": "89445001011527894567",
                "imsi": "310150123456789",
                "meterType": "InternalMeter",
                "meterSerialNumber": "MTR123456789"
            }
        ]
        self.send(msg)
        logger.info(f"Sent boot notification for charger: {self.charger_barcode}")

    def handle_message(self, message):
        """
        A function to handle incoming messages from the charging station management system.
        """
        logger.debug(f"Handling message: {message}")
        if isinstance(message, list):
            try:
                msg_type = message[0]
                unique_id = message[1]
                action = message[2]

                if msg_type == 2:
                    # Respond to backend commands with an empty payload
                    response = [3, unique_id, {}]
                    self.send(response)
                    logger.info(f"Acknowledged {action}")
                else:
                    logger.warning(f"Acknowledged message: {action}")
            except Exception as e:
                logger.exception(f"Error handling command: {e}")
        else:
            logger.warning(f"Received message of unknown type: {message}")

    def send_start_transaction(self):
        """
        A function to send a start transaction command to the charging station management system.
        """
        msg = [
            2,
            str(uuid.uuid4()),
            "StartTransaction",
            {
                "connectorId": 1,
                "idTag": "ABC12345",
                "timestamp": datetime.now(),
                "reservationId": 10
            }
        ]
        self.send(msg)
        logger.info("Sent StartTransaction")

    def send_stop_transaction(self):
        """
        A function to send a stop transaction command to the charging station management system.
        """
        reasons = [
            "EmergencyStop",
            "EVDisconnected",
            "HardReset",
            "Local",
            "Other",
            "PowerLoss",
            "Reboot",
            "Remote",
            "SoftReset",
            "UnlockCommand",
            "DeAuthorized"
        ]
        reason = random.choice(reasons)
        data = generate_random_readings()
        msg = [
            2,
            str(uuid.uuid4()),
            "StopTransaction",
         {
             "transactionId": 101,
             "idTag": "ABC12345",
             "timestamp": datetime.now(),
             "meterStop": data["energy_Wh"],
             "reason": reason,
             "transactionData": [
                 {
                     "timestamp": datetime.now(),
                     "sampledValue": [
                         {"measurand": "Energy.Active.Import.Register",
                             "unit": "Wh",
                             "value": data["energy_Wh"]},
                         {"measurand": "Power.Active.Import",
                          "unit": "W",
                          "value": data["power_W"]},
                         {"measurand": "Current.Import",
                          "unit": "A",
                          "value": data["current_A"]},
                         {"measurand": "Voltage",
                          "unit": "V",
                          "value": data["voltage_V"]},
                     ]
                 }
             ]
         }
        ]
        self.send(msg)
        logger.info("Sent StopTransaction")
