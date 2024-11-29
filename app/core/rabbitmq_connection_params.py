import pika


class RabbitMQConnectionParams:
    """
    Classe responsável por gerenciar os parâmetros de conexão com o RabbitMQ.
    """

    def __init__(self, host: str = "rabbitmq", port: int = 5672, username: str = "guest", password: str = "guest"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def get_connection(self) -> pika.ConnectionParameters:
        """
        Retorna os parâmetros de conexão configurados.

        Returns:
            pika.ConnectionParameters: Parâmetros configurados para conexão.
        """
        credentials = pika.PlainCredentials(self.username, self.password)
        return pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials,
            heartbeat=60,
            blocked_connection_timeout=30,
        )
