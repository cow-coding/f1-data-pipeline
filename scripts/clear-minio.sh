mc alias set local http://minio:9000 minioadmin minioadmin && \
mc rm --recursive --force local/f1-raw && \
echo "f1-raw bucket cleared"
