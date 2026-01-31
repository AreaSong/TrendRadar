FROM python:3.10-slim

WORKDIR /app

# 使用预下载的 supercronic（避免网络问题）
# 原始下载地址: https://github.com/aptible/supercronic/releases/download/v0.2.39/
ARG TARGETARCH
COPY docker/supercronic-linux-amd64 /tmp/supercronic-linux-amd64
COPY docker/supercronic-linux-arm64 /tmp/supercronic-linux-arm64
RUN ARCH_FILE="supercronic-linux-${TARGETARCH}" && \
    cp /tmp/${ARCH_FILE} /usr/local/bin/${ARCH_FILE} && \
    chmod +x /usr/local/bin/${ARCH_FILE} && \
    ln -s /usr/local/bin/${ARCH_FILE} /usr/local/bin/supercronic && \
    supercronic -version && \
    rm -f /tmp/supercronic-linux-*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY docker/manage.py .
COPY trendradar/ ./trendradar/

# 复制 entrypoint.sh 并强制转换为 LF 格式
COPY docker/entrypoint.sh /entrypoint.sh.tmp
RUN sed -i 's/\r$//' /entrypoint.sh.tmp && \
    mv /entrypoint.sh.tmp /entrypoint.sh && \
    chmod +x /entrypoint.sh && \
    chmod +x manage.py && \
    mkdir -p /app/config /app/output

ENV PYTHONUNBUFFERED=1 \
    CONFIG_PATH=/app/config/config.yaml \
    FREQUENCY_WORDS_PATH=/app/config/frequency_words.txt

ENTRYPOINT ["/entrypoint.sh"]