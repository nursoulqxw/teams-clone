FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements/prod.txt requirements/prod.txt
RUN pip install --no-cache-dir -r requirements/prod.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 7777

CMD ["daphne", "-b", "0.0.0.0", "-p", "7777", "settings.asgi:application"]