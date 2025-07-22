# import socket
# import json
# import threading
# from config import HOST, PORT, MAX_CONNECTIONS, BUFFER_SIZE
# from auth.authenticator import Authenticator
# from core.process_db import ProcessDB
# from utils.logger import log
# import time

# class TCPServer:
#     # Initialize socket server, authentication, and database
#     def __init__(self, socketio, on_update=None):
#         self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         self.auth = Authenticator()
#         self.process_db = ProcessDB()
#         # web interface
#         self._buffer = {}  # Initialize buffer variable
#         self.active_clients = {}  # Track currently connected clients

#         self.on_update = on_update  # Store callback from app.py

#         self.client_sockets = {}  # client_socket -> client_id
#         self.socketio = socketio
        
#     def start(self):
#         self.server_socket.bind((HOST, PORT))
#         self.server_socket.listen(MAX_CONNECTIONS)
#         log(f"Server started on {HOST}:{PORT}")
#         while True:
#             client_socket, addr = self.server_socket.accept()
#             threading.Thread(
#                 target=self.handle_client,
#                 args=(client_socket, addr),

#                 daemon=True
#             ).start()

#     def handle_client(self, client_socket: socket.socket, addr: tuple):
#         client_id = None
#         authenticated = False
#         try:
#             # Authenticate
#             log(f"Authenticating Client...")
#             auth_data = client_socket.recv(BUFFER_SIZE).decode()
#             auth = json.loads(auth_data)
#             client_id = auth.get("client_id")
#             password = auth.get("password")

#             if not client_id or not password:
#                 client_socket.send(b"AUTH_FAIL\n")
#                 return

#             # Nếu client_id đang online → từ chối kết nối mới
#             now = time.time()
#             if client_id in self.client_sockets and now - self.active_clients.get(client_id, 0) < 10:
#                 log(f"[WARNING] client_id '{client_id}' already connected and active → rejecting new connection.")
#                 try:
#                     existing_socket = self.client_sockets[client_id]
#                     warning = {"type": "warning", "message": "Another client attempted to connect with your client_id"}
#                     existing_socket.sendall((json.dumps(warning) + "\n").encode())
#                 except:
#                     pass
#                 client_socket.send(b"AUTH_FAIL_DUPLICATE_ID\n")
#                 return

#             if not self.auth.validate(client_id, password):
#                 client_socket.send(b"AUTH_FAIL\n")
#                 return

#             self.client_sockets[client_id] = client_socket
#             self.active_clients[client_id] = time.time()
#             client_socket.send(b"AUTH_SUCCESS\n")
#             log(f"[AUTH] Client '{client_id}' authenticated successfully.")
#             authenticated = True
#             log(f"[EMIT] status_update for client {client_id} → online")
#             self.socketio.emit("status_update", {client_id: "online"})
#             self.socketio.emit("process_data", {"client_id": client_id, "processes": []})
#             log(f"[EMIT] process_data (empty) for client {client_id}")
#             if client_id in self.process_db.db:
#                 self.socketio.emit("process_data", {
#                     "client_id": client_id,
#                     "processes": self.process_db.db[client_id]
#                 })
#             # Receive process data
#             while True:
#                 data = client_socket.recv(BUFFER_SIZE).decode()
#                 if not data:
#                     break

#                 if data.startswith('{"kill_result":'):
#                     result = json.loads(data)
#                     self.socketio.emit('kill_result', {'kill_result': result})
#                 else:
#                     self._process_data(addr, data)

#         except (ConnectionResetError, json.JSONDecodeError) as e:
#             log(f"[ERROR] Client error: {e}")

#         finally:
#             # 🔴 Xử lý khi client disconnect (real-time)
#             log(f"[DISCONNECT] Client '{client_id}' disconnected")

#             if authenticated and client_id:
#                 self.client_sockets.pop(client_id, None)
#                 self.active_clients.pop(client_id, None)
#                 self.process_db.db.pop(client_id, None)  # ✅ Xóa process ngay lập tức

