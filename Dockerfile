FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=4443 \
    FILES_DIR=/data

WORKDIR /app

RUN groupadd --system app \
    && useradd --system --gid app --create-home --home-dir /home/app app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py ./
COPY docker-entrypoint.py /usr/local/bin/docker-entrypoint.py

RUN mkdir -p /data \
    && chown -R app:app /app /data \
    && chmod 755 /usr/local/bin/docker-entrypoint.py

EXPOSE 4443

VOLUME ["/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; port = os.environ.get('PORT', '4443'); urllib.request.urlopen(f'http://127.0.0.1:{port}/healthz', timeout=3)"

ENTRYPOINT ["python", "/usr/local/bin/docker-entrypoint.py"]
