# Use uma imagem base oficial do Python
FROM python:3.10-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia o arquivo requirements.txt e instala as dependências
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o conteúdo do diretório atual para o diretório de trabalho
COPY . .

# Expõe a porta que o FastAPI usará
EXPOSE 8000

# Comando para rodar o servidor Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]