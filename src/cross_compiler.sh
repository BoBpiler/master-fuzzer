# 크로스 컴파일러와 QEMU 설치 (GCC)
sudo apt-get install -y gcc-aarch64-linux-gnu
sudo apt-get install -y g++-aarch64-linux-gnu
sudo apt-get install -y gcc-mips64-linux-gnuabi64 g++-mips64-linux-gnuabi64
sudo apt-get install -y gcc-mips64el-linux-gnuabi64 g++-mips64el-linux-gnuabi64
sudo apt-get install -y gcc-powerpc64le-linux-gnu g++-powerpc64le-linux-gnu
sudo apt-get install -y gcc-powerpc64-linux-gnu g++-powerpc64-linux-gnu
sudo apt-get install -y gcc-s390x-linux-gnu g++-s390x-linux-gnu
sudo apt-get install -y gcc-sparc64-linux-gnu g++-sparc64-linux-gnu

# QEMU 설치
sudo apt-get install -y qemu-user-static

