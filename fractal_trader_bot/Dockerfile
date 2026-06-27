FROM python:3.12-slim
WORKDIR /app
COPY src/ src/
COPY risk_config.json ./
RUN pip install --no-cache-dir -r src/requirements.txt || pip install --no-cache-dir requests pandas numpy ccxt
CMD ["python", "src/bx_orchestrator.py"]
