import socket
import json
import threading
from config import HOST, PORT, MAX_CONNECTIONS, BUFFER_SIZE
from auth.authenticator import Authenticator
from core.process_db import ProcessDB
from utils.logger import log
import time

class TCPServer:
    def __init__(self, socketio, on_update=None):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.auth = Authenticator()
        self.process_db = ProcessDB()
        self.active_clients = {}
        self.on_update = on_update
        self.client_sockets = {}
        self.socketio = socketio
        self._buffer = {}

    def start(self):
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(MAX_CONNECTIONS)
        log(f"Server started on {HOST}:{PORT}")
        
        while True:
            client_socket, addr = self.server_socket.accept()
            threading.Thread(
                target=self.handle_client,
                args=(client_socket, addr),
                daemon=True
            ).start()

    def handle_client(self, client_socket: socket.socket, addr: tuple):
        client_id = None
        authenticated = False
        
        try:
            auth_data = client_socket.recv(BUFFER_SIZE).decode()
            auth = json.loads(auth_data)
            client_id = auth.get("client_id")
            password = auth.get("password")

            if not client_id or not password:
                client_socket.send(b"AUTH_FAIL\n")
                return

            now = time.time()
            if client_id in self.client_sockets and now - self.active_clients.get(client_id, 0) < 10:
                log(f"Client '{client_id}' already connected - rejecting")
                client_socket.send(b"AUTH_FAIL_DUPLICATE_ID\n")
                return

            if not self.auth.validate(client_id, password):
                client_socket.send(b"AUTH_FAIL\n")
                return

            self.client_sockets[client_id] = client_socket
            self.active_clients[client_id] = time.time()
            client_socket.send(b"AUTH_SUCCESS\n")
            authenticated = True
            
            self.socketio.emit("status_update", {client_id: "online"})
            self.socketio.emit("process_data", {"client_id": client_id, "processes": []})
            
            if client_id in self.process_db.db:
                self.socketio.emit("process_data", {
                    "client_id": client_id,
                    "processes": self.process_db.db[client_id]
                })

            while True:
                data = client_socket.recv(BUFFER_SIZE).decode()
                if not data:
                    break

                if data.startswith('{"kill_result":'):
                    result = json.loads(data)
                    self.socketio.emit('kill_result', {'kill_result': result})
                else:
                    self._process_data(addr, data)

        except (ConnectionResetError, json.JSONDecodeError) as e:
            log(f"Client error: {e}")

        finally:
            if authenticated and client_id:
                self.client_sockets.pop(client_id, None)
                self.active_clients.pop(client_id, None)
                self.process_db.db.pop(client_id, None)

                self.socketio.emit("process_data", {
                    "client_id": client_id,
                    "processes": []
                })

                self.socketio.emit("status_update", {
                    client_id: "offline"
                })

            client_socket.close()

    def send_command_to_client(self, client_id, command_str):
        sock = self.client_sockets.get(client_id)
        if sock:
            try:
                sock.sendall((command_str + '\n').encode())
            except Exception as e:
                log(f"Error sending command: {e}", level="ERROR")

    def _process_data(self, addr: tuple, data: str):
        self._buffer.setdefault(addr, "")
        self._buffer[addr] += data

        while '\n' in self._buffer[addr]:
            line, self._buffer[addr] = self._buffer[addr].split('\n', 1)
            try:
                process_data = json.loads(line)
                self.process_db.update(process_data["client_id"], process_data["processes"])
                self.active_clients[process_data["client_id"]] = time.time()

                if self.on_update:
                    self.on_update(process_data)
            except json.JSONDecodeError as e:
                log(f"Invalid JSON data: {repr(line)}", level="WARNING")
