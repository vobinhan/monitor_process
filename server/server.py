import socketserver
import threading
import json
from flask import Flask, render_template, request
import os

CLIENT_DB = "clients.json"
PORT = 8000

app = Flask(__name__)
clients_data = {}

def load_clients():
    if not os.path.exists(CLIENT_DB):
        with open(CLIENT_DB, 'w') as f:
            json.dump({"clients": {}}, f)
    with open(CLIENT_DB) as f:
        return json.load(f)

def validate_client(client_id, password, db):
    return client_id in db["clients"] and db["clients"][client_id]["password"] == password

class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        while True:
            try:
                data = self.request.recv(4096).decode("utf-8")
                if not data:
                    break
                msg = json.loads(data)
                db = load_clients()
                client_id = msg["client_id"]
                print(client_id)
                password = msg["password"]
                if not validate_client(client_id, password, db):
                    print(f"Auth failed for {client_id}")
                    continue

                clients_data[client_id] = msg["processes"]
                print(f"Received from {client_id}")
            except Exception as e:
                print(f"Error: {e}")
                break

def run_tcp_server():
    server = socketserver.ThreadingTCPServer(("0.0.0.0", PORT), TCPHandler)
    print(f"TCP Server listening on port {PORT}")
    server.serve_forever()

@app.route("/")
def index():
    return render_template("index.html", clients=clients_data)

if __name__ == "__main__":
    threading.Thread(target=run_tcp_server, daemon=True).start()
    app.run(port=5000)

