#ifndef PROCESS_H
#define PROCESS_H

#include <string>

class ProcessCollector {
public:
    // Thu thập thông tin process và trả về JSON
    static std::string get_processes();
    
    // Hàm hỗ trợ kill process (dùng cho lệnh từ server)
    static bool kill_process(int pid);
};

#endif // PROCESS_H