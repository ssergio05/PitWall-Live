#include "../include/Receiver.hpp"
#include <direct.h>
#include <iostream>

int main() {
    char cwd[1024];
    if (_getcwd(cwd, sizeof(cwd)) != NULL) {
        std::cout << "[DEBUG] El C++ esta trabajando en: " << cwd << std::endl;
    }
    try {
        TelemetryReceiver receiver(20777);
        receiver.start();
    }
    catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    return 0;
}