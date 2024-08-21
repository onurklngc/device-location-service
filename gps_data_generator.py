import logging
import os
import time

import requests
from dotenv import load_dotenv

import config as cfg
from src.iot_device import IoTDevice, send_gps_data
from tests.create_devices import create_devices

load_dotenv()
tcp_server_host = os.getenv("TCP_SERVER_HOST", "0.0.0.0")
tcp_server_port = int(os.getenv("TCP_SERVER_PORT", "65432"))
webserver_url = os.getenv("WEBSERVER_URL", "http://localhost:8081")
num_devices = int(os.getenv("NUM_DEVICES_TO_CREATE", 100))
generation_interval = int(os.getenv("DATA_GENERATION_INTERVAL_PER_DEVICE", 10))

session = requests.Session()
logger = logging.getLogger(__name__)


def get_devices(server_url):
    devices = []
    query = """
    query {
      allDevices {
        id
        name
      }
    }
    """
    response = session.post(server_url + "/graphql", json={"query": query})
    data = response.json()

    if response.status_code == 200:
        devices = data["data"]["allDevices"]
    else:
        logger.error(f"Error retrieving devices: {data['errors']}")
    return devices


class DeviceStorer:
    def __init__(self, device_ids: list[int]):
        self.devices = {device_id: IoTDevice(device_id) for device_id in device_ids}

    def get_devices_gps_data(self):
        return {device_id: self.devices[device_id].generate_gps_data() for device_id in self.devices}

    def update_devices(self, device_ids: list[int]):
        removed_devices = self.devices.keys() - device_ids
        for k in removed_devices:
            self.devices.pop(k, None)
        new_devices = device_ids - self.devices.keys()
        for device_id in new_devices:
            self.devices[device_id] = IoTDevice(device_id)

    def move_devices(self):
        [device.move() for device in self.devices.values()]


def send_data_to_tcp_server(device_storer: DeviceStorer):
    devices = get_devices(webserver_url)
    logger.info(f"Number of devices: {len(devices)}")
    device_ids = [device["id"] for device in devices]
    device_storer.update_devices(device_ids)
    device_storer.move_devices()
    gps_data = device_storer.get_devices_gps_data()
    for gps in gps_data.values():
        send_gps_data(gps)


if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, cfg.LOG_LEVEL), format=cfg.LOGGING_FORMAT, datefmt=cfg.TIME_FORMAT)
    current_device_storer = DeviceStorer(device_ids=[])
    while True:
        try:
            create_devices(webserver_url, num_devices)
            break
        except Exception as e:
            logger.error(f"Couldn't create devices will try again: {e}")
            time.sleep(2)

    while True:
        try:
            send_data_to_tcp_server(current_device_storer)
        except (KeyboardInterrupt, InterruptedError):
            logger.info('Terminating data generator...')
            break
        except Exception as err:
            logger.exception(err)
        time.sleep(generation_interval)
