import logging
import os

import requests
from dotenv import load_dotenv

import config as cfg

logger = logging.getLogger(__name__)

load_dotenv()
webserver_url = os.getenv("WEBSERVER_URL", "http://localhost:8081")
num_devices = int(os.getenv("NUM_DEVICES_TO_GENERATE", 100))


def create_devices(server_url: str, num_devices: int):
    """
    Creates a specified number of devices.

    Args:
        server_url: The base URL of webserver.
        num_devices: The number of devices to create.

    Returns:
        None
    """

    session = requests.Session()
    query = """
    mutation {
        createDevice(input: { name: "Device %s" }) {
            id
            name
        }
    }
    """
    successful_creations = 0
    for i in range(num_devices):
        device_name = query % (i + 1)
        response = session.post(server_url + "/graphql", json={"query": device_name})

        if response.status_code == 200:
            successful_creations += 1
    logger.info(f"{successful_creations}/{num_devices} device create requests sent successfully")



if __name__ == "__main__":
    logging.basicConfig(level=getattr(logging, cfg.LOG_LEVEL), format=cfg.LOGGING_FORMAT, datefmt=cfg.TIME_FORMAT)

    create_devices(webserver_url, num_devices)
