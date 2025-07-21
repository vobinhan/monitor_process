# Process Monitoring System
## Environment
OS: Ubuntu 24.04

### Server
$ python3 -m venv venv \
$ source venv/bin/activate \
$ pip install flask flask-socketio eventlet

### Client
CMake version ≥ 3.10 \
CMD: \
$ sudo apt update \
$ sudo apt install build-essential cmake libboost-all-dev -y

## Tutorial Run
### Server
$ cd server \
$ python app.py 

### Client
Mỗi client, chạy dòng lệnh \
$ cd client/build \
$ ./client --client_id client(1-10) --password password --server_host <host server> --server_port 8000

-----
NOTE:  \
Source build step client (can if): \
$ cd client \
$ mkdir -p build \
$ cd build \
$ cmake .. \
$ make

Nếu build lại client cần rf -rm build, sau đó mkdir build và cd build, chạy lệnh cmake ..

Các app_1,app_2 ... \
=> Chạy ./app_1 ... Nếu cần chạy để mô phỏng tiến trình. \
Các app này mô phỏng 1 process đang chạy. Để phục vụ cho test kill tiến trình \

Search tên app trên thanh tìm kiếm để kill tiến trình


## System Architecture
```mermaid
flowchart TD
    subgraph Clients
        C1[C++ Client 1]
        C2[C++ Client 2]
        CN[C++ Client N]
    end

    subgraph Server
        TCPServer
        WebInterface
        ProcessDB[(ProcessDB)]
    end

    C1 -->|TCP:8000| TCPServer
    C2 -->|TCP:8000| TCPServer
    CN -->|TCP:8000| TCPServer
    WebInterface -->|WebSocket| Browser
    TCPServer --> ProcessDB
    ProcessDB --> WebInterface
```

## Core Modules Flow
### TCP Server Module
```mermaid
flowchart TD
    A[Start Server] --> B[Bind Port 8000]
    B --> C[Listen for Connections]
    C --> D{New Connection?}
    D -->|Yes| E[Authenticate Client]
    E -->|Success| F[Create Client Thread]
    F --> G[Receive Process Data]
    G --> H[Update ProcessDB]
    H --> I[Notify WebInterface]
    D -->|No| C
```

### Client Module
```mermaid
flowchart TD
    A[Start Client] --> B[Connect to Server]
    B --> C{Auth Success?}
    C -->|Yes| D[Start Command Listener]
    C -->|No| B
    D --> E[Send Process Data Every 5s]
    E --> F{Connection Alive?}
    F -->|Yes| E
    F -->|No| B
```

### Web Interface Module
```mermaid
flowchart TD
    A[User Opens Browser] --> B[Load Web UI]
    B --> C[Connect WebSocket]
    C --> D[Receive Real-time Updates]
    D --> E[Render Process Table]
    E --> F{User Clicks Kill?}
    F -->|Yes| G[Send Kill Command]
    G --> H[Show Result]
```
## Detailed Component Flows
### Authentication Flow
```mermaid
sequenceDiagram
    Client->>Server: {"client_id":"id","password":"pass"}
    Server->>AuthDB: Check credentials
    AuthDB-->>Server: Validation Result
    alt Valid
        Server->>Client: AUTH_SUCCESS
        Server->>ProcessDB: Add client
    else Invalid
        Server->>Client: AUTH_FAIL
    end
```

### Kill Process Flow
```mermaid
sequenceDiagram
    Browser->>Server: Kill PID 123
    Server->>Client: {"type":"kill","pid":123}
    Client->>System: kill -9 123
    Client->>Server: {"kill_result":{...}}
    Server->>Browser: Show notification
```

### Process Monitoring Flow
```mermaid
sequenceDiagram
    loop Every 5 seconds
        Client->>Server: Process Data (JSON)
        Server->>ProcessDB: Update records
        Server->>WebUI: Broadcast update
        WebUI->>Browser: Render table
    end
```
