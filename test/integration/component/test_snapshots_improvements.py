'''
Created on Feb 6, 2013

@author: root
'''

""" P1 tests for Snapshots Improvements
"""
# Import Local Modules
from nose.plugins.attrib import attr
from urlparse import urlparse
from marvin.cloudstackTestCase import cloudstackTestCase, unittest
from marvin.integration.lib.utils import (random_gen)
from marvin.integration.lib.base import (
                                        Account,
                                        ServiceOffering,
                                        VirtualMachine,
                                        Snapshot,
                                        Template,
                                        Volume,
                                        Host,
                                        DiskOffering
                                        )
from marvin.integration.lib.common import (get_domain,
                                        get_zone,
                                        get_template,
                                        cleanup_resources,
                                        )
from marvin.cloudstackAPI import (createSnapshot,
                                  migrateVirtualMachine,
                                  createVolume,
                                  createTemplate,
                                  listOsTypes
                                  )
from marvin.asyncJobMgr import (job)
from marvin import remoteSSHClient
import time
import pdb


class Services:
    def __init__(self):
        self.services = {
                        "service_offering": {
                                    "name": "Tiny Instance",
                                    "displaytext": "Tiny Instance",
                                    "cpunumber": 1,
                                    "cpuspeed": 200,    # in MHz
                                    "memory": 256,    # In MBs
                        },
                         "service_offering2": {
                                    "name": "Med Instance",
                                    "displaytext": "Med Instance",
                                    "cpunumber": 1,
                                    "cpuspeed": 1000,    # In MHz
                                    "memory": 1024,    # In MBs
                        },
                        "disk_offering": {
                                    "displaytext": "Small Disk",
                                    "name": "Small Disk",
                                    "disksize": 1,
                                    "storagetype": "shared",
                        },
                        "disk_offering2": {
                                    "displaytext": "Med Disk",
                                    "name": "Med Disk",
                                    "disksize": 5,
                                    "storagetype": "shared",
                        },
                        "virtual_machine": {
                                    "displayname": "TestVM",
                                    "username": "root",
                                    "password": "password",
                                    "ssh_port": 22,
                                    "hypervisor": 'XenServer',
                                    "privateport": 22,
                                    "publicport": 22,
                                    "protocol": 'TCP',
                        },
                        "win_template": {
                                    "displaytext": 'windows2008R2',
                                    "name": 'windows2008R2',
                                    "ostype": 'Windows Server 2008 R2 (64-bit)',
                                    "url": 'http://10.147.28.7/templates/Windows2008/Windows2008R2server64bit.vhd',
                                    "hypervisor": 'XenServer',
                                    "format": 'VHD',
                                    "isfeatured": 'true',
                                    "isextractable": 'true',
                                    "ispublic": 'true',
                        },
                        "template": {
                                    "displaytext": "Public Template",
                                    "name": "Public template",
                                    "ostype": 'CentOS 5.3 (64-bit)',
                                    "url": "http://download.cloud.com/releases/2.0.0/UbuntuServer-10-04-64bit.vhd.bz2",
                                    "hypervisor": 'XenServer',
                                    "format": 'VHD',
                                    "isfeatured": True,
                                    "ispublic": True,
                                    "isextractable": True,
                                    "templatefilter": 'self',
                        },
                        "volume": {
                                   "diskname": "TestDiskServ",
                                   "size": 1,    # GBs
                        },
                        "diskdevice": "/dev/xvda",
                        "rootdisk": "/dev/xvda",

                        "mount_dir": "/mnt/tmp",
                        "sub_dir": "test",
                        "sub_lvl_dir1": "test1",
                        "sub_lvl_dir2": "test2",
                        "random_data": "random.data",

                        "ostype": 'CentOS 5.3 (64-bit)',
                        "NumberOfThreads": 1,
                        "sleep": 60,
                        "timeout": 10,
                        "mode": 'advanced',
                        # Networking mode: Advanced, Basic
                }


