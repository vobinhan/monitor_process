import socket
import json
import threading
from config import HOST, PORT, MAX_CONNECTIONS, BUFFER_SIZE
from auth.authenticator import Authenticator
from core.process_db import ProcessDB
from utils.logger import log
import time

class TCPServer:
    # Khởi tạo socket server, auth, và database
    def __init__(self, socketio, on_update=None):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.auth = Authenticator()
        self.process_db = ProcessDB()
        # web interface
        self._buffer = {}  # Thêm dòng này để khởi tạo biến
        self.active_clients = {}  # Thêm để theo dõi client đang kết nối

        self.on_update = on_update  # lưu callback từ app.py

        self.client_sockets = {}  # client_socket -> client_id
        self.socketio = socketio
        
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
        try:
            # Xác thực
            log(f"Authenticating Client...")
            auth_data = client_socket.recv(BUFFER_SIZE).decode()
            if not self._authenticate(client_socket, auth_data):
                return

            # Nhận process data định kỳ
            while True:
                data = client_socket.recv(BUFFER_SIZE).decode()
                if not data:
                    break
                # Xử lý lệnh kill từ client
                if data.startswith('{"kill_result":'):
                    result = json.loads(data)
                    print(f"[DEBUG] Nhận kill_result từ client: {result}")
                    self.socketio.emit('kill_result', {'kill_result': result})
                else:
                    self._process_data(addr, data)
        except ConnectionResetError:
            log(f"Client {addr} disconnected abruptly", level="ERROR")
        finally:
            client_socket.close()

    def send_command_to_client(self, client_id, command_str):
        sock = self.client_sockets.get(client_id)
        if sock:
            try:
                print(f"------[DEBUG] Sending kill command to client {client_id}: {command_str}")
                sock.sendall((command_str + '\n').encode())
            except Exception as e:
                log(f"Lỗi gửi command: {e}", level="ERROR")

    def _authenticate(self, client_socket: socket.socket, data: str) -> bool:
        try:
            auth = json.loads(data)
            
            if self.auth.validate(auth["client_id"], auth["password"]):

                # Kill
                self.client_sockets[auth["client_id"]] = client_socket

                client_socket.send(b"AUTH_SUCCESS\n")
                print(f'AUTH_SUCCESS')
                return True
        except json.JSONDecodeError:
            pass
        client_socket.send(b"AUTH_FAIL")
        return False
    
    def _process_data(self, addr: tuple, data: str):
        self._buffer.setdefault(addr, "")
        self._buffer[addr] += data  # accumulate data

        while '\n' in self._buffer[addr]:
            line, self._buffer[addr] = self._buffer[addr].split('\n', 1)
            try:
                # print(f"Parsing line from {addr}: {repr(line)}")
                process_data = json.loads(line)
                self.process_db.update(process_data["client_id"], process_data["processes"])
                log(f"Updated processes from {addr}")
                self.active_clients[process_data["client_id"]] = time.time()
                print(self.active_clients[process_data["client_id"]])
                # Gọi callback về app.py nếu có
                if self.on_update:
                    self.on_update(process_data)
            except json.JSONDecodeError as e:
                log(f"Invalid JSON data: {repr(line)} -- Error: {e}", level="WARNING")


def send_to_client(self, client_id, message: str):
    sock = self.client_sockets.get(client_id)
    if sock:
        try:
            sock.sendall((message + '\n').encode())
        except Exception as e:
            log(f"Failed to send to {client_id}: {e}", level="ERROR")