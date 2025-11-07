#include <iostream>
#include <fstream>
#include <sstream>

int main() {
    int p = 1;
    int r = 1;

    std::ostringstream s;

    for (int i = 1; i < 500000; ++i) {
        s << "2025-10-31 12:15:59  WAIT P" << p << "  R" << r - 1 << "\n";
        s << "2025-10-31 12:15:59  HOLD P" << p << "  R" << r << "\n";

        if (i % 10 == 0) {
            s << "2025-10-31 12:15:59  HOLD P" << p << "  R" << r - 10 << "\n";
            p += 5;
            r += 5;
        }

        p += 1;
        r += 1;
    }

    std::ofstream f("test.log");
    f << s.str();
    f.close();

    return 0;
}
