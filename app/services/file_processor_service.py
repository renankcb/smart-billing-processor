import csv
from loguru import logger
from uuid import uuid4
from app.schemas.chunk import ChunkRow
from typing import Generator, List
import os
import json


class FileProcessorService:
    """
    Serviço para dividir arquivos em chunks para processamento paralelo.
    """

    def process_file(self, file_path: str, chunk_size: int = 200) -> Generator[List[dict], None, None]:
        """
        Divide o arquivo em chunks.

        Args:
            file_path (str): Caminho do arquivo a ser processado.
            chunk_size (int): Número de linhas por chunk.

        Yields:
            List[dict]: Um chunk contendo múltiplos registros validados.
        """
        valid_lines = 0
        invalid_lines = 0
        invalid_rows = []

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                chunk = []
                for i, row in enumerate(reader):
                    row["debt_id"] = str(uuid4())  # Adiciona um ID único para cada dívida
                    try:
                        validated_row = ChunkRow(**row)  # Validação com Pydantic
                        chunk.append(validated_row.dict())
                        valid_lines += 1
                    except Exception as e:
                        logger.error(f"Invalid row at line {i + 1}: {e}")
                        invalid_rows.append({"line_number": i + 1, "row": row, "error": str(e)})
                        invalid_lines += 1

                    if len(chunk) >= chunk_size:
                        yield chunk
                        chunk = []

                if chunk:
                    yield chunk

            # Log de linhas inválidas
            if invalid_rows:
                self._log_invalid_rows(file_path, invalid_rows)

            # Relatório de processamento
            logger.info(
                f"Processing completed for file {file_path}: "
                f"{valid_lines} valid lines, {invalid_lines} invalid lines."
            )
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise ValueError(f"Error processing file {file_path}: {e}")

    @staticmethod
    def _log_invalid_rows(file_path: str, invalid_rows: List[dict]):
        """
        Registra as linhas inválidas em um arquivo JSON.

        Args:
            file_path (str): Caminho do arquivo processado.
            invalid_rows (List[dict]): Lista de linhas inválidas com detalhes do erro.
        """
        base_name = os.path.basename(file_path)
        invalid_log_path = f"logs/invalid_rows_{base_name}.json"

        os.makedirs("logs", exist_ok=True)
        with open(invalid_log_path, "w", encoding="utf-8") as log_file:
            json.dump(invalid_rows, log_file, indent=4)

        logger.info(f"Invalid rows logged to {invalid_log_path}")