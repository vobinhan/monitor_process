#include "tcp_client.h"
#include <boost/asio.hpp>
#include <iostream>

using boost::asio::ip::tcp;

TCPClient::TCPClient(const std::string& host, int port, std::string& client_id, std::string& password) 
    : host_(host), port_(port), clientId_(client_id), passWd_(password) {}

bool TCPClient::connect() 
{
    try 
    {
        boost::asio::io_context io_context;
        tcp::socket socket(io_context);
        tcp::resolver resolver(io_context);
        boost::asio::connect(socket, resolver.resolve(host_, std::to_string(port_)));
        socket_ = std::make_unique<tcp::socket>(std::move(socket));
        std::cerr << "connected" <<  std::endl;
        return true;
    } catch (const std::exception& e) 
    {
        std::cerr << "Lỗi kết nối: " << e.what() << std::endl;
        return false;
    }
}

bool TCPClient::send_data(const std::string& data) 
{
    try {
        boost::asio::write(*socket_, boost::asio::buffer(data + "\n"));
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Lỗi gửi dữ liệu: " << e.what() << std::endl;
        return false;
    }
}

std::string TCPClient::receive_data() {
    try {
        if (!is_connected()) {
            std::cerr << "[WARN] Socket không còn kết nối\n";
            return "";
        }

        // Nếu có dòng dư chưa xử lý → trả ngay
        size_t newline = leftover_.find('\n');
        if (newline != std::string::npos) {
            std::string line = leftover_.substr(0, newline);
            leftover_ = leftover_.substr(newline + 1);
            std::cerr << "[WARN] Socket không còn kết nối" << line;
            return line;
        }

        // Nếu không có dòng dư → đọc tiếp
        boost::asio::streambuf buf;
        boost::asio::read_until(*socket_, buf, '\n');
        std::istream is(&buf);
        std::string incoming;
        std::getline(is, incoming);

        // Append vào leftover để xử lý
        leftover_ += incoming + "\n";

        // Xử lý như lúc đầu
        newline = leftover_.find('\n');
        if (newline != std::string::npos) {
            std::string line = leftover_.substr(0, newline);
            leftover_ = leftover_.substr(newline + 1);
            return line;
        }

    } catch (const std::exception& e) {
        std::cerr << "[ERROR] receive_data: " << e.what() << std::endl;
    }
    return "";
}


bool TCPClient::is_connected() const {
    return socket_ && socket_->is_open();
}