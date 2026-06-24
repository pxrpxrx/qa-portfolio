FROM python:3.14-slim
WORKDIR /app
COPY src/ src/
COPY config.json risk_config.json ./
RUN pip install requests
CMD ["python", "src/bx_trader_main.py"]
