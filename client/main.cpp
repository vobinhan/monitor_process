#include "tcp_client.h"
#include "process.h"
#include <iostream>
#include <thread>
#include <chrono>
#include <map>
#include <fstream>

#include <regex>

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

    // Kết nối đến server
    TCPClient client(server_host, server_port, client_id, password);
    while (true) {
        if (!client.connect()) {
            std::cerr << "Retrying in 5s...\n";
            std::this_thread::sleep_for(std::chrono::seconds(5));
            continue;
        }

        // Auth
        std::string auth_msg = R"({"client_id":")" + client_id + R"(","password":")" + password + "\"}";
        if (!client.send_data(auth_msg)) {
            std::cerr << "Auth failed. Reconnecting in 5s...\n";
            std::this_thread::sleep_for(std::chrono::seconds(5));
            continue;
        }

        while (true) {
            std::string processes = ProcessCollector::get_processes();
            std::string full_json = R"({"client_id":")" + client_id + R"(",)" + processes.substr(1); 
            if (!client.send_data(full_json)) {
                std::cerr << "Send failed. Reconnecting...\n";
                break; // out of inner loop -> reconnect
            }
            std::this_thread::sleep_for(std::chrono::seconds(5));
        }
    }

    // Định kỳ gửi process data
    int count = 0;
    while (true) {
        std::string processes = ProcessCollector::get_processes();
        std::string full_json = R"({"client_id":")" + client_id + R"(",)" + processes.substr(1); 
        client.send_data(full_json);
        std::this_thread::sleep_for(std::chrono::seconds(5));  // Gửi mỗi 5 giây
        count++;
        std::cout << count << std::endl;
    }

    std::thread([&client]() {
        while (true) {
            std::string command = client.receive_data();
            if (command.find("\"type\":\"kill\"") != std::string::npos) {
                std::smatch match;
                std::regex rgx("\"pid\":\"(\\d+)\"");
                if (std::regex_search(command, match, rgx)) {
                    std::string pid = match[1];
                    std::string result;
                    int ret = std::system(("kill -9 " + pid).c_str());
                    result = (ret == 0) ? "success" : "fail";

                    std::string response = R"({"kill_result":{"client_id":")" + client.get_id() +
                        R"(","pid":")" + pid + R"(","result":")" + result + R"("}})";
                    client.send_data(response);
                }
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }).detach();

    return 0;
}