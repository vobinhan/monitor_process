from flask import Flask, render_template
from flask_socketio import SocketIO
from core.tcp_server import TCPServer
import threading
import time
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


@app.route("/")
def index():
    return render_template("index.html")

# Callback nhận process_data từ TCPServer
def handle_process_data(process_data):
    socketio.emit("process_data", {
        "client_id": process_data["client_id"],
        "processes": process_data["processes"]
    })
    statuses = {
        client_id: "online" if time.time() - last_seen < 10 else "offline"
        for client_id, last_seen in server.active_clients.items()
    }
    socketio.emit("status_update", statuses)


@socketio.on('kill_process')
def handle_kill_process(data):
    client_id = data.get('client_id')
    pid = data.get('pid')
    if client_id and pid:
        msg = json.dumps({
            "type": "kill",
            "client_id": client_id,
            "pid": pid
        })
        server.send_to_client(client_id, msg)

if __name__ == "__main__":
    # Truyền callback cho TCPServer
    server = TCPServer(on_update=handle_process_data)
    
    # Chạy server TCP trên luồng riêng
    threading.Thread(target=server.start, daemon=True).start()

    # Chạy web UI
    socketio.run(app, host="0.0.0.0", port=5000)
