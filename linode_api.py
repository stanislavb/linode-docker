import linode
import time
import logging

logger = logging.getLogger()


class LinodeApi:
    linodestatus = {'Being Created': -1,
                    'Brand New': 0,
                    'Running': 1,
                    'Powered Off': 2}

    def __init__(self, apikey):
        self.api = linode.Api(apikey)

    def get_first_kernel_id_by_label(self, label):
        available_kernels = self.api.avail.kernels()
        for kernel in available_kernels:
            if label in kernel['LABEL']:
                logger.info('Searched for {} kernel. Found ID {}: {}'.format(
                    label, kernel['KERNELID'], kernel['LABEL']))
                return kernel['KERNELID']

    def get_latest_64_kernel_id(self):
        return self.get_first_kernel_id_by_label('Latest 64')

    def get_london_datacenter_id(self):
        datacenters = self.api.avail.datacenters()
        for datacenter in datacenters:
            if 'london' in datacenter['ABBR']:
                return datacenter['DATACENTERID']

    def get_64_bit_distributions(self):
        distributions = self.api.avail.distributions()
        distributions64 = [d for d in distributions if d['IS64BIT'] == 1]
        return distributions64

    def get_2016_distributions(self):
        distributions = self.get_64_bit_distributions()
        distributions2016 = [d for d in distributions if '2016' in d['CREATE_DT']]
        return distributions2016

    def get_distributions_by_label(self, label):
        distributions = self.get_64_bit_distributions()
        distributions_filtered = [d for d in distributions if label in d['LABEL']]
        logger.info('Searched for {} distributions, found: {}'.format(label, distributions_filtered))
        return distributions_filtered

    def get_first_distribution_id_by_label(self, label):
        available_distributions = self.get_64_bit_distributions()
        for distribution in available_distributions:
            if label in distribution['LABEL']:
                logger.info('Searched for {} distribution. Found ID {}: {}'.format(
                    label, distribution['DISTRIBUTIONID'], distribution['LABEL']))
                return distribution['DISTRIBUTIONID']

    def get_centos_distributions(self):
        return self.get_distributions_by_label('CentOS')

    def get_centos7_distribution_id(self):
        return self.get_first_distribution_id_by_label('CentOS 7')

    def get_linodes_by_status(self, status):
        linodes = self.api.linode.list()
        linodes_filtered = [l for l in linodes if l['STATUS'] == self.linodestatus[status]]
        return linodes_filtered

    def get_new_linodes(self):
        return self.get_linodes_by_status('Brand New')

    def get_first_public_interface(self, linodeid):
        ips = self.api.linode.ip.list(linodeid=linodeid)
        public_ips = [i for i in ips if i['ISPUBLIC'] == 1]
        return public_ips[0]

    def set_reverse_dns(self, linodeid, hostname):
        ip = self.get_first_public_interface(linodeid=linodeid)
        ipid = ip['IPADDRESSID']
        self.api.linode.ip.setrdns(ipaddressid=ipid, hostname=hostname)

    def get_my_first_stackscript_id_by_label(self, label):
        my_stackscripts = self.api.stackscript.list()
        for stackscript in my_stackscripts:
            if label in stackscript['LABEL']:
                return stackscript['STACKSCRIPTID']

    def get_centos_docker_stackscript_id(self):
        return self.get_my_first_stackscript_id_by_label("Docker CentOS 7")

    def get_disk_id_list(self, linodeid):
        disklist = self.api.linode.disk.list(linodeid=linodeid)
        return [d['DISKID'] for d in disklist]

    def create_centos7_docker_disks(self, linodeid, sshkey, rootpass,
                                    stackscriptid=None, swapsize=512):
        distributionid = self.get_centos7_distribution_id()

        create_args = {
            "linodeid": linodeid,
            "distributionid": distributionid,
            "label": "CentOS 7",
            "size": self.get_max_disk_size(linodeid=linodeid)-swapsize,
            "rootpass": rootpass,
            "rootsshkey": sshkey,
        }

        if stackscriptid is not None:
            create_args["stackscriptid"] = stackscriptid
            create_args["stackscriptudfresponses"] = "{}"
            rootdisk = self.api.linode.disk.createfromstackscript(**create_args)
        else:
            rootdisk = self.api.linode.disk.createfromdistribution(**create_args)

        swapdisk = self.api.linode.disk.create(
            linodeid=linodeid,
            label="swap",
            type="swap",
            size=swapsize,
        )

        disklist = [rootdisk['DiskID'], swapdisk['DiskID']]
        return disklist

    def wait_for_pending_jobs(self, linodeid):
        while True:
            pending_jobs = self.api.linode.job.list(linodeid=linodeid, pendingonly=1)
            if len(pending_jobs) == 0:
                return True
            time.sleep(3)

    def delete_all_configs(self, linodeid):
        configs = self.api.linode.config.list(linodeid=linodeid)
        for config in configs:
            self.api.linode.config.delete(linodeid=linodeid, configid=config['ConfigID'])

    def get_plan_id_from_linode(self, linodeid):
        linode = self.api.linode.list(linodeid=linodeid)[0]
        return linode['PLANID']

    def get_max_disk_size(self, linodeid):
        planid = self.get_plan_id_from_linode(linodeid)
        logger.info("Linode {} has plan {}".format(linodeid, planid))
        plan = self.api.avail.linodeplans(planid=planid)[0]
        return plan['DISK'] * 1024

    def boot(self, linodeid):
        return self.api.linode.boot(linodeid=linodeid)

    def list_configs(self, linodeid):
        return self.api.linode.config.list(linodeid=linodeid)

    def create_config(self, linodeid, kernelid, label, disklist):
        return self.api.linode.config.create(
            linodeid=linodeid,
            kernelid=kernelid,
            label=label,
            disklist=disklist
        )
