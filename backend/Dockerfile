FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 兜底：即使检出时被转成 CRLF，也修正为 LF，避免 shebang 失效
RUN sed -i 's/\r$//' /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh \
    && useradd --create-home --uid 1001 appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
