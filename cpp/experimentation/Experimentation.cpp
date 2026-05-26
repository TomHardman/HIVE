#include <iostream>
#include "Experimentation.h"

int main() {
    std::cout << "Program Start\n";
    
    {
        MyClass a = MyClass();
        MyClass b = MyClass{"John"};
        MyClass c = MyClass(123);
        MyClass c1 = 123;
    }

    MyClass a{};
    MyClass b{"John"};
    MyClass c(123);

    MyClass d = a; // copy constructor
    std::cout << d << "\n";
    d = b; // copy assignment
    std::cout << d << "\n";
    

    MyClass e = std::move(b); // move constructor
    std::cout << e << "\n";
    e = std::move(c); // move assignment
    std::cout << e << "\n";
    return 0;
}