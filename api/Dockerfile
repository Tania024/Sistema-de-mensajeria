FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev

COPY requerimientos.txt .
RUN pip install --no-cache-dir -r requerimientos.txt

COPY . .

CMD ["python", "app.py"]
