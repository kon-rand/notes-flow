#!/bin/bash
# Daily backup script for tasks and archive

cd /app

# Run backup
python3 scripts/backup_data.py

# Clean up old backups (keep 30 days)
find /app/backup -type d -name "20*" -mtime +30 -exec rm -rf {} + 2>/dev/null || true

echo "Backup completed at $(date)"
