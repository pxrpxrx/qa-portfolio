FROM python:3.14-slim
WORKDIR /app
COPY src/ src/
COPY risk_config.json ./
RUN pip install requests websocket-client
CMD ["python", "src/bx_trail_traider.py"]
