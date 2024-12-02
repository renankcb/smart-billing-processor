import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import uuid4

from app.services.chunk_processing_service import ChunkProcessingService
from app.repositories.user_repository import UserRepository
from app.repositories.debt_repository import DebtRepository

class TestChunkProcessingService:
    @pytest.fixture
    def mock_session(self):
        """Cria um mock da sessão com todos os métodos necessários."""
        session = AsyncMock()
        # Mock do context manager da transação
        session.begin.return_value.__aenter__.return_value = None
        session.begin.return_value.__aexit__.return_value = None
        return session

    @pytest.fixture
    def mock_session_factory(self, mock_session):
        """Cria um mock do session factory que retorna um session mock configurado."""
        async def _session_factory():
            return AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=None)
            )
        return _session_factory

    @pytest.fixture
    def service(self, mock_session_factory):
        """Cria uma instância do serviço com o session factory mockado."""
        return ChunkProcessingService(mock_session_factory)

    @pytest.fixture
    def valid_chunk_data(self):
        """Dados de teste válidos."""
        return [{
            "name": "John Doe",
            "governmentId": "12345",
            "email": "john@example.com",
            "debtAmount": 1000.00,
            "debtDueDate": "2024-01-01",
            "debtId": str(uuid4())
        }]

    @pytest.mark.asyncio
    async def test_successful_chunk_processing(self, service, valid_chunk_data):
        """Teste de processamento bem-sucedido de chunk."""
        file_id = uuid4()

        # Configure os mocks dos repositórios
        with patch.object(UserRepository, '__init__', return_value=None), \
             patch.object(DebtRepository, '__init__', return_value=None), \
             patch.object(UserRepository, 'insert_users', new_callable=AsyncMock) as mock_insert_users, \
             patch.object(DebtRepository, 'insert_debts', new_callable=AsyncMock) as mock_insert_debts:

            # Execute o processamento
            await service.process_chunk(file_id, valid_chunk_data)

            # Verifique as chamadas
            mock_insert_users.assert_called_once()
            mock_insert_debts.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_data_handling(self, service):
        """Teste de tratamento de dados inválidos."""
        file_id = uuid4()
        invalid_chunk = [{
            "name": "",  # nome inválido
            "governmentId": "",  # ID inválido
            "email": "invalid-email",
            "debtAmount": "invalid",
            "debtDueDate": "invalid-date",
            "debtId": "invalid-uuid"
        }]

        with patch.object(UserRepository, '__init__', return_value=None), \
             patch.object(DebtRepository, '__init__', return_value=None), \
             patch.object(UserRepository, 'insert_users', new_callable=AsyncMock) as mock_insert_users, \
             patch.object(DebtRepository, 'insert_debts', new_callable=AsyncMock) as mock_insert_debts:

            await service.process_chunk(file_id, invalid_chunk)

            mock_insert_users.assert_not_called()
            mock_insert_debts.assert_not_called()

    @pytest.mark.asyncio
    async def test_user_integrity_error(self, service, valid_chunk_data):
        """Teste de erro de integridade na inserção de usuários."""
        file_id = uuid4()

        with patch.object(UserRepository, '__init__', return_value=None), \
             patch.object(DebtRepository, '__init__', return_value=None), \
             patch.object(UserRepository, 'insert_users', 
                         new_callable=AsyncMock, 
                         side_effect=IntegrityError(None, None, None)):

            with pytest.raises(IntegrityError):
                await service.process_chunk(file_id, valid_chunk_data)

    @pytest.mark.asyncio
    async def test_debt_integrity_error(self, service, valid_chunk_data):
        """Teste de erro de integridade na inserção de dívidas."""
        file_id = uuid4()

        with patch.object(UserRepository, '__init__', return_value=None), \
             patch.object(DebtRepository, '__init__', return_value=None), \
             patch.object(UserRepository, 'insert_users', new_callable=AsyncMock), \
             patch.object(DebtRepository, 'insert_debts', 
                         new_callable=AsyncMock, 
                         side_effect=IntegrityError(None, None, None)):

            with pytest.raises(IntegrityError):
                await service.process_chunk(file_id, valid_chunk_data)

    @pytest.mark.asyncio
    async def test_empty_chunk(self, service):
        """Teste de processamento de chunk vazio."""
        file_id = uuid4()
        empty_chunk = []

        with patch.object(UserRepository, '__init__', return_value=None), \
             patch.object(DebtRepository, '__init__', return_value=None), \
             patch.object(UserRepository, 'insert_users', new_callable=AsyncMock) as mock_insert_users, \
             patch.object(DebtRepository, 'insert_debts', new_callable=AsyncMock) as mock_insert_debts:

            await service.process_chunk(file_id, empty_chunk)

            mock_insert_users.assert_not_called()
            mock_insert_debts.assert_not_called()

    @pytest.mark.asyncio
    async def test_database_error(self, service, valid_chunk_data):
        """Teste de erro geral do banco de dados."""
        file_id = uuid4()

        with patch.object(UserRepository, '__init__', return_value=None), \
             patch.object(DebtRepository, '__init__', return_value=None), \
             patch.object(UserRepository, 'insert_users', 
                         new_callable=AsyncMock, 
                         side_effect=SQLAlchemyError("Database error")):

            with pytest.raises(SQLAlchemyError):
                await service.process_chunk(file_id, valid_chunk_data)