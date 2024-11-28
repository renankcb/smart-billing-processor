# Dockerfile atualizado
FROM python:3.11-slim

WORKDIR /app

# Atualizar o pip para a última versão antes de instalar dependências
RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
