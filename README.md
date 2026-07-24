# 🛰 NASA Space Dashboard

A Flask web app pulling live data from 4 NASA APIs — built as a Black Duck Code Sight test project.

## APIs Used

| Panel | API | Endpoint |
|---|---|---|
| Picture of the Day | NASA APOD | `api.nasa.gov/planetary/apod` |
| Mars Rover Photos | NASA Mars Photos | `api.nasa.gov/mars-photos/api/v1/...` |
| Near Earth Objects | NASA NeoWs | `api.nasa.gov/neo/rest/v1/feed` |
| ISS Location | Open Notify | `api.open-notify.org/iss-now.json` |

## Setup

**1. Clone / open in VS Code**

**2. Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set your NASA API key**
```bash
cp .env.example .env
# Edit .env and replace DEMO_KEY with your key from https://api.nasa.gov/
```
> Without a key it still works — DEMO_KEY is rate-limited to 30 req/hour.

**5. Run**
```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000)

---

## For Black Duck Code Sight Testing

This project is intentionally structured to exercise SAST, SCA, Container, IaC, and API scanning:

- **SCA targets**: `requirements.txt` uses older pinned versions of Flask, Werkzeug, urllib3, Jinja2, certifi, PyYAML, Pillow, cryptography, gunicorn, and lxml — these should surface known CVEs, most with fixes available. `package/package.json` similarly pins vulnerable versions of lodash, axios, minimist, and node-fetch.
- **SAST surface**: HTTP calls with user-supplied query params passed to external APIs, no input sanitization; see `src/vulnerable/` for standalone SQL injection, command injection, insecure deserialization, path traversal, weak crypto, and XXE examples
- **Container target**: `Dockerfile` builds on `python:3.9-slim-buster` (EOL Debian Buster base) and pins an old `linux-libc-dev` build alongside the vulnerable `requirements.txt` — good for exercising image/container scanning against OS-layer, kernel-layer, and language-layer CVEs. Build with `docker build -t nasa-dashboard .`
- **IaC target**: `k8s/` is a Helm chart (Black Duck Detect's Kubernetes detector keys off `Chart.yaml`; plain manifests without one aren't picked up) with intentional misconfigurations — `hostNetwork`, a `hostPath` mount of `/`, a `privileged` container running as root with `SYS_ADMIN`, a hardcoded API key, `automountServiceAccountToken: true`, and a mutable `:latest` image tag. `helm template nasa-dashboard k8s/ | trivy config -` turns up 24 findings (6 HIGH) out of the box.
- **API target**: `api/openapi.yml` describes the Flask API surface for API scanning
- **Dependencies to watch**: `requests==2.25.1`, `urllib3==1.26.5`, `PyYAML==5.3.1`, `Pillow==8.1.0`, `cryptography==3.3.1`, `gunicorn==20.0.4`, `lxml==4.6.2`
