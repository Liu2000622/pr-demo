# ---- build / runtime (single stage; Python needs no compile step) ----
FROM python:3.11-slim

WORKDIR /app

# System deps: libjpeg/libpng are required by Pillow; fonts are used for the
# captcha rendering (mirrors Java's SansSerif).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libjpeg62-turbo libpng16-16 \
       fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir \
        -i https://mirrors.aliyun.com/pypi/simple/ \
        -r requirements.txt

COPY app ./app

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

# Same default port as the Java app (server.port=8080).
ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
