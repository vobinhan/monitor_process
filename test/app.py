import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO
import time
import random
import threading
app = Flask(__name__)
socketio = SocketIO(app)


# kill 
connected_clients = {}

@app.route("/")
def index():
    return render_template("index.html")

# Fake process generator
def generate_fake_processes(client_id):
    processes = []
    for i in range(1, random.randint(3, 6)):
        processes.append({
            'pid': str(random.randint(1000, 9999)),
            'name': random.choice(['python', 'java', 'node', 'bash', 'nginx']),
            'cpu': round(random.uniform(0.0, 10.0), 2),
            'memory_mb': round(random.uniform(1.0, 100.0), 1)
        })
    return {
        'client_id': client_id,
        'processes': processes
    }


def broadcast_fake_data():
    while True:
        for client_id in ['client1', 'client2', 'client3']:
            connected_clients[client_id] = time.time()  # update last seen
            socketio.emit('process_data', generate_fake_processes(client_id))
        socketio.emit('status_update', get_client_statuses())
        time.sleep(5)

def get_client_statuses():
    now = time.time()
    return {
        client_id: "online" if now - last_seen < 10 else "offline"
        for client_id, last_seen in connected_clients.items()
    }

# Handle kill command (simulated)
@socketio.on('kill_process')
def kill_process(data):
    client_id = data.get('client_id')
    pid = data.get('pid')
    print(f"Kill command: Client={client_id}, PID={pid}")
    socketio.emit('kill_result', {'client_id': client_id, 'pid': pid, 'result': 'success'}, broadcast=True)


# Bắt đầu luồng nền
socketio.start_background_task(broadcast_fake_data)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=1000, debug=False, use_reloader=False)
