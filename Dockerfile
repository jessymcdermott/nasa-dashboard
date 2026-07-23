# Intentionally outdated base image — Debian Buster is EOL and python:3.9
# is past its prime support window. Good target for container/image scanning
# (OS package CVEs) on top of the already-vulnerable requirements.txt.
FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
