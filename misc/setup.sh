#!/bin/sh

# This script install various mesh routing protocols on Debian (tested with Debian Bullseye/11.7)

set -xe

apt-get update
apt-get install -y sudo time git subversion build-essential g++ bash make golang libssl-dev patch libncurses5 libncurses5-dev zlib1g-dev gawk flex gettext wget unzip xz-utils python3 python3-distutils-extra rsync linux-headers-$(uname -r) pkg-config libnl-3-dev libnl-genl-3-dev libiw-dev bison cmake

WD="/tmp/work/"
mkdir $WD
echo "working directory: $WD"

export PATH=$PATH:/usr/sbin

# install batman-adv
cd $WD
wget https://downloads.open-mesh.org/batman/releases/batman-adv-2023.2/batctl-2023.2.tar.gz -O batctl.tar.gz
tar -xvf batctl.tar.gz
cd batctl-*
make
make install

cd $WD
wget https://downloads.open-mesh.org/batman/releases/batman-adv-2023.2/batman-adv-2023.2.tar.gz -O batman-adv.tar.gz
tar -xvf batman-adv.tar.gz
cd batman-adv-*
make
make install

# install babel
cd $WD
wget https://www.irif.fr/~jch/software/files/babeld-1.13.1.tar.gz -O babeld.tar.gz
tar -xvf babeld.tar.gz
cd babeld-*
make
make install

# install bmx6
cd $WD
wget https://github.com/bmx-routing/bmx6/archive/v1.0.tar.gz -O bmx6.tar.gz
tar -xvf bmx6.tar.gz
cd bmx6-*
sed -i  '17i\#include <linux/sockios.h>' schedule.c
make
cp bmx6 /usr/bin/

# install bmx7
cd $WD
wget https://github.com/Mbed-TLS/mbedtls/archive/refs/tags/mbedtls-2.4.0.tar.gz -O mbedtls.tgz
tar -xvf mbedtls.tgz
cd mbedtls-*
make
make install
cd $WD
wget https://github.com/bmx-routing/bmx7/archive/v7.1.1.tar.gz -O bmx7.tar.gz
tar -xvf bmx7.tar.gz
cd bmx7-*/src
sed -i '17i\#include <linux/sockios.h>' schedule.c
sed -i 's/const void\* FAILURE_PTR;/extern const void\* FAILURE_PTR;/' bmx.h
make EXTRA_CFLAGS="-DCRYPTLIB=MBEDTLS_2_4_0"
cp bmx7 /usr/bin/

# install olsr1/olsrd
cd $WD
# get v0.9.8 with bugfixes
wget https://github.com/OLSR/olsrd/archive/204a44adc7e98b826833b6fac2f7673735832427.tar.gz -O olsrd.tar.gz
tar -xvf olsrd.tar.gz
cd olsrd-*
make
make install

# install olsr2/OONF
cd $WD
# get v0.15.1 with bugfixes
wget https://github.com/OLSR/OONF/archive/fb15d54d6a7a087cb0c5ec37c49804f6ce432396.tar.gz -O oonf.tar.gz
tar -xvf oonf.tar.gz
cd OONF-*
sed -i '2i\project(olsrd2)' CMakeLists.txt
# needed since OONF assumes this is always a git repository
cat > version.cmake << EOF
SET (OONF_VERSION 0.15.1)
SET (OONF_LIB_GIT v0.15.1-112-gfb15d54d-dirty)
EOF
cd build
cmake ..
make
make install
ln -s /usr/local/sbin/olsrd2_static /usr/local/sbin/olsrd2

# install cjdns
cd $WD
wget https://github.com/cjdelisle/cjdns/archive/cjdns-v20.6.tar.gz -O cjdns.tar.gz
tar -xvf cjdns.tar.gz
cd cjdns-*
./do
cp cjdroute /usr/bin/

# install yggdrasil
cd $WD
wget https://dl.google.com/go/go1.21.3.linux-amd64.tar.gz -O go.tar.gz
tar -xvf go.tar.gz
export PATH=$WD/go/bin:$PATH
export GOPATH=$WD/go
cd $WD
wget https://github.com/yggdrasil-network/yggdrasil-go/archive/v0.5.2.tar.gz -O yggdrasil.tar.gz
tar -xvf yggdrasil.tar.gz
cd yggdrasil-*
./build
cp yggdrasil yggdrasilctl /usr/bin/

#rm -rf "$WD"
