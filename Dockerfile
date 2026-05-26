# Stage 1: Build
FROM python:3.11-slim as builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*
COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim as runner
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*
COPY --from=builder /root/.local /root/.local

# Copy the API codebase, workers, skills, and design-systems
COPY apps/api/ /app/
COPY apps/workers/ /app/apps/workers/
COPY skills/ /app/skills/
COPY design-systems/ /app/design-systems/

# Ensure apps and apps/workers are treated as valid packages
RUN mkdir -p /app/apps && touch /app/apps/__init__.py && touch /app/apps/workers/__init__.py

ENV PYTHONPATH=/app
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "helix.main:app", "--host", "0.0.0.0", "--port", "8000"]
