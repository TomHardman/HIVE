#pragma once

#include <iostream>
#include <string>
#include <fmt/format.h>

class MyClass {
    public:
        MyClass()
        {
            std::cout << "Default constructor\n";
        }
        explicit MyClass(std::string name): name_(std::move(name)) 
        {
            std::cout << fmt::format("MyClass constructor for instance with name {}\n", name_);
        }
        MyClass(int number): number_(number)
        {
            std::cout << fmt::format("MyClass constructor for instance with number {}\n", number_);
        }
        // Destructor
        ~MyClass() {
            std::cout << "MyClass destructor\n";
        }
        // Copy constructor
        MyClass(const MyClass& other) {
            std::cout << "MyClass copy constructor\n";
        }
        // Move constructor
        MyClass(MyClass&& other) noexcept {
            std::cout << "MyClass move constructor\n";
        }
        //Move assignment operator
        MyClass& operator=(MyClass&& other) noexcept {
            std::cout << "MyClass move assignment operator\n";
            name_ = other.name_;
            number_ = other.number_;
            return *this;
        }
        //Copy assignment operator
        MyClass& operator=(const MyClass& other) {
            std::cout << "MyClass copy assignment operator\n";
            name_ = other.name_;
            number_ = other.number_;
            return *this;
        }
        // print 
        friend std::ostream& operator<<(std::ostream& os, const MyClass& myClass) {
            os << "MyClass instance with name " << myClass.name_ << " and number " << myClass.number_;
            return os;
        }
    private:
        std::string name_;
        int number_{};
};