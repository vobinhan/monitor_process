#include "tcp_client.h"
#include "process.h"
#include <iostream>
#include <thread>
#include <chrono>
#include <map>
#include <fstream>
#include <regex>

std::ofstream log_file("client.log", std::ios::app);

void log_debug(const std::string& message) {
    log_file << "[DEBUG] " << message << std::endl;
}

int main(int argc, char* argv[]) {
    // Parse tham số dòng lệnh (--client_id, --password, ...)
    std::map<std::string, std::string> args;
    for (int i = 1; i < argc - 1; i += 2) {
        std::string key(argv[i]);
        std::string value(argv[i + 1]);
        args[key] = value;
    }

    std::string client_id = args["--client_id"];
    std::string password = args["--password"];
    std::string server_host = args["--server_host"];
    int server_port = std::stoi(args["--server_port"]);

    TCPClient client(server_host, server_port, client_id, password);

    while (true) {
        if (!client.connect()) {
            log_debug("Kết nối thất bại. Thử lại sau 5s...");
            std::this_thread::sleep_for(std::chrono::seconds(5));
            continue;
        }
        log_debug("Kết nối thành công đến server");

        // Gửi thông tin xác thực
        std::string auth_msg = R"({"client_id":")" + client_id + R"(","password":")" + password + "\"}";
        if (!client.send_data(auth_msg)) {
            log_debug("Xác thực thất bại. Thử lại sau 5s...");
            std::this_thread::sleep_for(std::chrono::seconds(5));
            continue;
        }
        log_debug("Xác thực thành công");

        // Thread nhận và xử lý lệnh kill từ server
        std::thread([&client]() {
            while (true) {
                std::string command = client.receive_data();
                log_debug("Command raw: ");
                for (char c : command) {
                    log_file << "[" << static_cast<int>(c) << "]";
                }
                log_file << std::endl;
                if (command.empty()) {
                    std::this_thread::sleep_for(std::chrono::milliseconds(200));
                    continue;
                }
                command.erase(std::remove(command.begin(), command.end(), ' '), command.end());
                if (command.find("\"type\":\"kill\"") != std::string::npos) {
                    log_debug("Nhận lệnh kill: " + command);
                    std::smatch match;
                    std::regex rgx("\"pid\":\"(\\d+)\"");
                    if (std::regex_search(command, match, rgx)) {
                        std::string pid = match[1];
                        log_debug("Đang thực hiện kill PID: " + pid);
                        int ret = std::system(("kill -9 " + pid).c_str());
                        std::string result = (ret == 0) ? "success" : "fail";

                        std::string response = R"({"kill_result":{"client_id":")" + client.get_id() +
                            R"(","pid":")" + pid + R"(","result":")" + result + R"("}})";
                        log_debug("Gửi kết quả kill về server: " + response);
                        client.send_data(response);
                    }
                }
            }
        }).detach();

        // Gửi dữ liệu process định kỳ
        while (true) {
            std::string processes = ProcessCollector::get_processes();
            std::string full_json = R"({"client_id":")" + client_id + R"(",)" + processes.substr(1);
            log_debug("send_data ...");
            if (!client.send_data(full_json)) {
                log_debug("Gửi dữ liệu thất bại. Thử reconnect...");
                break; // quay lại vòng ngoài để reconnect
            }

            std::this_thread::sleep_for(std::chrono::seconds(5));
        }

        // Nếu rơi ra ngoài vòng lặp gửi dữ liệu, chờ 5s rồi reconnect
        std::this_thread::sleep_for(std::chrono::seconds(5));
    }

    return 0;
}
