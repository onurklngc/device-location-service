import argparse
import datetime
import json
import logging
import os
import time

import pika
from dotenv import load_dotenv

import config as cfg
from src.database_service import DatabaseService
from src.model import Location

INSERT_LOCATION_QUERY = """
    INSERT INTO `locations` (`device_id`, `latitude`, `longitude`, `timestamp`)
    VALUES (%s, %s, %s, %s)
"""

load_dotenv()
logger = logging.getLogger(__name__)
db_url = os.getenv("DATABASE_URL")
rabbitmq_host = os.getenv("RABBITMQ_HOST")
rabbitmq_port = os.getenv("RABBITMQ_PORT")
rabbitmq_gps_queue = os.getenv("RABBITMQ_GPS_QUEUE")


class GPSDataProcessor:
    def __init__(self, database_url):
        self.database_url = database_url
        self.database_config = self.connect_to_db()

    def connect_to_db(self):
        while True:
            try:
                database_config = DatabaseService(database_url=self.database_url)
                break
            except Exception as e:
                logger.error(f"Couldn't connect to DB: {e}, will try again shortly after.")
                time.sleep(2)

        return database_config

    def process_gps_data(self, message_body):
        try:
            message_data = json.loads(message_body)
            device_id = message_data["device_id"]
            latitude = message_data["latitude"]
            longitude = message_data["longitude"]
            timestamp = message_data["timestamp"]
            timestamp = datetime.datetime.utcfromtimestamp(timestamp)


            db_location = Location(device_id=device_id, latitude=latitude, longitude=longitude, timestamp=timestamp)
            db = next(self.database_config.get_db())
            db.add(db_location)
            db.commit()
            logger.info(f"Location data for device #{device_id} is saved successfully!")
        except Exception as e:
            logger.exception(f"Error processing GPS data: {e}\nBody: {message_body}")


class RabbitMQListener:
    def __init__(self, process_method, host, port, queue_name):
        self.process_method = process_method
        self.rabbitmq_host = host
        self.rabbitmq_port = port
        self.rabbitmq_queue = queue_name

    def queue_callback(self, ch, method, properties, body):
        try:
            self.process_method(body)
        except Exception:
            logger.exception(f"Error: unable to process queue message: {body}")

    def listen_queue(self):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.rabbitmq_host, port=self.rabbitmq_port))
        channel = connection.channel()
        channel.queue_declare(queue=self.rabbitmq_queue)
        channel.basic_consume(queue=self.rabbitmq_queue, auto_ack=True, on_message_callback=self.queue_callback)
        logger.info(f' [*] Waiting for messages on queue {self.rabbitmq_queue}.')
        channel.start_consuming()

    def start(self):
        while True:
            try:
                self.listen_queue()
            except (KeyboardInterrupt, InterruptedError):
                logger.info('Preparing to terminate...')
                break
            except Exception:
                logger.exception("Error occurred while listening to the queue:")


if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, cfg.LOG_LEVEL),
                        format=cfg.LOGGING_FORMAT, datefmt=cfg.TIME_FORMAT)

    gps_processor = GPSDataProcessor(db_url)
    queue_listener = RabbitMQListener(process_method=gps_processor.process_gps_data, host=rabbitmq_host,
                                      port=rabbitmq_port, queue_name=rabbitmq_gps_queue)
    queue_listener.start()
