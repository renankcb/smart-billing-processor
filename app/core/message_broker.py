from abc import ABC, abstractmethod
from typing import Dict


class MessageBroker(ABC):
    """
    Interface para sistemas de mensagens.
    """

    @abstractmethod
    def publish_to_queue(self, exchange: str, routing_key: str, message: Dict):
        """
        Publica uma mensagem em uma fila.

        Args:
            exchange (str): Nome da exchange.
            routing_key (str): Chave de roteamento para a fila.
            message (Dict): Mensagem a ser publicada.
        """
        pass
