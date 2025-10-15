#!/bin/bash

# Database backup script for PakJobs Aggregator
# Creates daily backups with rotation (keep last 7 days)

# Load environment variables
if [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Create backups directory
BACKUP_DIR="../backups"
mkdir -p $BACKUP_DIR

# Generate backup filename with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/pakjobs_backup_$TIMESTAMP.sql"

echo "Starting database backup..."
echo "Backup file: $BACKUP_FILE"

# Run pg_dump
pg_dump $DATABASE_URL > $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "✅ Backup completed successfully"
    
    # Compress backup
    gzip $BACKUP_FILE
    echo "✅ Backup compressed: ${BACKUP_FILE}.gz"
    
    # Delete backups older than 7 days
    find $BACKUP_DIR -name "pakjobs_backup_*.sql.gz" -mtime +7 -delete
    echo "✅ Old backups cleaned up"
    
    # Show backup size
    du -h ${BACKUP_FILE}.gz
else
    echo "❌ Backup failed"
    exit 1
fi
