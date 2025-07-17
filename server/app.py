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

# Callback to receive process_data from TCPServer
def handle_process_data(process_data):
    socketio.emit("process_data", {
        "client_id": process_data["client_id"],
        "processes": process_data["processes"]
    })

    # Update status for all clients, both active and inactive
    now = time.time()
    statuses = {
        client_id: "online" if now - last_seen < 10 else "offline"
        for client_id, last_seen in server.active_clients.items()
    }

    # If client disconnects => remove process_data
    for client_id, status in statuses.items():
        if status == "offline":
            server.process_db.db.pop(client_id, None)

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
    print("---------[DEBUG] Sending kill command to client", client_id, ":", repr(command_str))
    server.send_command_to_client(client_id, command_str)

if __name__ == "__main__":

    # Pass callback to TCPServer
    server = TCPServer(socketio=socketio, on_update=handle_process_data)
    
    # Run TCP server in a separate thread
    threading.Thread(target=server.start, daemon=True).start()
    threading.Thread(target=server.cleanup_inactive_clients, daemon=True).start()

    # Chạy web UI
    socketio.run(app, host="0.0.0.0", port=5000)
