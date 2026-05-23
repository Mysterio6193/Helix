FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

WORKDIR /app

# Reuse the API codebase (worker shares helix/)
COPY apps/api/pyproject.toml /app/pyproject.toml
RUN pip install --upgrade pip && pip install hatchling && pip install -e /app

COPY apps/api/helix /app/helix
COPY apps/workers/run_worker.py /app/run_worker.py
COPY skills /app/skills
COPY design-systems /app/design-systems

CMD ["python", "-u", "run_worker.py"]
