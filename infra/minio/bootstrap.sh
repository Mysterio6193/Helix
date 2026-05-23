#!/bin/sh
# Bootstrap the helix-assets bucket on first run.
set -eu

ACCESS=${S3_ACCESS_KEY:-minioadmin}
SECRET=${S3_SECRET_KEY:-minioadmin}
BUCKET=${S3_BUCKET:-helix-assets}

echo "[minio-bootstrap] waiting for minio..."
sleep 2
mc alias set helix http://minio:9000 "$ACCESS" "$SECRET"

if mc ls "helix/$BUCKET" >/dev/null 2>&1; then
  echo "[minio-bootstrap] bucket helix/$BUCKET already exists"
else
  echo "[minio-bootstrap] creating bucket helix/$BUCKET"
  mc mb "helix/$BUCKET"
  mc anonymous set download "helix/$BUCKET"
fi

echo "[minio-bootstrap] done"
