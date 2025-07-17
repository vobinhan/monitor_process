#ifndef TCP_CLIENT_H
#define TCP_CLIENT_H

#include <string>
#include <memory>
#include <boost/asio.hpp>

class TCPClient {
public:
    TCPClient(const std::string& host, int port, std::string& client_id, std::string& password);

    bool connect();
    bool send_data(const std::string& data);
    bool is_connected() const;
    std::string receive_data();
    std::string get_id() const { return clientId_;}
private:
    std::string host_;
    int port_;
    std::string clientId_;
    std::string passWd_;
    std::unique_ptr<boost::asio::ip::tcp::socket> socket_;

    std::string leftover_;
};

#endif // TCP_CLIENT_H