class TestSnapshotOnRootVolume(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_client = super(TestSnapshotOnRootVolume,
                               cls).getClsTestClient().getApiClient()
        cls.services = Services().services
        cls.domain = get_domain(cls.api_client, cls.services)
        cls.zone = get_zone(cls.api_client, cls.services)
        cls.template = get_template(
                                    cls.api_client,
                                    cls.zone.id,
                                    cls.services["ostype"])
        cls.account = Account.create(cls.api_client,
                                     cls.services["account"],
                                     domainid=cls.domain.id)
        # pdb.set_trace()
        cls.service_offering = ServiceOffering.create(
                                            cls.api_client,
                                            cls.services["service_offering"])
        cls.disk_offering = DiskOffering.create(
                                    cls.api_client,
                                    cls.services["disk_offering"],
                                    domainid=cls.domain.id)
        cls.service_offering2 = ServiceOffering.create(
                                            cls.api_client,
                                            cls.services["service_offering2"])
        cls.disk_offering2 = DiskOffering.create(
                                    cls.api_client,
                                    cls.services["disk_offering2"],
                                    domainid=cls.domain.id)

        cls._cleanup = [cls.account,
                        cls.service_offering,
                        cls.disk_offering,
                        cls.service_offering2,
                        cls.disk_offering2]

    @classmethod
    def tearDownClass(cls):
        try:
            # Cleanup resources used
            cleanup_resources(cls.api_client, cls._cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def setUp(self):
        self.apiclient = self.testClient.getApiClient()
        self.dbclient = self.testClient.getDbConnection()
        self.cleanup = []
        return

    def tearDown(self):
        try:
            # Clean up, terminate the created instance, volumes and snapshots
            cleanup_resources(self.apiclient, self.cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def test_01_snapshot_on_rootVolume(self):
        """Test create VM with default cent os template and create snapshot
            on root disk of the vm
        """
        # Validate the following
        # 1. Deploy a Linux VM using default CentOS template, use small service
        #    offering, disk offering
        # 2. Create snapshot on the root disk of this newly cteated vm
        # 3. listSnapshots should list the snapshot that was created.
        # 4. verify that secondary storage NFS share contains the reqd
        # volume under /secondary/snapshots/$accountid/$volumeid/$snapshot_uuid
        # 5. verify backup_snap_id was non null in the `snapshots` table

        # Create virtual machine with small systerm offering and disk offering
        new_virtual_machine = VirtualMachine.create(
                                    self.apiclient,
                                    self.services["virtual_machine"],
                                    templateid=self.template.id,
                                    zoneid=self.zone.id,
                                    accountid=self.account.account.name,
                                    domainid=self.account.account.domainid,
                                    serviceofferingid=self.service_offering.id,
                                    diskofferingid=self.disk_offering.id,
                                )
        self.debug("Virtual machine got created with id: %s" %
                                                    new_virtual_machine.id)
        list_virtual_machine_response = VirtualMachine.list(
                                                    self.apiclient,
                                                    id=new_virtual_machine.id)
        self.assertEqual(isinstance(list_virtual_machine_response, list),
                         True,
                         "Check listVirtualMachines returns a valid list")

        self.assertNotEqual(len(list_virtual_machine_response),
                            0,
                            "Check listVirtualMachines response")
        self.cleanup.append(new_virtual_machine)

        # Getting root volume id of the vm created above
        list_volume_response = Volume.list(
                                self.apiclient,
                                virtualmachineid=list_virtual_machine_response[0].id,
                                type="ROOT",
                                account=self.account.account.name,
                                domainid=self.account.account.domainid)

        self.assertEqual(isinstance(list_volume_response, list),
                         True,
                         "Check listVolumes returns a valid list")
        self.assertNotEqual(len(list_volume_response),
                            0,
                            "Check listVolumes response")
        self.debug(
            "Snapshot will be created on the volume with voluem id: %s" %
                                                    list_volume_response[0].id)

        # Perform snapshot on the root volume
        root_volume_snapshot = Snapshot.create(
                                        self.apiclient,
                                       volume_id=list_volume_response[0].id)
        self.debug("Created snapshot: %s for vm: %s" % (
                                        root_volume_snapshot.id,
                                        list_virtual_machine_response[0].id))
        list_snapshot_response = Snapshot.list(
                                        self.apiclient,
                                        id=root_volume_snapshot.id,
                                        account=self.account.account.name,
                                        domainid=self.account.account.domainid)
        self.assertEqual(isinstance(list_snapshot_response, list),
                         True,
                         "Check listSnapshots returns a valid list")

        self.assertNotEqual(len(list_snapshot_response),
                            0,
                            "Check listSnapshots response")
        self.assertEqual(
                list_snapshot_response[0].volumeid,
                list_volume_response[0].id,
                "Snapshot volume id is not matching with the vm's volume id")
        self.cleanup.append(root_volume_snapshot)

        # Below code is to verify snapshots in the backend and in db.
        # For time being I commented it since there are some issues in connecting to SQL through python
        # Verify backup_snap_id field in the snapshots table for the snapshot created, it should not be null

#        self.debug("select id, removed, backup_snap_id from snapshots where uuid = '%s';" % root_volume_snapshot.id)
#        qryresult = self.dbclient.execute("select id, removed, backup_snap_id from snapshots where uuid = '%s';" % root_volume_snapshot.id)
#        self.assertNotEqual(len(qryresult), 0, "Check sql query to return snapshots list")
#        snapshot_qry_response = qryresult[0]
#        snapshot_id = snapshot_qry_response[0]
#        is_removed = snapshot_qry_response[1]
#        backup_snap_id = snapshot_qry_response[2]
#        self.assertNotEqual(is_removed, "NULL", "Snapshot is removed from CS, please check the logs")
#        msg = "Backup snapshot id is set to null for the backedup snapshot :%s" % snapshot_id
#        self.assertNotEqual(backup_snap_id, "NULL", msg )
#
#        #Verify the snapshots in the backend(secondary storage)
#        hosts = Host.list(self.apiclient, type='SecondaryStorage', zoneid=self.zone.id)
#        for host in hosts :
#            # hosts[0].name = "nfs://10.147.28.7:/export/home/sanjeev"
#            parse_url = (host.name).split('/')
#             # parse_url = ['nfs:', '', '192.168.100.21', 'export', 'test']
#
#            # Stripping end ':' from storage type
#            storage_type = parse_url[0][:-1]
#            # Split IP address and export path from name
#            sec_storage_ip = parse_url[2]
#            # Sec Storage IP: 192.168.100.21
#            if sec_storage_ip[-1] != ":":
#                sec_storage_ip = sec_storage_ip + ":"
#
#            export_path = '/'.join(parse_url[3:])
#            # Export path: export/test


        return

    def test_02_snapshot_on_winVM_rootVolume(self):
        """Test create VM with windows template and create snapshot on root
            disk of the vm
        """
        # Validate the following
        # 1.Deploy a VM using windows template, use medium service offering and disk offering
        # 2.Create snapshot on the root disk of this newly cteated vm
        # 3.listSnapshots should list the snapshot that was created.
        # 4.verify that secondary storage NFS share contains the reqd
        # volume under /secondary/snapshots/$accountid/$volumeid/$snapshot_uuid
        # 5. verify backup_snap_id was non null in the `snapshots` table

        # Register windows template
        win_template = Template.register(self.apiclient,
                                         self.services["win_template"],
                                         zoneid=self.zone.id,
                                         account=self.account.account.name,
                                         domainid=self.account.account.domainid,
                                         )
        self.cleanup.append(win_template)
        # verify template download status
        win_template.download(self.apiclient)

        template_response = Template.list(self.apiclient,
                                        templatefilter="featured",
                                        account=self.account.account.name,
                                        domainid=self.account.account.domainid,
                                        name=self.services["win_template"]["name"],
                                        )
        template_id = template_response[0].id
        # Create virtual machine with small systerm offering and disk offering
        new_virtual_machine = VirtualMachine.create(self.apiclient,
                                    self.services["virtual_machine"],
                                    templateid=template_id,
                                    zoneid=self.zone.id,
                                    accountid=self.account.account.name,
                                    domainid=self.account.account.domainid,
                                    serviceofferingid=self.service_offering.id,
                                    diskofferingid=self.disk_offering.id,
                                )
        self.cleanup.append(new_virtual_machine)

        list_volume_response = Volume.list(self.apiclient,
                                           virtualmachineid=new_virtual_machine.id,
                                           type="ROOT",
                                           account=self.account.account.name,
                                           domainid=self.account.account.domainid,
                                           )

        # Perform snapshot on the root volume
        root_volume_snapshot = Snapshot.create(self.apiclient,
                                               volume_id=list_volume_response[0].id,
                                               )
        self.debug("Created snapshot: %s for vm: %s" % (root_volume_snapshot.id, new_virtual_machine.id))
        list_snapshot_response = Snapshot.list(self.apiclient,
                                               id=root_volume_snapshot.id,
                                               account=self.account.account.name,
                                               domainid=self.account.account.domainid,
                                               )
        self.assertEqual(isinstance(list_snapshot_response, list), True, "Check listSnapshots returns a valid list")
        self.assertNotEqual(len(list_snapshot_response), 0, "Check listSnapshots response")
        self.assertEqual(list_snapshot_response[0].volumeid, list_volume_response[0].id, "Snapshot volume id is not matching with the vm's volume id")

        self.cleanup.append(root_volume_snapshot)
        return


class TestCreateSnapshot(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_client = super(
                               TestCreateSnapshot,
                               cls).getClsTestClient().getApiClient()
        cls.services = Services().services
        # Get Zone, Domain and templates
        cls.domain = get_domain(cls.api_client, cls.services)
        cls.zone = get_zone(cls.api_client, cls.services)

        cls.template = get_template(
                            cls.api_client,
                            cls.zone.id,
                            cls.services["ostype"]
                            )

        cls.services["virtual_machine"]["zoneid"] = cls.zone.id

        # Create VMs, NAT Rules etc
        cls.account = Account.create(
                            cls.api_client,
                            cls.services["account"],
                            domainid=cls.domain.id
                            )
        cls.service_offering = ServiceOffering.create(
                                            cls.api_client,
                                            cls.services["service_offering"]
                                            )
        cls._cleanup = [
                        cls.service_offering,
                        cls.account,
                        ]
        return

    @classmethod
    def tearDownClass(cls):
        try:
            # Cleanup resources used
            cleanup_resources(cls.api_client, cls._cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def setUp(self):
        self.apiclient = self.testClient.getApiClient()
        self.dbclient = self.testClient.getDbConnection()
        self.cleanup = []
        return

    def tearDown(self):
        try:
            # Clean up, terminate the created instance, volumes and snapshots
            cleanup_resources(self.apiclient, self.cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def create_VM(self, host_id=None):
        try:
            self.debug('Creating VM for account=%s' %
                                            self.account.account.name)
            vm = VirtualMachine.create(
                                    self.apiclient,
                                    self.services["virtual_machine"],
                                    templateid=self.template.id,
                                    accountid=self.account.account.name,
                                    domainid=self.account.account.domainid,
                                    serviceofferingid=self.service_offering.id,
                                    hostid=host_id,
                                    mode=self.services["mode"]
                                    )
            self.debug('Created VM=%s in account=%s' %
                                        (vm.id, self.account.account.name))
            return vm
        except Exception as e:
            self.fail('Unable to deploy VM in a account=%s - %s' %
                                                (self.account.account.name, e))

    def stop_VM(self, virtual_machine):
        try:
            self.debug("Stopping the virtual machine")
            virtual_machine.stop(self.apiclient)
            self.debug("Checking VM state")
        except Exception as e:
            self.fail("Failed to stop virtual machine - %s, %s" %
                                                (virtual_machine.name, e))
        vms = VirtualMachine.list(
                                      self.apiclient,
                                      id=virtual_machine.id,
                                      listall=True
                                      )
        self.assertEqual(
                        isinstance(vms, list),
                        True,
                        "List virtual machines should return valid response"
                         )
        vm = vms[0]
        self.assertEqual(
                             vm.state,
                             "Stopped",
                             "VM state should be stopped after API call"
                             )
        return

    def create_Snapshot_On_Root_Disk(self, virtual_machine):
        try:
            volumes = Volume.list(
                                  self.apiclient,
                                  virtualmachineid=virtual_machine.id,
                                  type='ROOT',
                                  listall=True
                                  )
            self.assertEqual(
                            isinstance(volumes, list),
                            True,
                            "Check list response returns a valid list"
                        )
            volume = volumes[0]

            cmd = createSnapshot.createSnapshotCmd()
            cmd.volumeid = volume.id
            cmd.account = self.account.account.name
            cmd.domainid = self.account.account.domainid
            return cmd
        except Exception as e:
            self.fail('Unable to create new job for snapshot: %s' % e)

    def create_Dummy_Data_On_Root_Disk(self, ssh):
        try:
            random_data_0 = random_gen(100)
            random_data_1 = random_gen(100)
            cmds = [
                    "mkdir -p %s" % self.services["mount_dir"],
                    "mount %s1 %s" % (
                                      self.services["rootdisk"],
                                      self.services["mount_dir"]
                                      ),
                    "mkdir -p %s/%s/{%s,%s} " % (
                                                self.services["mount_dir"],
                                                self.services["sub_dir"],
                                                self.services["sub_lvl_dir1"],
                                                self.services["sub_lvl_dir2"]
                                            ),
                    "echo %s > %s/%s/%s/%s" % (
                                                random_data_0,
                                                self.services["mount_dir"],
                                                self.services["sub_dir"],
                                                self.services["sub_lvl_dir1"],
                                                self.services["random_data"]
                                            ),
                    "echo %s > %s/%s/%s/%s" % (
                                                random_data_1,
                                                self.services["mount_dir"],
                                                self.services["sub_dir"],
                                                self.services["sub_lvl_dir2"],
                                                self.services["random_data"]
                                        ),
                    "sync",
                    "umount %s" % (self.services["mount_dir"]),
                ]
            for c in cmds:
                self.debug("Command: %s" % c)
                self.debug("Result: %s" % ssh.execute(c))
        except Exception as e:
            self.fail(
                "Failed to create dummy data on ROOT disk of VM: %s" % e)
            return

    def get_Host_For_Migration(self, vm):
        try:
            hosts = Host.list(
                              self.apiclient,
                              zoneid=self.zone.id,
                              virtualmachineid=vm.id,
                              listall=True
                              )
            if not isinstance(hosts, list):
                self.fail(
                    "Failed to find suitable host for vm migration: %s" %
                                                                    vm.name)
            else:
                return hosts[0].id
        except Exception as e:
            self.fail("Failed to find suitable host for migration: %s" % e)

    def migrate_VMs(self):
        """Run concurrent migration jobs for VMs deployed in account"""

        self.debug("Finding VMs deployed in the account: %s" %
                                                    self.account.account.name)
        vms = VirtualMachine.list(
                                  self.apiclient,
                                  account=self.account.account.name,
                                  domainid=self.account.account.domainid,
                                  listall=True)
        self.assertEqual(isinstance(vms, list),
                         True,
                         "List VMs shall return a valid response")
        try:
            jobs = []
            for vm in vms:
                self.debug("Migrating vm: %s to host" % vm.id)
                hostid = self.get_Host_For_Migration(vm)

                cmd = migrateVirtualMachine.migrateVirtualMachineCmd()
                cmd.virtualmachineid = vm.id
                cmd.hostid = hostid
                jobs.append(cmd)

            # Verify IO usage by submitting the concurrent jobs
            self.testClient.submitCmdsAndWait(jobs)

        except Exception as e:
            self.fail("Failed to migrate vm to host: %s" % e)

    def create_Template_from_Snapshot(self, snapshot):
        try:
            self.debug("Creating template from snapshot: %s" % snapshot.name)

            cmd = createTemplate.createTemplateCmd()
            cmd.displaytext = self.services["template"]["displaytext"]
            cmd.name = "-".join([self.services["template"]["name"],
                                 random_gen()])

            ncmd = listOsTypes.listOsTypesCmd()
            ncmd.description = self.services["template"]["ostype"]
            ostypes = self.apiclient.listOsTypes(ncmd)

            if not isinstance(ostypes, list):
                raise Exception(
                    "Unable to find Ostype id with desc: %s" %
                                        self.services["template"]["ostype"])
            cmd.ostypeid = ostypes[0].id
            cmd.snapshotid = snapshot.id

            return cmd
        except Exception as e:
            self.fail("Failed to create template from snapshot: %s - %s" %
                                                        (snapshot.name, e))

    def create_Volume_from_Snapshot(self, snapshot):
        try:
            self.debug("Creating volume from snapshot: %s" % snapshot.name)

            cmd = createVolume.createVolumeCmd()
            cmd.name = "-".join([
                                self.services["volume"]["diskname"],
                                random_gen()])
            cmd.snapshotid = snapshot.id
            cmd.zoneid = self.zone.id
            cmd.size = self.services["volume"]["size"]
            cmd.account = self.account.account.name
            cmd.domainid = self.account.account.domainid
            return cmd
        except Exception as e:
            self.fail("Failed to create volume from snapshot: %s - %s" %
                                                        (snapshot.name, e))

    def create_Snapshot_VM(self):
        """Creates a virtual machine and take a snapshot on root disk

            1. Create a virtual machine
            2. SSH into virtual machine
            3. Create dummy folders on the ROOT disk of the virtual machine
            4. Take a snapshot of ROOT disk"""

        jobs = []
        self.debug("Deploying VM for account: %s" % self.account.account.name)
        for i in range(self.services["NumberOfThreads"]):
            vm = self.create_VM()
            self.debug("Creating dummy data on ROOT disk of vm: %s" % vm.name)
            self.create_Dummy_Data_On_Root_Disk(ssh=vm.get_ssh_client())
            self.debug("Stop virtual machine: %s" % vm.name)
            self.stop_VM(vm)

            self.debug("Create snapshot on ROOT disk")
            jobs.append(self.create_Snapshot_On_Root_Disk(vm))

        # Submit snapshot job at one go
        self.testClient.submitCmdsAndWait(jobs)
        return

    def create_Snaphot_Stop_VM(self):
        """Creates a snapshot on ROOT disk while vm is in stopping state

            1. Create a virtual machine
            2. SSH into virtual machine
            3. Create dummy folders on the ROOT disk of the virtual machine
            4. Create snapshot on ROOT disk
            5. Stop virtual machine while snapshots are taken on ROOT disk"""

        self.debug("Deploying VM for account: %s" % self.account.account.name)
        for i in range(self.services["NumberOfThreads"]):
            vm = self.create_VM()
            self.debug("Creating dummy data on ROOT disk of vm: %s" % vm.name)
            self.create_Dummy_Data_On_Root_Disk(ssh=vm.get_ssh_client())

            self.debug("Create thread to stop virtual machine: %s" % vm.name)
            self.stop_VM(vm)

            self.debug("Create snapshot on ROOT disk")
            self.create_Snapshot_On_Root_Disk(vm)

        self.debug("Running concurrent migration jobs in account: %s" %
                                                    self.account.account.name)
        self.migrate_VMs()
        return

    def verify_Snapshots_On_Secondary_Storage(self, snapshot):

        qresultset = self.dbclient.execute(
                            "select backup_snap_id, account_id, volume_id" + \
                            " from snapshots where uuid='%s'" % snapshot.id)

        self.assertEqual(isinstance(qresultset, list),
                         True,
                         "Check DBQuery returns a valid list"
                        )
        self.assertNotEqual(len(qresultset), 0, "Check DB Query result set")

        qresult = qresultset[0]
        snapshot_uuid = qresult[0]    # backup_snap_id = snapshot UUID
        account_id = qresult[1]
        volume_id = qresult[2]

        # Get the Secondary Storage details from  list Hosts
        hosts = Host.list(self.apiclient,
                           type='SecondaryStorage',
                           zoneid=self.zone.id)
        self.assertEqual(isinstance(hosts, list),
                         True,
                         "Check list response returns a valid list")
        uuids = []
        for host in hosts:
            # host.name = "nfs://192.168.100.21/export/test"
            parse = urlparse(host.name)
            sec_storage_ip = parse.netloc
            storage_type = parse.scheme
            export_path = parse.path

            try:
                # Login to VM to check snapshot present on sec disk
                ssh_client = remoteSSHClient.remoteSSHClient(
                                    self.apiclient.connection.mgtSvr,
                                    22,
                                    self.apiclient.connection.user,
                                    self.apiclient.connection.passwd
                                    )

                cmds = [
                    "mkdir -p %s" % self.services["mount_dir"],
                    "mount -t %s %s:%s %s" % (
                                         storage_type,
                                         sec_storage_ip,
                                         export_path,
                                         self.services["mount_dir"]
                                         ),
                    "ls %s/snapshots/%s/%s" % (
                                               self.services["mount_dir"],
                                               account_id,
                                               volume_id),
                ]

                for c in cmds:
                    result = ssh_client.execute(c)
                uuids.append(result)

                # Unmount the Sec Storage
                cmds = [
                    "umount %s" % (self.services["mount_dir"]),
                    ]
                for c in cmds:
                    result = ssh_client.execute(c)
            except Exception as e:
                raise Exception(
                        "SSH access failed for management server: %s - %s" %
                                    (self.apiclient.connection.mgtSvr, e))

        res = str(uuids)
        self.debug("Snapshot UUIDs: %s" % res)
        self.assertEqual(
                        res.count(snapshot_uuid),
                        1,
                        "Check snapshot UUID in secondary storage and database"
                        )
        return

    def get_Snapshots_For_Account(self, account, domainid):
        try:
            snapshots = Snapshot.list(
                                      self.apiclient,
                                      account=account,
                                      domainid=domainid,
                                      listall=True
                                      )
            self.assertEqual(
                             isinstance(snapshots, list),
                             True,
                             "List snapshots shall return a valid list"
                             )
            return snapshots
        except Exception as e:
            self.fail("Failed to fetch snapshots for account: %s - %s" %
                                                                (account, e))

    def verify_Snapshots(self):
        try:
            snapshots = self.get_Snapshots_For_Account(
                                            self.account.account.name,
                                            self.account.account.domainid)
            self.assertEqual(
                    len(snapshots),
                    int(self.services["NumberOfThreads"]),
                    "No of snapshots should equal to no of threads spawned"
                 )
            for snapshot in snapshots:
                self.verify_Snapshots_On_Secondary_Storage(snapshot)
        except Exception as e:
            self.fail("Failed to verify snapshots created: %s" % e)

    def wait_for_threads(self, threads):
        """Waits till execution of all threads is complete"""

        self.debug("Waits till all active threads finished execution")
        for th in threads:
            if th.is_alive():
                self.debug("Thread th: %s is still running" % th.name)
                time.sleep(self.services["sleep"])
        return

    @attr(speed="slow")
    @attr(tags=["advanced", "advancedns"])
    @attr(configuration='concurrent.snapshots.threshold.perhost')
    def test_01_concurrent_snapshots_live_migrate(self):
        """Test perform concurrent snapshots and migrate the vm from one host
            to another

            1.Configure the concurrent.snapshots.threshold.perhost=3
            2.Deploy a Linux VM using default CentOS template, use small
            service offering, disk offering
            3.Log into the VM and create a file with content in it.
            4.repeat step 2 to 3 for 10 times to create 10 vms
            5.Perform snapshot on the root disk of this newly created VMs"""

        # Validate the following
        # a. Check all snapshots jobs are running concurrently on backgrounds
        # b. listSnapshots should list this newly created snapshot.
        # c. Verify secondary_storage NFS share contains the required volume
        #    under /secondary/snapshots/$accountid/$volumeid/$snapshot_uuid
        # d. Verify backup_snap_id was non null in "snapshots"table

        self.debug("Create virtual machine and snapshot on ROOT disk thread")
        self.create_Snapshot_VM()

        self.debug("Verify whether snapshots were created properly or not?")
        self.verify_Snapshots()
        return

    @attr(speed="slow")
    @attr(tags=["advanced", "advancedns"])
    @unittest.skip("Skipping - ListHosts doesn't return suitable VM for migration when called with virtualmachineid parameter")
    @attr(configuration='concurrent.snapshots.threshold.perhost')
    def test_02_stop_vm_concurrent_snapshots(self):
        """Test stop running VM while performing concurrent snapshot on volume

            1.Configure the concurrent.snapshots.threshold.perhost=3
            2.Deploy a Linux VM using default CentOS template, use small
            service offering, disk offering
            3.Log into the VM and create a file with content in it.
            4.repeat step 2 to 3 for 4times to create 4vms
            5.Perform snapshot on root disk of this newly created VMs(4 vms)
            6.stop the running Vms while snapshot on volume in progress"""

        # Validate the following
        # a. check all snapshots jobs are running concurrently on back grounds
        # b. listSnapshots should list this newly created snapshot.
        # c. Verify secondary_storage NFS share contains the required volume
        #    under /secondary/snapshots/$accountid/$volumeid/$snapshot_uuid.
        # d. Verify backup_snap_id was non null in "snapshots"table

        self.debug("Create virtual machine and snapshot on ROOT disk thread")
        self.create_Snaphot_Stop_VM()

        self.debug("Verify whether snapshots were created properly or not?")
        self.verify_Snapshots()
        return

    @attr(speed="slow")
    @attr(tags=["advanced", "advancedns"])
    @attr(configuration='concurrent.snapshots.threshold.perhost')
    def test_03_concurrent_snapshots_create_template(self):
        """Test while parent concurrent snapshot job in progress,create
            template from completed snapshot

            1.Configure the concurrent.snapshots.threshold.perhost=3
            2.Deploy a Linux VM using default CentOS template, use small
            service offering, disk offering
            3.Log into the VM and create a file with content in it.
            4.repeat step 2 to 3 for 10 times to create 10 vms
            5.Perform snapshot on root disk of this newly created VMs(10 vms)
            6.while parent concurrent snapshot job in progress,create template
            from completed snapshot"""

        # Validate the following
        # a.Able to create Template from snapshots
        # b.check all snapshots jobs are running concurrently on back grounds
        # c.listSnapshots should list this newly created snapshot.
        # d.Verify secondary_storage NFS share contains the required volume
        #   under /secondary/snapshots/$accountid/$volumeid/$snapshot_uuid.
        # e. Verify backup_snap_id was non null in "snapshots"table

        self.debug("Create virtual machine and snapshot on ROOT disk")
        self.create_Snapshot_VM()

        self.debug("Verify whether snapshots were created properly or not?")
        self.verify_Snapshots()

        self.debug("Fetch the list of snapshots belong to account: %s" %
                                                    self.account.account.name)
        snapshots = self.get_Snapshots_For_Account(
                                                self.account.account.name,
                                                self.account.account.domainid)
        jobs = []
        for snapshot in snapshots:
            self.debug("Create a template from snapshot: %s" % snapshot.name)
            jobs.append(self.create_Template_from_Snapshot(snapshot))

        # Verify IO usage by submitting the concurrent jobs
        self.testClient.submitCmdsAndWait(jobs)

        self.debug("Verifying if templates are created properly or not?")
        templates = Template.list(
                            self.apiclient,
                            templatefilter=self.services["template"]["templatefilter"],
                            account=self.account.account.name,
                            domainid=self.account.account.domainid,
                            listall=True)
        self.assertNotEqual(templates,
                            None,
                            "Check if result exists in list item call")
        for template in templates:
            self.assertEqual(template.isready,
                         True,
                        "Check new template state in list templates call")

        self.debug("Test completed successfully.")
        return

    @attr(speed="slow")
    @attr(tags=["advanced", "advancedns"])
    @attr(configuration='concurrent.snapshots.threshold.perhost')
    def test_04_concurrent_snapshots_create_volume(self):
        """Test while parent concurrent snapshot job in progress,create volume
            from completed snapshot

            1.Configure the concurrent.snapshots.threshold.perhost=3
            2.Deploy a Linux VM using default CentOS template, use small
            service offering, disk offering
            3.Log into the VM and create a file with content in it.
            4.repeat step 2 to 3 for 10 times to create 10 vms
            5.Perform snapshot on root disk of this newly created VMs(10 vms)
            6.while parent concurrent snapshot job in progress,create volume
            from completed snapshot"""

        # Validate the following
        # a.Able to create Volume from snapshots
        # b.check all snapshots jobs are running concurrently on back grounds
        # c.listSnapshots should list this newly created snapshot.
        # d.Verify secondary_storage NFS share contains the required volume
        #   under /secondary/snapshots/$accountid/$volumeid/$snapshot_uuid.
        # e. Verify backup_snap_id was non null in "snapshots"table

        self.debug("Create virtual machine and snapshot on ROOT disk thread")
        self.create_Snapshot_VM()

        self.debug("Verify whether snapshots were created properly or not?")
        self.verify_Snapshots()

        self.debug("Fetch the list of snapshots belong to account: %s" %
                                                    self.account.account.name)
        snapshots = self.get_Snapshots_For_Account(
                                                self.account.account.name,
                                                self.account.account.domainid)
        jobs = []
        for snapshot in snapshots:
            self.debug("Create a volume from snapshot: %s" % snapshot.name)
            jobs.append(self.create_Volume_from_Snapshot(snapshot))

        # Verify IO usage by submitting the concurrent jobs
        self.testClient.submitCmdsAndWait(jobs)

        self.debug("Verifying if volume created properly or not?")
        volumes = Volume.list(self.apiclient,
                              account=self.account.account.name,
                              domainid=self.account.account.domainid,
                              listall=True,
                              type='DATADISK')

        self.assertNotEqual(volumes,
                            None,
                            "Check if result exists in list item call")
        for volume in volumes:
            self.debug("Volume: %s, state: %s" % (volume.name, volume.state))
            self.assertEqual(volume.state,
                         "Ready",
                         "Check new volume state in list volumes call")

        self.debug("Test completed successfully.")
        return


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
