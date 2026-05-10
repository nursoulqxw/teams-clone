FROM python:3.12-slim

ENV PYTHONUMBUFFERED=1

WORKDIR /app

COPY requirements/prod.txt requirements/prod.txt
RUN pip install --no--cache-dir -r requirements/prod.txt

COPY . .

