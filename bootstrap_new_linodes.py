#!/usr/bin/env python3
import os
import logging
from linode_api import LinodeApi

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# Must have API key
apikey = os.environ['LINODE_API_KEY']
api = LinodeApi(apikey)

kernelid = os.getenv('LINODE_KERNEL')
if not kernelid:
    kernelid = api.get_latest_64_kernel_id()

sshkey = open(os.path.expanduser('~/.ssh/id_rsa.pub')).read()

new_linodes = api.get_new_linodes()
for new_linode in new_linodes:
    linodeid = new_linode['LINODEID']
    disklist = api.get_disk_id_list(linodeid=linodeid)
    if len(disklist) == 0:
        disklist = api.create_centos7_docker_disks(
            linodeid=linodeid,
            sshkey=sshkey,
            rootpass=os.environ['LINODE_ROOT_PASS'])
        api.delete_all_configs(linodeid=linodeid)

    if len(api.list_configs(linodeid=linodeid)) == 0:
        api.create_config(
            linodeid=linodeid,
            kernelid=kernelid,
            label="CentOS 7",
            disklist=','.join(map(str, disklist)),
        )
    api.wait_for_pending_jobs(linodeid=linodeid)
    api.boot(linodeid)
