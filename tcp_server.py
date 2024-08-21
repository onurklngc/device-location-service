import json
import logging
import queue
import socket

import config as cfg

TCP_SERVER_HOST = '127.0.0.1'
TCP_SERVER_PORT = 65432


class TCPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.gps_data_queue = queue.Queue()

    def handle_client_connection(self, client_socket):
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if data:
                logger.info(f"Received data: {data}")
                gps_data = json.loads(data)
                self.gps_data_queue.put(gps_data)
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


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=getattr(logging, cfg.LOG_LEVEL), format=cfg.LOGGING_FORMAT, datefmt=cfg.TIME_FORMAT)
    logger = logging.getLogger(__name__)
    server = TCPServer(host=TCP_SERVER_HOST, port=TCP_SERVER_PORT)
    server.start()
