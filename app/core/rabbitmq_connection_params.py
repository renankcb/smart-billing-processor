import aio_pika

class RabbitMQConnectionParams:
    """
    Classe responsável por gerenciar os parâmetros de conexão com o RabbitMQ para uso com aio_pika.
    """

    def __init__(self, host: str = "rabbitmq", port: int = 5672, username: str = "guest", password: str = "guest"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    async def get_connection(self) -> aio_pika.RobustConnection:
        """
        Retorna uma conexão assíncrona configurada com RabbitMQ.

        Returns:
            aio_pika.RobustConnection: Conexão configurada.
        """
        return await aio_pika.connect_robust(
            f"amqp://{self.username}:{self.password}@{self.host}:{self.port}/"
        )
