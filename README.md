## This project is made obsolete by Linode's new user-friendly API: https://developers.linode.com/guides/python-guide/

# Linode Docker
Use Linode API to provision a docker host on CentOS 7

This is primarily an example of how to use the code provided by https://github.com/ghickman/linode to bootstrap a fresh Linode VM with CentOS 7 and Docker.

It relies on environment variables. See examples in .linode file.

# Usage
```
pip install linode
source .linode
./linode-docker.py
```
