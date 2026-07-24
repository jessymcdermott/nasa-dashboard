# Intentionally outdated base image — Debian Buster is EOL and python:3.9
# is past its prime support window. Good target for container/image scanning
# (OS package CVEs) on top of the already-vulnerable requirements.txt.
FROM python:3.9-slim-buster

# Buster is EOL and pulled from the live Debian mirrors — point at the archive.
# Pin linux-libc-dev to an old Buster build (pre-dates later kernel security
# updates) so kernel-layer CVEs show up in container/image scans.
RUN printf 'deb http://archive.debian.org/debian buster main\ndeb http://archive.debian.org/debian-security buster/updates main\n' > /etc/apt/sources.list \
    && apt-get -o Acquire::Check-Valid-Until=false update \
    && apt-get install -y --no-install-recommends linux-libc-dev=4.19.249-2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
