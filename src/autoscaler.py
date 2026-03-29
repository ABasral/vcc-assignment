import subprocess
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

GCP_PROJECT = os.environ.get("GCP_PROJECT", "vcc-assignment-488908")
GCP_ZONE = os.environ.get("GCP_ZONE", "us-central1-a")


class AutoScaler:

    def __init__(self):
        self.scaled_instances = []
        self.scale_history = []

    def scale_up(self, instance_name, machine_type="e2-medium"):
        logger.info(f"Scaling UP: Creating {instance_name}")

        cmd = [
            "gcloud", "compute", "instances", "create", instance_name,
            "--project", GCP_PROJECT,
            "--zone", GCP_ZONE,
            "--machine-type", machine_type,
            "--image-family", "ubuntu-2204-lts",
            "--image-project", "ubuntu-os-cloud",
            "--metadata", f"startup-script={self._startup_script()}",
            "--tags", "http-server",
            "--format", "json",
            "--quiet"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                ip = self._get_ip(instance_name)
                record = {
                    'name': instance_name,
                    'created_at': datetime.now().isoformat(),
                    'machine_type': machine_type,
                    'ip': ip,
                    'status': 'running'
                }
                self.scaled_instances.append(record)
                self.scale_history.append({
                    'action': 'scale_up',
                    'instance': instance_name,
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"Instance {instance_name} created at {ip}")
                return True, record
            else:
                logger.error(f"Scale up failed: {result.stderr}")
                return False, result.stderr
        except FileNotFoundError:
            logger.error("gcloud CLI not installed")
            return False, "gcloud not found"
        except subprocess.TimeoutExpired:
            logger.error("Timed out creating instance")
            return False, "Timeout"

    def scale_down(self, instance_name):
        logger.info(f"Scaling DOWN: Deleting {instance_name}")

        cmd = [
            "gcloud", "compute", "instances", "delete", instance_name,
            "--project", GCP_PROJECT,
            "--zone", GCP_ZONE,
            "--quiet"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                self.scaled_instances = [
                    i for i in self.scaled_instances if i['name'] != instance_name
                ]
                self.scale_history.append({
                    'action': 'scale_down',
                    'instance': instance_name,
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"{instance_name} deleted")
                return True
            else:
                logger.error(f"Scale down failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Scale down error: {e}")
            return False

    def _get_ip(self, instance_name):
        cmd = [
            "gcloud", "compute", "instances", "describe", instance_name,
            "--project", GCP_PROJECT,
            "--zone", GCP_ZONE,
            "--format", "json"
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                info = json.loads(result.stdout)
                interfaces = info.get('networkInterfaces', [])
                if interfaces:
                    access = interfaces[0].get('accessConfigs', [])
                    if access:
                        return access[0].get('natIP', 'N/A')
        except Exception:
            pass
        return 'N/A'

    def _startup_script(self):
        return """#!/bin/bash
set -e
apt-get update -y
apt-get install -y python3-pip python3-venv
python3 -m venv /opt/app/venv
source /opt/app/venv/bin/activate
pip install flask psutil gunicorn
mkdir -p /opt/app
cat > /opt/app/health.py << 'PYEOF'
from flask import Flask, jsonify
import psutil, os
app = Flask(__name__)
@app.route('/health')
def health():
    return jsonify({"status": "healthy", "host": os.uname().nodename,
                    "cpu": psutil.cpu_percent(), "memory": psutil.virtual_memory().percent})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
PYEOF
cd /opt/app && source venv/bin/activate
gunicorn -w 2 -b 0.0.0.0:5000 health:app --daemon
"""

    def get_status(self):
        return {
            'active_instances': len(self.scaled_instances),
            'instances': self.scaled_instances,
            'history': self.scale_history[-10:]
        }
