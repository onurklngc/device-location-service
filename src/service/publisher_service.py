import json
import logging

import pika

logger = logging.getLogger(__name__)


class RabbitMQPublisherService:
    def __init__(self, rabbitmq_host, rabbitmq_port, queues_to_declare: list = None):
        self.rabbitmq_connection_parameters = pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port)
        self.declared_queues = set()
        if queues_to_declare:
            queues_to_declare = set(queues_to_declare)
            connection = pika.BlockingConnection(self.rabbitmq_connection_parameters)
            channel = connection.channel()
            for queue_name in queues_to_declare:
                channel.queue_declare(queue=queue_name)
            self.declared_queues = queues_to_declare

    def publish(self, queue_name, message_data):
        connection = pika.BlockingConnection(self.rabbitmq_connection_parameters)
        channel = connection.channel()
        if queue_name not in self.declared_queues:
            channel.queue_declare(queue=queue_name)
            self.declared_queues.add(queue_name)

        body = json.dumps(message_data).encode()
        channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(message_data).encode())
        logger.info(f"RabbitMQ publisher sent: {body}")
