#!/bin/sh
set -e

mc alias set local http://minio:9000 minioadmin minioadmin

mc mb --ignore-existing local/f1-raw

echo "MinIO bucket f1-raw ready"
