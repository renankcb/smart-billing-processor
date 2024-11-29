import csv
import logging

logging.basicConfig(level=logging.INFO)


class FileProcessorService:
    """
    Serviço para dividir arquivos em chunks para processamento paralelo.
    """

    def process_file(self, file_path, chunk_size=5000):
        """
        Divide o arquivo em chunks.

        Args:
            file_path (str): Caminho do arquivo a ser processado.
            chunk_size (int): Número de linhas por chunk.

        Returns:
            Generator[List[str]]: Gera chunks, onde cada chunk é uma lista de linhas.
        """
        try:
            with open(file_path, "r") as file:
                reader = csv.reader(file)
                headers = next(reader)  # Lê os cabeçalhos para validação, se necessário
                chunk = []
                for i, line in enumerate(reader):
                    chunk.append(line)
                    if (i + 1) % chunk_size == 0:
                        logging.info(f"Yielding chunk with {chunk_size} rows.")
                        yield chunk
                        chunk = []
                if chunk:  # Retorna o último chunk
                    logging.info(f"Yielding final chunk with {len(chunk)} rows.")
                    yield chunk
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}")
            raise ValueError(f"Error processing file {file_path}: {e}")
