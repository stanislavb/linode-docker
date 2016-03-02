#!/bin/bash

cat <<EOT > /etc/yum.repos.d/docker-centos.repo
[docker-centos]
name=Docker Repository
baseurl=https://yum.dockerproject.org/repo/main/centos/$releasever/
enabled=1
gpgcheck=1
gpgkey=https://yum.dockerproject.org/gpg
EOT

yum -y update
yum -y install docker-engine python-pip
pip install docker-compose
systemctl enable docker
systemctl start docker
