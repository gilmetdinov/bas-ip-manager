FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

ENV PATH="/opt/venv/bin:$PATH"

COPY src /app/src
COPY server.py /app/

CMD ["python", "server.py"]
