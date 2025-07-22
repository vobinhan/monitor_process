#include "tcp_client.h"
#include <boost/asio.hpp>
#include <iostream>

using boost::asio::ip::tcp;

/**
 * @brief Constructs a TCPClient object.
 * 
 * @param host The server host address.
 * @param port The server port.
 * @param client_id The client identifier.
 * @param password The client password.
 */
TCPClient::TCPClient(const std::string& host, int port, std::string& client_id, std::string& password) 
    : host_(host), port_(port), clientId_(client_id), passWd_(password) {}

    /**
 * @brief Establishes a connection to the server.
 * 
 * @return true if connection is successful, false otherwise.
 */
bool TCPClient::connect() 
{
    try 
    {
        boost::asio::io_context io_context;
        tcp::socket socket(io_context);
        tcp::resolver resolver(io_context);
        boost::asio::connect(socket, resolver.resolve(host_, std::to_string(port_)));
        socket_ = std::make_unique<tcp::socket>(std::move(socket));
        error_logged_ = false;
        return true;
    } catch (const std::exception& e) 
    {
        return false;
    }
}

/**
 * @brief Sends data to the server.
 * 
 * @param data The string data to send.
 * @return true if data is sent successfully, false otherwise.
 */
bool TCPClient::send_data(const std::string& data) 
{
    try {
        boost::asio::write(*socket_, boost::asio::buffer(data + "\n"));
        return true;
    } catch (const std::exception& e) {
        return false;
    }
}

std::string TCPClient::receive_data() {
    try {
        if (!is_connected()) {
            if (!error_logged_) {
                std::cerr << "[WARN] Socket is not connected\n";
                error_logged_ = true;
            }
            return "";
        }

        size_t newline = leftover_.find('\n');
        if (newline != std::string::npos) {
            std::string line = leftover_.substr(0, newline);
            leftover_ = leftover_.substr(newline + 1);
            return line;
        }

        boost::asio::streambuf buf;
        boost::asio::read_until(*socket_, buf, '\n');
        std::istream is(&buf);
        std::string incoming;
        std::getline(is, incoming);

        leftover_ += incoming + "\n";

        newline = leftover_.find('\n');
        if (newline != std::string::npos) {
            std::string line = leftover_.substr(0, newline);
            leftover_ = leftover_.substr(newline + 1);
            return line;
        }

    } catch (const std::exception& e) {
        if (!error_logged_) {
            std::cerr << "[ERROR] receive_data: " << e.what() << std::endl;
            error_logged_ = true;
        }
    }
    return "";
}


/**
 * @brief Checks if the socket is currently connected.
 * 
 * @return true if connected, false otherwise.
 */
bool TCPClient::is_connected() const {
    return socket_ && socket_->is_open();
}
