import logging
import os

import config as cfg
from src.iot_device import IoTDevice
from src.service.publisher_service import RabbitMQPublisherService

IOT_DEVICE_ID = 1

rabbitmq_host = os.getenv("RABBITMQ_HOST")
rabbitmq_port = os.getenv("RABBITMQ_PORT")
rabbitmq_queue = os.getenv("RABBITMQ_GPS_QUEUE")
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, cfg.LOG_LEVEL), format=cfg.LOGGING_FORMAT, datefmt=cfg.TIME_FORMAT)
    if not (rabbitmq_host and rabbitmq_port and rabbitmq_queue):
        logger.error("Error: One or more RabbitMQ environment variables are missing.")
        exit(1)
    iot_device = IoTDevice(device_id=IOT_DEVICE_ID)
    device_gps_data = iot_device.generate_gps_data()
    rabbitmq_publisher_service = RabbitMQPublisherService(rabbitmq_host=rabbitmq_host, rabbitmq_port=rabbitmq_port)
    rabbitmq_publisher_service.publish(rabbitmq_queue, device_gps_data)
