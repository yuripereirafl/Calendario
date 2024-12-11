# Usar uma imagem base do Python
FROM python:3.10-slim

# Definir o diretório de trabalho
WORKDIR /app

# Copiar os arquivos necessários para o container
COPY . /app

# Instalar as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Expor a porta 5000 para o Flask
EXPOSE 5000

# Comando para iniciar a aplicação
CMD ["python", "app.py"]
