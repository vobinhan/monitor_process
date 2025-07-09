#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <thread>
#include <chrono>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <jsoncpp/json/json.h>

std::string client_id, password, server_host;
int server_port;

std::string getProcessInfo() {
    std::stringstream ss;
    FILE* fp = popen("ps -eo pid,comm,%cpu --no-header", "r");
    if (!fp) return "";

    char buf[256];
    while (fgets(buf, sizeof(buf), fp)) {
        ss << buf;
    }
    pclose(fp);
    return ss.str();
}

Json::Value buildMessage(const std::string& rawProcess) {
    Json::Value root;
    root["client_id"] = client_id;
    root["password"] = password;
    Json::Value processes(Json::arrayValue);

    std::stringstream ss(rawProcess);
    std::string line;
    while (std::getline(ss, line)) {
        std::istringstream ls(line);
        int pid;
        std::string name;
        double cpu;
        ls >> pid >> name >> cpu;

        Json::Value proc;
        proc["pid"] = pid;
        proc["name"] = name;
        proc["cpu"] = cpu;
        processes.append(proc);
    }
    root["processes"] = processes;
    return root;
}

void sendProcessData(int sockfd) {
    while (true) {
        std::string raw = getProcessInfo();
        Json::Value msg = buildMessage(raw);
        Json::StreamWriterBuilder writer;
        std::string json_str = Json::writeString(writer, msg);
        send(sockfd, json_str.c_str(), json_str.size(), 0);
        std::this_thread::sleep_for(std::chrono::seconds(5));
    }
}

int main(int argc, char* argv[]) {
    if (argc != 9) {
        std::cerr << "Usage: Client --client_id <ID> --password <PWD> --server_host <IP> --server_port <PORT>\n";
        return 1;
    }

    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--client_id") client_id = argv[++i];
        else if (arg == "--password") password = argv[++i];
        else if (arg == "--server_host") server_host = argv[++i];
        else if (arg == "--server_port") server_port = std::stoi(argv[++i]);
    }

    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in servaddr{};
    servaddr.sin_family = AF_INET;
    servaddr.sin_port = htons(server_port);
    inet_pton(AF_INET, server_host.c_str(), &servaddr.sin_addr);

    if (connect(sockfd, (sockaddr*)&servaddr, sizeof(servaddr)) < 0) {
        perror("Connect failed");
        return 1;
    }

    std::cout << "Connected to server. Sending process info...\n";
    sendProcessData(sockfd);
    close(sockfd);
    return 0;
}