#                 # ✅ Emit status và xóa UI realtime
#                 self.socketio.emit("process_data", {
#                     "client_id": client_id,
#                     "processes": []  # Gửi danh sách trống để UI tự xóa
#                 })

#                 self.socketio.emit("status_update", {
#                     client_id: "offline"
#                 })

#                 log(f"[STATUS] {client_id} marked as offline and process data cleared in real-time.")


#             client_socket.close()


#     def send_command_to_client(self, client_id, command_str):
#         sock = self.client_sockets.get(client_id)
#         if sock:
#             try:
#                 print(f"------[DEBUG] Sending kill command to client {client_id}: {command_str}")
#                 sock.sendall((command_str + '\n').encode())
#             except Exception as e:
#                 log(f"Error sending command: {e}", level="ERROR")

#     def _authenticate(self, client_socket: socket.socket, data: str) -> bool:
#         try:
#             auth = json.loads(data)
#             client_id = auth.get("client_id")
#             password = auth.get("password")

#             if not client_id or not password:
#                 client_socket.send(b"AUTH_FAIL\n")
#                 return False

#             # ✅ Nếu client_id đang online → từ chối kết nối mới
#             now = time.time()
#             last_seen = self.active_clients.get(client_id)

#             if client_id in self.client_sockets:
#                 log(f"[REJECT] client_id '{client_id}' is already connected → reject new connection.")
#                 try:
#                     existing_socket = self.client_sockets[client_id]
#                     warning = {
#                         "type": "warning",
#                         "message": f"Another client tried to use your ID '{client_id}'"
#                     }
#                     existing_socket.sendall((json.dumps(warning) + "\n").encode())
#                 except:
#                     pass
#                 client_socket.send(b"AUTH_FAIL_DUPLICATE_ID\n")
#                 return

#             # ✅ Cho phép nếu xác thực đúng
#             if self.auth.validate(client_id, password):
#                 self.client_sockets[client_id] = client_socket
#                 client_socket.send(b"AUTH_SUCCESS\n")
#                 log(f"[AUTH] Client '{client_id}' authenticated successfully.")
#                 return True

#         except json.JSONDecodeError:
#             pass

#         client_socket.send(b"AUTH_FAIL\n")
#         return False

    
#     def _process_data(self, addr: tuple, data: str):
#         self._buffer.setdefault(addr, "")
#         self._buffer[addr] += data  # accumulate data

#         while '\n' in self._buffer[addr]:
#             line, self._buffer[addr] = self._buffer[addr].split('\n', 1)
#             try:
#                 # print(f"Parsing line from {addr}: {repr(line)}")
#                 process_data = json.loads(line)
#                 self.process_db.update(process_data["client_id"], process_data["processes"])
#                 log(f"Updated processes from {addr}")
#                 self.active_clients[process_data["client_id"]] = time.time()
#                 print(self.active_clients[process_data["client_id"]])

#                 # Call callback to app.py if available
#                 if self.on_update:
#                     self.on_update(process_data)
#             except json.JSONDecodeError as e:
#                 log(f"Invalid JSON data: {repr(line)} -- Error: {e}", level="WARNING")

#     def cleanup_inactive_clients(self):
#         import time
#         while True:
#             now = time.time()

#             # Dọn các client không gửi data quá 10s
#             inactive_clients = [
#                 cid for cid, ts in self.active_clients.items()
#                 if now - ts > 10
#             ]
#             for cid in inactive_clients:
#                 print(f"[CLEANUP] Client {cid} marked as offline")
#                 if cid in self.active_clients:
#                     del self.active_clients[cid]
#                 if cid in self.process_db.db:
#                     del self.process_db.db[cid]

#             # Gửi trạng thái của TẤT CẢ client từng kết nối
#             all_clients = set(list(self.process_db.db.keys()) + list(self.client_sockets.keys()))

#             statuses = {
#                 cid: "online" if cid in self.active_clients else "offline"
#                 for cid in all_clients
#             }

#             self.socketio.emit("status_update", statuses)
#             time.sleep(5)


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
