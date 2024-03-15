#!/bin/sh

# This script install various mesh routing protocols on Debian (tested with Debian Bullseye/11.7)

set -xe

apt-get update
apt-get install -y sudo time git subversion build-essential g++ bash make golang libssl-dev patch libncurses5 libncurses5-dev zlib1g-dev gawk flex gettext wget unzip xz-utils python3 python3-distutils-extra rsync linux-headers-$(uname -r) pkg-config libnl-3-dev libnl-genl-3-dev libiw-dev bison cmake

WD="/tmp/work/"
mkdir $WD
echo "working directory: $WD"

export PATH=$PATH:/usr/sbin

# install yggdrasil versions
cd $WD
wget https://dl.google.com/go/go1.21.3.linux-amd64.tar.gz -O go.tar.gz
tar -xvf go.tar.gz
export PATH=$WD/go/bin:$PATH
export GOPATH=$WD/go
cd $WD
git clone https://github.com/yggdrasil-network/yggdrasil-go
cd yggdrasil-go

./build
cp yggdrasil /usr/bin/yggdrasil
cp yggdrasilctl /usr/bin/yggdrasilctl

git checkout v0.3.16
./build
cp yggdrasil /usr/bin/yggdrasil-0.3
cp yggdrasilctl /usr/bin/yggdrasilctl-0.3

git checkout v0.4.7
./build
cp yggdrasil /usr/bin/yggdrasil-0.4
cp yggdrasilctl /usr/bin/yggdrasilctl-0.4

git checkout v0.5.5
./build
cp yggdrasil /usr/bin/yggdrasil-0.5
cp yggdrasilctl /usr/bin/yggdrasilctl-0.5

#rm -rf "$WD"
