#!/bin/bash

while true; do
    DATE=$(date +%F_%H-%M-%S);
    BACKUP_FILE=/backups/backups/db_backup_${DATE}.sql.zstd;
    echo "[INFO] Starting backup at ${DATE}";
    pg_dump -h database -U "${POSTGRES_USER}" -w -d "${POSTGRES_DB}" -Z zstd -f "${BACKUP_FILE}";
    echo "[INFO] Backup complete: ${BACKUP_FILE}";

    # Keep only last 7 backups
    echo "[INFO] Cleaning up backups older than 7 days. Listed below, if any:";
    find /backups -type f -name 'db_backup_*.sql.zstd' -mtime +7 -print -delete;
    echo "[INFO] Cleanup complete. Sleeping for 24h...";
    echo "";
    echo "";
    sleep 86400;
done
