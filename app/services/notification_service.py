from loguru import logger

class NotificationService:
    """
    Serviço responsável por notificar os usuários sobre boletos gerados.
    """

    def __init__(self):
        # Aqui você pode configurar serviços externos de notificação, como email ou SMS
        pass

    async def notify_user(self, user_id: str, boleto_id: str):
        """
        Notifica um usuário que um boleto foi gerado.

        Args:
            user_id (str): ID do usuário.
            boleto_id (str): ID do boleto gerado.

        Raises:
            ValueError: Se parâmetros obrigatórios estiverem faltando.
        """
        if not user_id or not boleto_id:
            raise ValueError("Both 'user_id' and 'boleto_id' are required for notification.")

        try:
            # Implementar aqui logica envio de notificaçao para usuario relacionado ao boleto.
            logger.info(f"Notifying User ID: {user_id} about Boleto ID: {boleto_id}")
        except Exception as e:
            logger.error(f"Failed to notify user {user_id} about boleto {boleto_id}: {e}")
            raise
