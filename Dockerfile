FROM archlinux:latest

RUN pacman -Syy && \
    pacman -S --noconfirm make cmake git valgrind gcc
RUN git clone --recursive https://github.com/Fumesover/Criterion /Criterion && \
    mkdir /Criterion/build/ && \
    cd /Criterion/build/ && \
    cmake -DCMAKE_INSTALL_PREFIX=/usr .. && \
    cmake --build . && \
    make install

