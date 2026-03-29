from flask import Flask, jsonify, render_template_string
import psutil
import time
import math
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>VCC Assignment 3 - Auto-Scale Demo</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }
        .metric { background: #f4f4f4; padding: 15px; margin: 10px 0; border-radius: 8px; }
        .metric h3 { margin: 0 0 8px 0; }
        .bar { height: 20px; border-radius: 4px; background: #e0e0e0; }
        .bar-fill { height: 100%; border-radius: 4px; transition: width 0.3s; }
        .ok { background: #4caf50; }
        .warn { background: #ff9800; }
        .critical { background: #f44336; }
        button { padding: 10px 20px; margin: 5px; cursor: pointer; border: none; border-radius: 4px; color: white; }
        .btn-cpu { background: #2196f3; }
        .btn-mem { background: #9c27b0; }
        .btn-stop { background: #f44336; }
        #status { margin-top: 20px; padding: 15px; border-radius: 8px; display: none; }
    </style>
</head>
<body>
    <h1>VCC Assignment 3 - Auto-Scale Demo</h1>
    <p>Local VM Resource Monitor with Cloud Auto-Scaling</p>

    <div class="metric">
        <h3>CPU Usage: <span id="cpu">-</span>%</h3>
        <div class="bar"><div class="bar-fill" id="cpu-bar" style="width:0%"></div></div>
    </div>
    <div class="metric">
        <h3>Memory Usage: <span id="mem">-</span>%</h3>
        <div class="bar"><div class="bar-fill" id="mem-bar" style="width:0%"></div></div>
    </div>
    <div class="metric">
        <h3>Disk Usage: <span id="disk">-</span>%</h3>
        <div class="bar"><div class="bar-fill" id="disk-bar" style="width:0%"></div></div>
    </div>

    <h2>Stress Test Controls</h2>
    <button class="btn-cpu" onclick="stress('cpu')">Generate CPU Load</button>
    <button class="btn-mem" onclick="stress('memory')">Generate Memory Load</button>
    <button class="btn-stop" onclick="stress('stop')">Stop Stress Test</button>

    <div id="status"></div>

    <script>
        function updateMetrics() {
            fetch('/api/metrics').then(r => r.json()).then(data => {
                document.getElementById('cpu').textContent = data.cpu_percent;
                document.getElementById('mem').textContent = data.memory_percent;
                document.getElementById('disk').textContent = data.disk_percent;
                updateBar('cpu-bar', data.cpu_percent);
                updateBar('mem-bar', data.memory_percent);
                updateBar('disk-bar', data.disk_percent);
            });
        }

        function updateBar(id, value) {
            const bar = document.getElementById(id);
            bar.style.width = value + '%';
            bar.className = 'bar-fill ' + (value > 75 ? 'critical' : value > 50 ? 'warn' : 'ok');
        }

        function stress(type) {
            const status = document.getElementById('status');
            status.style.display = 'block';
            status.style.background = '#fff3e0';
            status.textContent = 'Running ' + type + ' stress test...';
            fetch('/api/stress/' + type).then(r => r.json()).then(data => {
                status.textContent = data.message;
                status.style.background = type === 'stop' ? '#e8f5e9' : '#fff3e0';
            });
        }

        setInterval(updateMetrics, 2000);
        updateMetrics();
    </script>
</body>
</html>
"""

stress_running = False
stress_memory = []


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/metrics')
def metrics():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    return jsonify({
        'cpu_percent': cpu,
        'memory_percent': memory.percent,
        'memory_used_gb': round(memory.used / (1024**3), 2),
        'memory_total_gb': round(memory.total / (1024**3), 2),
        'disk_percent': disk.percent,
        'disk_used_gb': round(disk.used / (1024**3), 2),
        'disk_total_gb': round(disk.total / (1024**3), 2),
        'hostname': os.uname().nodename,
        'timestamp': time.time()
    })


@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'hostname': os.uname().nodename})


@app.route('/api/stress/<stress_type>')
def stress_test(stress_type):
    global stress_running, stress_memory

    if stress_type == 'cpu':
        stress_running = True
        start = time.time()
        while time.time() - start < 30 and stress_running:
            [math.sqrt(i**2 + i) for i in range(100000)]
        return jsonify({'message': 'CPU stress test completed (30s burst)'})

    elif stress_type == 'memory':
        stress_memory = [bytearray(1024 * 1024) for _ in range(200)]
        return jsonify({'message': 'Allocated 200MB of memory. Use stop to release.'})

    elif stress_type == 'stop':
        stress_running = False
        stress_memory = []
        return jsonify({'message': 'Stress tests stopped, memory released.'})

    return jsonify({'message': 'Unknown stress type. Use: cpu, memory, stop'}), 400


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
