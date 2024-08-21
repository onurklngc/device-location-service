import json
import logging
import random
import socket
import time

import config as cfg

TCP_SERVER_HOST = '127.0.0.1'
TCP_SERVER_PORT = 65432
DEVICE_ID = 1
DATA_SEND_INTERVAL = 5
logger = logging.getLogger(__name__)


class IoTDevice:
    def __init__(self, device_id: int):
        self.device_id = device_id
        self.latitude = round(random.uniform(-90.0, 90.0), 6)
        self.longitude = round(random.uniform(-180.0, 180.0), 6)

    def move_device(self):
        self.latitude = round(random.uniform(-0.0001, 0.0001) + self.latitude, 6)
        self.longitude = round(random.uniform(-0.0001, 0.0001) + self.longitude, 6)

    def generate_gps_data(self):
        return {
            "device_id": self.device_id,
            "timestamp": int(time.time()),
            "latitude": self.latitude,
            "longitude": self.longitude
        }


def send_gps_data(gps_data: dict):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((TCP_SERVER_HOST, TCP_SERVER_PORT))
            message = json.dumps(gps_data).encode('utf-8')
            sock.sendall(message)
            logger.info(f"Sent GPS data: {gps_data}")
            response = sock.recv(1024)
            logger.info(f"Received from server: {response.decode('utf-8')}")
        except Exception as e:
            logger.info(f"Error: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=getattr(logging, cfg.LOG_LEVEL), format=cfg.LOGGING_FORMAT, datefmt=cfg.TIME_FORMAT)

    iot_device = IoTDevice(device_id=DEVICE_ID)
    while True:
        iot_device.move_device()
        device_gps_data = iot_device.generate_gps_data()
        send_gps_data(device_gps_data)
        time.sleep(DATA_SEND_INTERVAL)
