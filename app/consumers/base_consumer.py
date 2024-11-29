import aio_pika
import json
from loguru import logger


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

    async def declare_infrastructure(self):
        """
        Declara filas, exchanges e bindings.
        """
        connection = await self.connection_params.get_connection()
        async with connection:
            channel = await connection.channel()

            # Declaração da exchange principal
            exchange = await channel.declare_exchange(self.exchange_name, aio_pika.ExchangeType.DIRECT, durable=True)

            # Declaração da fila principal
            queue = await channel.declare_queue(self.queue_name, durable=True)
            await queue.bind(exchange, routing_key=self.routing_key)

            # Declaração da fila de retentativa
            retry_queue = await channel.declare_queue(
                self.retry_queue_name,
                durable=True,
                arguments={"x-dead-letter-exchange": self.exchange_name, "x-dead-letter-routing-key": self.routing_key},
            )
            await retry_queue.bind(exchange, routing_key=f"{self.routing_key}.retry")

            # Declaração da DLQ
            dlq_queue = await channel.declare_queue(self.dlq_name, durable=True)
            await dlq_queue.bind(exchange, routing_key=f"{self.routing_key}.dlq")

            logger.info(f"Infrastructure for queue {self.queue_name} declared successfully!")

    async def start_consuming(self, prefetch_count=1):
        """
        Inicia o consumo da fila.
        """
        connection = await self.connection_params.get_connection()
        async with connection:
            channel = await connection.channel()

            # Configura prefetch
            await channel.set_qos(prefetch_count=prefetch_count)

            queue = await channel.declare_queue(self.queue_name, durable=True)

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            await self.process_message(json.loads(message.body))
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            await self.handle_failure(channel, message)

    async def handle_failure(self, channel, message):
        """
        Tratamento de falhas com retentativa e envio para DLQ.
        """
        retry_count = message.headers.get("x-retry-count", 0)

        if retry_count < 3:  # Máximo de 3 retentativas
            new_headers = message.headers.copy()
            new_headers["x-retry-count"] = retry_count + 1
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=message.body,
                    headers=new_headers,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=f"{self.routing_key}.retry",
            )
        else:
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=message.body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=f"{self.routing_key}.dlq",
            )

    async def process_message(self, message):
        """
        Método a ser implementado pelos consumidores específicos.
        """
        raise NotImplementedError("Subclasses devem implementar o método `process_message`.")
