#!/bin/bash

cat <<EOT > /etc/yum.repos.d/virt7-testing.repo
[virt7-testing]
name=virt7-testing
baseurl=http://cbs.centos.org/repos/virt7-testing/x86_64/os/
enabled=1
gpgcheck=0
exclude=kernel
EOT

yum -y update
yum -y install docker
systemctl enable docker
systemctl start docker
