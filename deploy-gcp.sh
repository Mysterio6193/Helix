#!/usr/bin/env bash
set -e

echo "🚀 Starting Helix OS GCP Deployment"
PROJECT_ID=$(gcloud config get-value project)
echo "📦 Project ID: $PROJECT_ID"
REGION="us-central1"

echo "1️⃣ Enabling GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com

echo "2️⃣ Provisioning Cloud SQL Postgres 16 (this might take 10 minutes)..."
gcloud sql instances create helix-postgres \
  --database-version=POSTGRES_16 \
  --tier=db-custom-2-7680 \
  --region=$REGION \
  --storage-type=SSD \
  --storage-size=20GB || echo "Instance helix-postgres already exists"

DB_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
echo "Setting Postgres password..."
gcloud sql users set-password postgres \
  --instance=helix-postgres \
  --password="$DB_PASSWORD"

echo "Creating helix database..."
gcloud sql databases create helix --instance=helix-postgres || echo "Database helix already exists"

SQL_IP=$(gcloud sql instances describe helix-postgres --format="value(ipAddresses[0].ipAddress)")
echo "✅ Cloud SQL IP: $SQL_IP"

echo "3️⃣ Provisioning Redis Memorystore..."
gcloud redis instances create helix-redis \
  --size=1 \
  --region=$REGION \
  --redis-version=redis_7_0 || echo "Redis instance already exists"

REDIS_IP=$(gcloud redis instances describe helix-redis --region=$REGION --format="value(host)")
echo "✅ Redis IP: $REDIS_IP"

echo "4️⃣ Provisioning Cloud Storage..."
gsutil mb -c standard -l $REGION gs://$PROJECT_ID-assets-bucket || echo "Bucket already exists"
gsutil uniformbucketlevelaccess set on gs://$PROJECT_ID-assets-bucket

cat << 'EOF' > cors-json.json
[
  {
    "origin": ["*"],
    "method": ["GET", "PUT", "POST", "HEAD"],
    "responseHeader": ["Content-Type", "Content-MD5", "x-goog-meta-filename"],
    "maxAgeSeconds": 3600
  }
]
EOF
gsutil cors set cors-json.json gs://$PROJECT_ID-assets-bucket

echo "5️⃣ Building Docker Image..."
gcloud artifacts repositories create helix-repo \
  --repository-format=docker \
  --location=$REGION \
  --description="Helix OS Docker Repository" || echo "Artifact repo already exists"

IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/helix-repo/helix-backend:latest"
gcloud builds submit --tag $IMAGE .

echo "6️⃣ Deploying Services to Cloud Run..."

DB_URL="postgresql+asyncpg://postgres:${DB_PASSWORD}@${SQL_IP}/helix"
REDIS_URL="redis://${REDIS_IP}:6379/0"

gcloud run deploy helix-api \
  --image=$IMAGE \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --port=8000 \
  --cpu=2 \
  --memory=2Gi \
  --concurrency=80 \
  --timeout=3600 \
  --set-env-vars="HELIX_ENV=production,DATABASE_URL=${DB_URL},REDIS_URL=${REDIS_URL}"

gcloud run deploy helix-worker \
  --image=$IMAGE \
  --platform=managed \
  --region=$REGION \
  --no-allow-unauthenticated \
  --min-instances=1 \
  --command="python" \
  --args="-m,apps.workers.run_worker" \
  --set-env-vars="HELIX_ENV=production,DATABASE_URL=${DB_URL},REDIS_URL=${REDIS_URL}"

gcloud run deploy helix-scheduler \
  --image=$IMAGE \
  --platform=managed \
  --region=$REGION \
  --no-allow-unauthenticated \
  --min-instances=1 \
  --command="celery" \
  --args="-A,helix.services.scheduler,beat,--loglevel=info" \
  --set-env-vars="HELIX_ENV=production,DATABASE_URL=${DB_URL},REDIS_URL=${REDIS_URL}"

echo "🎉 Deployment Script Finished! Check the outputs for your API Gateway URL."
