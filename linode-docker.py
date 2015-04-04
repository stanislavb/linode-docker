#!/usr/bin/env python3
from linode import Api
import os
import time

linodestatus = {'Being Created': -1,
                'Brand New': 0,
                'Running': 1,
                'Powered Off': 2}


def get_first_kernel_id_by_label(label):
    available_kernels = api.avail.kernels()
    for kernel in available_kernels:
        if label in kernel['LABEL']:
            return kernel['KERNELID']


def get_latest_64_kernel_id():
    return get_first_kernel_id_by_label('Latest 64')


def get_london_datacenter_id():
    datacenters = api.avail.datacenters()
    for datacenter in datacenters:
        if 'london' in datacenter['ABBR']:
            return datacenter['DATACENTERID']


def get_64_bit_distributions():
    distributions = api.avail.distributions()
    distributions64 = [d for d in distributions if d['IS64BIT'] == 1]
    return distributions64


def get_2015_distributions():
    distributions = get_64_bit_distributions()
    distributions2015 = [d for d in distributions if '2015' in d['CREATE_DT']]
    return distributions2015


def get_distributions_by_label(label):
    distributions = get_64_bit_distributions()
    distributions_filtered = [d for d in distributions if label in d['LABEL']]
    return distributions_filtered


def get_first_distribution_id_by_label(label):
    available_distributions = get_64_bit_distributions()
    for distribution in available_distributions:
        if label in distribution['LABEL']:
            return distribution['DISTRIBUTIONID']


def get_centos_distributions():
    return get_distributions_by_label('CentOS')


def get_centos7_distribution_id():
    return get_first_distribution_id_by_label('CentOS 7')


def get_linodes_by_status(status):
    linodes = api.linode.list()
    linodes_filtered = [l for l in linodes if l['STATUS'] == linodestatus[status]]
    return linodes_filtered


def get_new_linodes():
    return get_linodes_by_status('Brand New')


def get_first_public_interface(linodeid):
    ips = api.linode.ip.list(linodeid=linodeid)
    public_ips = [i for i in ips if i['ISPUBLIC'] == 1]
    return public_ips[0]


def set_reverse_dns(linodeid, hostname):
    ip = get_first_public_interface(linodeid=linodeid)
    ipid = ip['IPADDRESSID']
    api.linode.ip.setrdns(ipaddressid=ipid, hostname=hostname)


def get_my_first_stackscript_id_by_label(label):
    my_stackscripts = api.stackscript.list()
    for stackscript in my_stackscripts:
        if label in stackscript['LABEL']:
            return stackscript['STACKSCRIPTID']


def get_centos_docker_stackscript_id():
    return get_my_first_stackscript_id_by_label("Docker CentOS 7")


def get_disk_id_list(linodeid):
    disklist = api.linode.disk.list(linodeid=linodeid)
    return [d['DISKID'] for d in disklist]


def create_centos7_docker_disks(linodeid, sshkey):
    distributionid = get_centos7_distribution_id()

    rootdisk = api.linode.disk.createfromstackscript(
        linodeid=linodeid,
        stackscriptid=get_centos_docker_stackscript_id(),
        stackscriptudfresponses="{}",
        distributionid=distributionid,
        label="CentOS 7",
        size=get_max_disk_size(linodeid=linodeid)-512,
        rootpass=os.environ['LINODE_ROOT_PASS'],
        rootsshkey=sshkey,
    )

    swapdisk = api.linode.disk.create(
        linodeid=linodeid,
        label="swap",
        type="swap",
        size=512,
    )

    disklist = [rootdisk['DiskID'], swapdisk['DiskID']]
    return disklist


def wait_for_pending_jobs(linodeid):
    while True:
        pending_jobs = api.linode.job.list(linodeid=linodeid, pendingonly=1)
        if len(pending_jobs) == 0:
            return True
        time.sleep(3)


def delete_all_configs(linodeid):
    configs = api.linode.config.list(linodeid=linodeid)
    for config in configs:
        api.linode.config.delete(linodeid=linodeid, configid=config['ConfigID'])


def get_plan_id_from_linode(linodeid):
    linode = api.linode.list(linodeid=linodeid)[0]
    return linode['PLANID']


def get_max_disk_size(linodeid):
    planid = get_plan_id_from_linode(linodeid)
    plan = api.avail.linodeplans(planid=planid)
    return plan['DISK'] * 1024


if __name__ == "__main__":
    # Must have API key
    apikey = os.environ['LINODE_API_KEY']
    api = Api(apikey)

    kernelid = os.getenv('LINODE_KERNEL')
    if not kernelid:
        kernelid = get_latest_64_kernel_id()

    sshkey = open(os.path.expanduser('~/.ssh/id_rsa.pub')).read()

    new_linodes = get_new_linodes()
    for linode in new_linodes:
        linodeid = linode['LINODEID']
        disklist = get_disk_id_list(linodeid=linodeid)
        if len(disklist) == 0:
            disklist = create_centos7_docker_disks(linodeid, sshkey)
            delete_all_configs(linodeid=linodeid)

        if len(api.linode.config.list(linodeid=linodeid)) == 0:
            api.linode.config.create(
                linodeid=linodeid,
                kernelid=kernelid,
                label="Docker CentOS 7",
                disklist=','.join(map(str, disklist)),
            )
        wait_for_pending_jobs(linodeid=linodeid)
        api.linode.boot(linodeid=linodeid)
