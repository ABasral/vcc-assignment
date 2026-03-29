#!/bin/bash
# ============================================================
# VCC Assignment 3 - Cleanup GCP Resources
# Removes auto-scaled instances and firewall rules
# ============================================================

set -e

# Load config
if [ -f config/gcp_config.env ]; then
    export $(grep -v '^#' config/gcp_config.env | xargs)
fi

PROJECT=${GCP_PROJECT:-your-gcp-project-id}
ZONE=${GCP_ZONE:-us-central1-a}
INSTANCE=${GCP_INSTANCE_NAME:-autoscaled-vm}

echo "=========================================="
echo " Cleaning Up GCP Resources"
echo "=========================================="
echo "Project: $PROJECT"
echo "Zone: $ZONE"
echo ""

# Delete the auto-scaled instance
echo "[1/2] Deleting instance: $INSTANCE"
gcloud compute instances delete "$INSTANCE" \
    --project "$PROJECT" \
    --zone "$ZONE" \
    --quiet 2>/dev/null && echo "Instance deleted." || echo "Instance not found or already deleted."

# Delete firewall rule
echo "[2/2] Deleting firewall rule: allow-flask-5000"
gcloud compute firewall-rules delete allow-flask-5000 \
    --project "$PROJECT" \
    --quiet 2>/dev/null && echo "Firewall rule deleted." || echo "Firewall rule not found."

echo ""
echo "Cleanup complete."
