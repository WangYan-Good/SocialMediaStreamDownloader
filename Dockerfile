#
# refer command
# docker run -d --name=aliyundrive-webdav --restart=unless-stopped -p 8080:8080 \
# -v /etc/aliyundrive-webdav/:/etc/aliyundrive-webdav/ \
# -e REFRESH_TOKEN='your refresh token' \
# -e WEBDAV_AUTH_USER=admin \
# -e WEBDAV_AUTH_PASSWORD=admin \
# messense/aliyundrive-webdav
#
#
# This docker file uses the almalinux image
FROM quay.io/almalinux/almalinux

# maintancer
MAINTAINER wangyan 16609932941@163.com

# 换源
RUN rpm --import https://repo.almalinux.org/almalinux/RPM-GPG-KEY-AlmaLinux
RUN rpm -q gpg-pubkey-ced7258b-6525146f
# 注意：“# baseurl” 中间有个空格（AlmaLinux 专有）
RUN sed -e 's|^mirrorlist=|#mirrorlist=|g' \
    -e 's|^# baseurl=https://repo.almalinux.org|baseurl=https://mirrors.aliyun.com|g' \
    -i.bak \
    /etc/yum.repos.d/almalinux*.repo
RUN yum clean packages
RUN yum makecache
RUN echo "switch resource succeed!!!"
RUN dnf upgrade almalinux-release -y

# command install git
RUN echo "install denpendency"
# RUN yum install zlib-devel bzip2-devel ncurses-devel sqlite-devel readline-devel tk-devel gcc make libffi-devel -y
RUN yum install -y wget perl gcc zlib-devel git

# command install openssl 1.1.1w
RUN cd /usr/local/src
RUN wget https://github.com/openssl/openssl/releases/download/OpenSSL_1_1_1w/openssl-1.1.1w.tar.gz
RUN tar -zxvf ./openssl-1.1.1w.tar.gz
RUN cd openssl-1.1.1w/ && ./config --prefix=/usr/local/openssl --openssldir=/usr/local/openssl && make && make install
RUN mv /usr/bin/openssl /usr/bin/openssl_backup
RUN ln -s /usr/local/openssl/bin/openssl /usr/bin/openssl
RUN ln -s /usr/local/openssl/lib/libssl.so.1.1 /usr/lib/libssl.so.1.1
RUN ln -s /usr/local/openssl/lib/libcrypto.so.1.1 /usr/lib/libcrypto.so.1.1
RUN mv /usr/lib64/libssl.so.1.1 /usr/lib64/libssl.so.1.1.bak
RUN ln -s /usr/local/openssl/lib/libssl.so.1.1 /usr/lib64/libssl.so.1.1
RUN ln -s /usr/local/openssl/lib/libcrypto.so.1.1
RUN rm openssl-1.1.1w.tar.gz
RUN rm -rf openssl-1.1.1w

# command install python312
RUN echo "download https://www.python.org/ftp/python/3.12.6/Python-3.12.6.tgz"
RUN wget https://www.python.org/ftp/python/3.12.6/Python-3.12.6.tgz
RUN echo "tar -zxvf Python-3.12.6.tgz"
RUN tar -zxvf Python-3.12.6.tgz && cd Python-3.12.6/ && ./configure -C --with-openssl=/usr/local/openssl --with-openssl-rpath=auto --prefix=/usr/local/python312 && make && make install
RUN ln -s /usr/local/python312/bin/python3.12 /usr/bin/python3
RUN ln -s /usr/local/python312/bin/pip3.12 /usr/bin/pip3
RUN ln -s /usr/local/python312/bin/python3.12-config /usr/bin/python3-config
RUN rm Python-3.12.6.tgz
RUN rm -rf Python-3.12.6



# command deploy SocialMediaStreamDownloader project
RUN mkdir -p /mnt/main/Service
COPY /mnt/main/Service/SocialMediaStreamDownloader /mnt/main/Service
# RUN git clone --recursive git@github.com:WangYan-Good/SocialMediaStreamDownloader.git