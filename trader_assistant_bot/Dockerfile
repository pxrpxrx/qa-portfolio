FROM python:3.12-slim
WORKDIR /app

# Install system dependencies for TA-Lib
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib C library
RUN wget -q http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

COPY src/ src/
COPY risk_config.json ./
RUN pip install --no-cache-dir -r src/requirements.txt
CMD ["python", "src/bx_trail_traider.py"]
