from flask import Flask, render_template
from flask_socketio import SocketIO
from core.tcp_server import TCPServer
import threading
import time
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
server = None

@app.route("/")
def index():
    return render_template("index.html")

# Callback to receive process data from TCPServer
def handle_process_data(process_data):
    client_id = process_data["client_id"]
    processes = process_data["processes"]

    socketio.emit("process_data", {
        "client_id": client_id,
        "processes": processes
    })

    now = time.time()
    server.active_clients[client_id] = now
    server.process_db.update(client_id, processes)

    statuses = {
        cid: "online" if cid in server.active_clients else "offline"
        for cid in set(server.client_sockets.keys()).union(server.process_db.db.keys())
    }

    socketio.emit("status_update", statuses)

@socketio.on('kill_process')
def handle_kill_process(data):
    client_id = data['client_id']
    pid = data['pid']
    command = {
        "type": "kill",
        "pid": pid
    }
    command_str = json.dumps(command) + '\n'
    print("[DEBUG] Sending kill command to", client_id, ":", repr(command_str))
    server.send_command_to_client(client_id, command_str)

@socketio.on("request_full_state")
def handle_request_full_state():
    print("[SYNC] UI requested full state")

    statuses = {
        cid: "online" if cid in server.active_clients else "offline"
        for cid in set(server.client_sockets.keys()).union(server.process_db.db.keys())
    }
    socketio.emit("status_update", statuses)

    for client_id, processes in server.process_db.db.items():
        socketio.emit("process_data", {
            "client_id": client_id,
            "processes": processes
        })

if __name__ == "__main__":
    server = TCPServer(socketio=socketio, on_update=handle_process_data)
    threading.Thread(target=server.start, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000)
