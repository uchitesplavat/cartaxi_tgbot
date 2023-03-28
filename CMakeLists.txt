cmake_minimum_required(VERSION 3.16)
project(telegram_bot)

set(PostgreSQL_INCLUDE_DIR /usr/include/postgresql)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
set(Boost_USE_MULTITHREADED ON)

find_package(PostgreSQL REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(PQXX libpqxx)
find_package(libpqxx REQUIRED)
find_package(libpqxx REQUIRED COMPONENTS pqxx)
find_package(Threads REQUIRED)
find_package(OpenSSL REQUIRED)
find_package(Boost COMPONENTS system REQUIRED)
find_package(CURL)
include_directories(/usr/local/include ${OPENSSL_INCLUDE_DIR} ${Boost_INCLUDE_DIR})
include_directories(${PQXX_INCLUDE_DIRS})
add_executable(cartaxi_bot src/car.cpp)


target_link_libraries(cartaxi_bot PRIVATE /home/up/tgbot-cpp/libTgBot.a ${CMAKE_THREAD_LIBS_INIT} ${OPENSSL_LIBRARIES} ${Boost_LIBRARIES} ${PostgreSQL_LIBRARIES} ${lipqxx_LIBRARIES} ${PQXX_LIBRARIES})