import pika
import json
import logging

class BaseConsumer:
    """
    Consumer base para facilitar a criação de consumidores com boas práticas.
    Inclui suporte para DLQ, retentativa e bindings.
    """

    def __init__(self, queue_name, exchange_name, routing_key, connection_params, dlq_name=None, retry_queue_name=None):
        self.queue_name = queue_name
        self.exchange_name = exchange_name
        self.routing_key = routing_key
        self.connection_params = connection_params
        self.dlq_name = dlq_name or f"{queue_name}.dlq"
        self.retry_queue_name = retry_queue_name or f"{queue_name}.retry"

    def declare_infrastructure(self):
        """Declara filas, exchanges e bindings."""
        connection = pika.BlockingConnection(self.connection_params.get_connection())
        channel = connection.channel()

        # Declaração da exchange principal
        channel.exchange_declare(exchange=self.exchange_name, exchange_type="direct", durable=True)

        # Declaração da fila principal
        channel.queue_declare(queue=self.queue_name, durable=True)
        channel.queue_bind(exchange=self.exchange_name, queue=self.queue_name, routing_key=self.routing_key)

        # Declaração da fila de retentativa
        channel.queue_declare(
            queue=self.retry_queue_name,
            durable=True,
            arguments={"x-dead-letter-exchange": self.exchange_name, "x-dead-letter-routing-key": self.routing_key},
        )
        channel.queue_bind(exchange=self.exchange_name, queue=self.retry_queue_name, routing_key=f"{self.routing_key}.retry")

        # Declaração da DLQ
        channel.queue_declare(queue=self.dlq_name, durable=True)
        channel.queue_bind(exchange=self.exchange_name, queue=self.dlq_name, routing_key=f"{self.routing_key}.dlq")

        connection.close()

    def start_consuming(self):
        """Inicia o consumo da fila."""
        connection = pika.BlockingConnection(self.connection_params.get_connection())
        channel = connection.channel()

        def callback(ch, method, properties, body):
            try:
                self.process_message(json.loads(body))
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logging.error(f"Error processing message: {e}")
                self.handle_failure(ch, method, body, properties)

        channel.basic_consume(queue=self.queue_name, on_message_callback=callback)
        logging.info(f"Started consuming on queue {self.queue_name}")
        channel.start_consuming()

    def handle_failure(self, channel, method, body, properties):
        """Tratamento de falhas com retentativa e envio para DLQ."""
        # Aqui, poderíamos implementar lógica de retentativa antes de enviar para a DLQ
        headers = properties.headers or {}
        retry_count = int(headers.get("x-retry-count", 0))

        if retry_count < 3:  # Máximo de 3 retentativas
            new_headers = headers.copy()
            new_headers["x-retry-count"] = retry_count + 1
            channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=f"{self.routing_key}.retry",
                body=body,
                properties=pika.BasicProperties(
                    headers=new_headers,
                    delivery_mode=2,  # Persistente
                ),
            )
            logging.info(f"Retrying message, count: {retry_count + 1}")
        else:
            channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=f"{self.routing_key}.dlq",
                body=body,
            )
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def process_message(self, message):
        """Método a ser implementado pelos consumidores específicos."""
        raise NotImplementedError("Subclasses devem implementar o método `process_message`.")
