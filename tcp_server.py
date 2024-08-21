import json
import logging
import os
import queue
import socket
import threading
import time

from dotenv import load_dotenv

import config as cfg
from src.service.publisher_service import RabbitMQPublisherService

load_dotenv()
tcp_server_host = os.getenv("TCP_SERVER_HOST", "0.0.0.0")
tcp_server_port = int(os.getenv("TCP_SERVER_PORT", "65432"))
rabbitmq_host = os.getenv("RABBITMQ_HOST")
rabbitmq_port = os.getenv("RABBITMQ_PORT")
rabbitmq_queue = os.getenv("RABBITMQ_GPS_QUEUE")
logger = logging.getLogger(__name__)


class TCPServer:
    def __init__(self, host: str, port: int, output_queue: queue.Queue):
        self.host = host
        self.port = port
        self.output_queue = output_queue

    def handle_client_connection(self, client_socket):
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if data:
                logger.info(f"Received data: {data}")
                gps_data = json.loads(data)
                self.output_queue.put(gps_data)
                client_socket.sendall(b'ACK')
        except Exception as e:
            logger.error(f"Error handling client connection: {e}")
        finally:
            client_socket.close()

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            logger.info(f"Server listening on {self.host}:{self.port}")

            while True:
                client_socket, client_address = server_socket.accept()
                logger.info(f"Connected by {client_address}")
                self.handle_client_connection(client_socket)


class RabbitMQPublisher(RabbitMQPublisherService):
    def __init__(self, input_queue, rabbitmq_queue_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_queue = input_queue
        self.rabbitmq_queue_name = rabbitmq_queue_name

    def listen_internal_queue(self):
        while True:
            try:
                data = self.input_queue.get()
                self.publish(self.rabbitmq_queue_name, data)
            except (KeyboardInterrupt, InterruptedError):
                logger.info('Terminating internal queue listener...')
                break
            except Exception as err:
                logger.exception(err)
                time.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=getattr(logging, cfg.LOG_LEVEL), format=cfg.LOGGING_FORMAT, datefmt=cfg.TIME_FORMAT)
    logging.getLogger("pika").setLevel(logging.WARNING)

    if not (rabbitmq_host and rabbitmq_port and rabbitmq_queue):
        logger.error("Error: One or more RabbitMQ environment variables are missing.")
        exit(1)

    internal_queue = queue.Queue()
    server = TCPServer(host=tcp_server_host, port=tcp_server_port, output_queue=internal_queue)
    threading.Thread(target=server.start, daemon=True).start()
    rabbitmq_publisher = RabbitMQPublisher(input_queue=internal_queue, rabbitmq_queue_name=rabbitmq_queue,
                                           rabbitmq_host=rabbitmq_host,
                                           rabbitmq_port=rabbitmq_port)
    rabbitmq_publisher.listen_internal_queue()
