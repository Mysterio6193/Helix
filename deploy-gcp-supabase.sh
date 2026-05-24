#!/usr/bin/env bash
set -e

echo "🚀 Starting Helix OS GCP + Supabase Hybrid Deployment"

# Check if gcloud CLI is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
  echo "❌ Error: You are not logged into the Google Cloud SDK. Please run 'gcloud auth login' and try again."
  exit 1
fi

PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
  echo "❌ Error: No Google Cloud project is currently selected. Please run 'gcloud config set project <PROJECT_ID>' first."
  exit 1
fi

echo "📦 Selected GCP Project: $PROJECT_ID"
REGION="us-central1"

# Step 1: Read or Prompt for Supabase Database URL
if [ -z "$DATABASE_URL" ]; then
  echo "🔑 Supabase Database Integration Required"
  echo "Note: The URL must use the asyncpg schema: 'postgresql+asyncpg://<user>:<password>@<host>/<dbname>'"
  read -p "Enter your Supabase asyncpg DATABASE_URL: " INPUT_DB_URL
  if [ -z "$INPUT_DB_URL" ]; then
    echo "❌ Error: DATABASE_URL cannot be empty."
    exit 1
  fi
  DB_URL="$INPUT_DB_URL"
else
  echo "✅ Using DATABASE_URL from environment variables."
  DB_URL="$DATABASE_URL"
fi

# Ensure asyncpg is specified
if [[ ! "$DB_URL" =~ \+asyncpg ]]; then
  echo "⚠️ Warning: Your database connection string does not contain '+asyncpg'. FastAPI requires this for async SQLAlchemy."
  echo "Converting connection string schema to postgresql+asyncpg..."
  # Replace postgresql:// or postgres:// with postgresql+asyncpg://
  DB_URL=$(echo "$DB_URL" | sed -E 's/^postgres(ql)?:\/\//postgresql+asyncpg:\/\//')
  echo "New Connection String: $DB_URL"
fi

echo "1️⃣ Enabling GCP APIs (excluding Cloud SQL)..."
gcloud services enable \
  run.googleapis.com \
  redis.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com

echo "2️⃣ Provisioning Redis Memorystore (for queue & cache)..."
gcloud redis instances create helix-redis \
  --size=1 \
  --region=$REGION \
  --redis-version=redis_7_0 || echo "Redis instance already exists"

REDIS_IP=$(gcloud redis instances describe helix-redis --region=$REGION --format="value(host)")
echo "✅ Redis IP: $REDIS_IP"
REDIS_URL="redis://${REDIS_IP}:6379/0"

echo "3️⃣ Provisioning Cloud Storage bucket..."
gsutil mb -c standard -l $REGION gs://$PROJECT_ID-assets-bucket || echo "Bucket already exists"
gsutil uniformbucketlevelaccess set on gs://$PROJECT_ID-assets-bucket

# Create CORS configuration
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
rm -f cors-json.json

echo "4️⃣ Building Docker Image via Cloud Build..."
gcloud artifacts repositories create helix-repo \
  --repository-format=docker \
  --location=$REGION \
  --description="Helix OS Docker Repository" || echo "Artifact repo already exists"

IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/helix-repo/helix-backend:latest"
gcloud builds submit --tag $IMAGE .

echo "5️⃣ Deploying Backend Services to Cloud Run..."

# Deploy FastAPI API Gateway
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

# Deploy Celery Worker
gcloud run deploy helix-worker \
  --image=$IMAGE \
  --platform=managed \
  --region=$REGION \
  --no-allow-unauthenticated \
  --min-instances=1 \
  --command="python" \
  --args="-m,apps.workers.run_worker" \
  --set-env-vars="HELIX_ENV=production,DATABASE_URL=${DB_URL},REDIS_URL=${REDIS_URL}"

# Deploy Celery Beat Scheduler
gcloud run deploy helix-scheduler \
  --image=$IMAGE \
  --platform=managed \
  --region=$REGION \
  --no-allow-unauthenticated \
  --min-instances=1 \
  --command="celery" \
  --args="-A,helix.services.scheduler,beat,--loglevel=info" \
  --set-env-vars="HELIX_ENV=production,DATABASE_URL=${DB_URL},REDIS_URL=${REDIS_URL}"

echo "🎉 Hybrid GCP + Supabase Deployment Finished Successfully!"
echo "--------------------------------------------------------"
echo "👉 Check the Cloud Run console for your live API url."
echo "👉 Use your live API URL to configure NEXT_PUBLIC_API_BASE on Vercel."
