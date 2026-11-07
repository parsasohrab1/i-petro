FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY server/requirements.txt server/requirements.txt
RUN pip install -r server/requirements.txt
COPY server server
COPY platform/index.html platform/index.html
ENV PLATFORM_HTML=/app/platform/index.html
RUN useradd -r -u 10001 app && chown -R app /app
USER app
EXPOSE 8000
# one worker on purpose: live updates are fanned out in-process
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*"]
