import psutil
import time
import json
import logging
import subprocess
import sys
import os
from datetime import datetime

THRESHOLD = 75
CHECK_INTERVAL = 10
BREACHES_NEEDED = 3

GCP_PROJECT = os.environ.get("GCP_PROJECT", "vcc-assignment-488908")
GCP_ZONE = os.environ.get("GCP_ZONE", "us-central1-a")
GCP_INSTANCE = os.environ.get("GCP_INSTANCE_NAME", "autoscaled-vm")
GCP_MACHINE = os.environ.get("GCP_MACHINE_TYPE", "e2-medium")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("monitor.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def get_metrics():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    return {
        'timestamp': datetime.now().isoformat(),
        'cpu_percent': cpu,
        'memory_percent': memory.percent,
        'memory_used_mb': round(memory.used / (1024**2)),
        'memory_total_mb': round(memory.total / (1024**2)),
        'disk_percent': disk.percent,
        'disk_used_gb': round(disk.used / (1024**3), 2),
        'disk_total_gb': round(disk.total / (1024**3), 2),
    }


def check_threshold(metrics):
    breaches = []
    if metrics['cpu_percent'] > THRESHOLD:
        breaches.append(f"CPU: {metrics['cpu_percent']}%")
    if metrics['memory_percent'] > THRESHOLD:
        breaches.append(f"Memory: {metrics['memory_percent']}%")
    if metrics['disk_percent'] > THRESHOLD:
        breaches.append(f"Disk: {metrics['disk_percent']}%")
    return breaches


def create_gcp_instance():
    logger.info("=== INITIATING AUTO-SCALE TO GCP ===")

    startup_script = """#!/bin/bash
    apt-get update
    apt-get install -y python3-pip python3-venv git
    python3 -m venv /opt/app/venv
    source /opt/app/venv/bin/activate
    pip install flask psutil gunicorn
    mkdir -p /opt/app
    cd /opt/app
    echo "Cloud VM ready for workload migration"
    """

    cmd = [
        "gcloud", "compute", "instances", "create", GCP_INSTANCE,
        "--project", GCP_PROJECT,
        "--zone", GCP_ZONE,
        "--machine-type", GCP_MACHINE,
        "--image-family", "ubuntu-2204-lts",
        "--image-project", "ubuntu-os-cloud",
        "--metadata", f"startup-script={startup_script}",
        "--tags", "http-server,https-server",
        "--format", "json"
    ]

    logger.info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            instance_info = json.loads(result.stdout)
            logger.info(f"GCP instance created successfully: {GCP_INSTANCE}")
            return True, instance_info
        else:
            logger.error(f"Failed to create GCP instance: {result.stderr}")
            return False, result.stderr
    except FileNotFoundError:
        logger.error("gcloud CLI not found. Install Google Cloud SDK.")
        return False, "gcloud CLI not installed"
    except subprocess.TimeoutExpired:
        logger.error("GCP instance creation timed out")
        return False, "Timeout"


def save_metrics(history):
    with open("metrics.json", 'w') as f:
        json.dump(history, f, indent=2)


def run_monitor():
    logger.info("=" * 50)
    logger.info("Resource Monitor Started")
    logger.info(f"Threshold: {THRESHOLD}% | Interval: {CHECK_INTERVAL}s")
    logger.info(f"GCP Project: {GCP_PROJECT}")
    logger.info("=" * 50)

    consecutive_breaches = 0
    scaled = False
    history = []

    while True:
        metrics = get_metrics()
        history.append(metrics)

        if len(history) > 1000:
            history = history[-1000:]

        save_metrics(history)

        logger.info(
            f"CPU: {metrics['cpu_percent']}% | "
            f"Memory: {metrics['memory_percent']}% | "
            f"Disk: {metrics['disk_percent']}%"
        )

        breaches = check_threshold(metrics)

        if breaches and not scaled:
            consecutive_breaches += 1
            logger.warning(
                f"THRESHOLD BREACH ({consecutive_breaches}/{BREACHES_NEEDED}): "
                f"{', '.join(breaches)}"
            )

            if consecutive_breaches >= BREACHES_NEEDED:
                logger.critical("THRESHOLD EXCEEDED - TRIGGERING AUTO-SCALE")
                success, info = create_gcp_instance()
                if success:
                    scaled = True
                    logger.info("Auto-scaling complete. Cloud VM is running.")
                else:
                    logger.error(f"Auto-scaling failed: {info}")
                    consecutive_breaches = 0
        else:
            if consecutive_breaches > 0 and not scaled:
                logger.info("Usage back to normal. Resetting breach counter.")
            consecutive_breaches = 0

        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    run_monitor()
