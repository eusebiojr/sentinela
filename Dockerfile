# Use Python 3.11 slim para menor tamanho da imagem
FROM python:3.11-slim

# Metadados da imagem
LABEL maintainer="Logistica MS - Suzano"
LABEL description="Sistema Sentinela - Gestão de Desvios Logísticos"

# Configurações de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=production

# Diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copia arquivo de dependências
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY app/ ./app/

# CORREÇÃO: Copia assets de dentro da pasta app
# COPY assets/ ./assets/  # LINHA ANTIGA - REMOVIDA
# Assets já estão dentro de app/assets

# Cria usuário não-root para segurança
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Porta que será exposta (Cloud Run usa PORT env var)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Comando para iniciar a aplicação
CMD ["python", "-m", "app.main"]