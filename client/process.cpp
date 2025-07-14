#include "process.h"
#include <stdio.h>
#include <string>
#include <sstream>
#include <vector>
#include <iomanip>

std::string escape_json(const std::string& input) {
    std::ostringstream ss;
    for (char c : input) {
        if (c == '\"') ss << "\\\"";
        else if (c == '\\') ss << "\\\\";
        else ss << c;
    }
    return ss.str();
}

std::string ProcessCollector::get_processes() {
    FILE* pipe = popen("ps -eo pid,uid,user,comm,%cpu,%mem,state,lstart,etime,time,args --sort=-%cpu --no-headers", "r");
    if (!pipe) return "{}";

    char buffer[1024];
    std::string line, result;
    std::string json = R"({"processes":[)";
    bool first = true;

    while (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
        line = buffer;
        std::istringstream iss(line);
        std::string pid, uid, user, comm, cpu, mem, state;
        std::string lstart1, lstart2, lstart3, lstart4, lstart5;
        std::string etime, cputime;

        // Parse fields
        iss >> pid >> uid >> user >> comm >> cpu >> mem >> state
            >> lstart1 >> lstart2 >> lstart3 >> lstart4 >> lstart5 >> etime >> cputime;


        // Chuyển state bắt đầu bằng R lên đầu bảng — server sẽ sắp xếp sau

        if (!first) json += ",";
        first = false;

        std::string start_time = lstart1 + " " + lstart2 + " " + lstart3 + " " + lstart4 + " " + lstart5;

        json += R"({"pid":")" + pid +
                R"(","uid":")" + uid +
                R"(","user":")" + user +
                R"(","name":")" + escape_json(comm) +
                R"(","cpu":")" + cpu +
                R"(","memory_mb":")" + mem +
                R"(","state":")" + state +
                R"(","start_time":")" + escape_json(start_time) +
                R"(","elapsed":")" + etime +
                R"(","cpu_time":")" + cputime +
                R"("})";
    }

    pclose(pipe);
    json += "]}";
    return json;
}
