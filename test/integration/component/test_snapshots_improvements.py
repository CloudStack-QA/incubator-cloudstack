# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import marvin
from nose.plugins.attrib import attr
from marvin.cloudstackTestCase import *
from marvin.integration.lib.common import get_domain,get_zone
from marvin.integration.lib.base import *
from marvin.integration.lib.utils import *
from marvin.integration.lib.common import *
class Services:
    def __init__(self):
        self.services = {
                        "account": {
                                    "email": "test@test.com",
                                    "firstname": "Test",
                                    "lastname": "User",
                                    "username": "test",
                                    "password": "password",
                         },
                         "service_offering": {
                                    "name": "Tiny Instance",
                                    "displaytext": "Tiny Instance",
                                    "cpunumber": 1,
                                    "cpuspeed": 200,    # in MHz
                                    "memory": 256,      # In MBs
                        },
                         "service_offering2": {
                                    "name": "Med Instance",
                                    "displaytext": "Med Instance",
                                    "cpunumber": 1,
                                    "cpuspeed": 1000,  # In MHz
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
                         "server": {
                                    "displayname": "TestVM",
                                    "username": "root",
                                    "password": "password",
                                    "ssh_port": 22,
                                    "hypervisor": 'XenServer',
                                    "privateport": 22,
                                    "publicport": 22,
                                    "protocol": 'TCP',
                        },
                         "templates": {
                                    "displaytext": 'Template',
                                    "name": 'Template',
                                    "ostype": 'CentOS 5.3 (64-bit)',
                                    "templatefilter": 'self',
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
                        "ostype": 'CentOS 5.3 (64-bit)',
                        # Cent OS 5.3 (64 bit)
                        "sleep": 60,
                        "timeout": 10,
                        "mode": 'advanced',     # Networking mode: Advanced, Basic
                    }





class TestSnapshotOnRootVolume(cloudstackTestCase):
    @classmethod
    def setUpClass(cls):
        cls.api_client = super(TestSnapshotOnRootVolume, cls).getClsTestClient().getApiClient()
        cls.services = Services().services
        cls.domain = get_domain(cls.api_client, cls.services)
        cls.zone = get_zone(cls.api_client, cls.services)
        cls.template = get_template(cls.api_client,cls.zone.id,cls.services["ostype"])
        cls.account = Account.create(cls.api_client, cls.services["account"], domainid=cls.domain.id) 
        cls.service_offering = ServiceOffering.create(cls.api_client, cls.services["service_offering"])
        cls.disk_offering = DiskOffering.create(cls.api_client, cls.services["disk_offering"], domainid=cls.domain.id)
        cls.service_offering2 = ServiceOffering.create(cls.api_client, cls.services["service_offering2"])
        cls.disk_offering2 = DiskOffering.create(cls.api_client, cls.services["disk_offering2"], domainid=cls.domain.id)
        cls._cleanup = [cls.account, cls.service_offering, cls.disk_offering, cls.service_offering2, cls.disk_offering2]
    @classmethod
    def tearDownClass(cls):
        try:
            #Cleanup resources used
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
            #Clean up, terminate the created instance, volumes and snapshots
            cleanup_resources(self.apiclient, self.cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return


    def test_01_snapshot_on_rootVolume(self):
        """
            Test create VM with default cent os template and create snapshot on root disk of the vm 
        """
        # Validate the following
        #1.Deploy a Linux VM using default CentOS template, use small service offering, disk offering
        #2.Create snapshot on the root disk of this newly cteated vm
        #3.listSnapshots should list the snapshot that was created.
        #4.verify that secondary storage NFS share contains the reqd
        # volume under /secondary/snapshots/$accountid/$volumeid/$snapshot_uuid
        # 5. verify backup_snap_id was non null in the `snapshots` table

        #Create virtual machine with small systerm offering and disk offering
        new_virtual_machine = VirtualMachine.create( self.apiclient, self.services["server"], 
                                                     templateid=self.template.id, zoneid=self.zone.id,
                                                     accountid=self.account.account.name, domainid=self.account.account.domainid,
                                                     serviceofferingid=self.service_offering.id, diskofferingid=self.disk_offering.id,
                                                    )
        self.debug("Virtual machine got created with id: %s" % new_virtual_machine.id)
        list_virtual_machine_response = VirtualMachine.list( self.apiclient, id=new_virtual_machine.id )
        self.assertEqual( isinstance(list_virtual_machine_response, list), True, "Check listVirtualMachines returns a valid list" )
        self.assertNotEqual( len(list_virtual_machine_response), 0, "Check listVirtualMachines response")
        self.cleanup.append(new_virtual_machine)
        #Getting root volume id of the vm created above
        list_volume_response = Volume.list(self.apiclient, virtualmachineid=list_virtual_machine_response[0].id, type="ROOT",
                                           account=self.account.account.name, domainid=self.account.account.domainid )
        self.assertEqual( isinstance(list_volume_response, list), True, "Check listVolumes returns a valid list" )
        self.assertNotEqual( len(list_volume_response), 0, "Check listVolumes response")
        self.debug("Snapshot will be created on the volume with voluem id: %s" % list_volume_response[0].id)
        #Perform snapshot on the root volume
        root_volume_snapshot = Snapshot.create(self.apiclient, volume_id=list_volume_response[0].id)
        self.debug("Created snapshot: %s for vm: %s" % (root_volume_snapshot.id, list_virtual_machine_response[0].id))
        list_snapshot_response = Snapshot.list(self.apiclient, id=root_volume_snapshot.id,
                                               account=self.account.account.name, domainid=self.account.account.domainid)
        self.assertEqual(isinstance(list_snapshot_response, list), True, "Check listSnapshots returns a valid list")
        self.assertNotEqual(len(list_snapshot_response), 0, "Check listSnapshots response")
        self.assertEqual(list_snapshot_response[0].volumeid, list_volume_response[0].id, "Snapshot volume id is not matching with the vm's volume id")
        self.cleanup.append(root_volume_snapshot)
        #Below code is to verify snapshots in the backend and in db. 
        #For time being I commented it since there are some issues in connecting to SQL through python
        #Verify backup_snap_id field in the snapshots table for the snapshot created, it should not be null
         #FIXME: JIRA issue CLOUDSTACK-601 
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
        """
            Test create VM with windows template and create snapshot on root disk of the vm 
        """
        # Validate the following
        #1.Deploy a VM using windows template, use medium service offering and disk offering
        #2.Create snapshot on the root disk of this newly cteated vm
        #3.listSnapshots should list the snapshot that was created.
        #4.verify that secondary storage NFS share contains the reqd
        # volume under /secondary/snapshots/$accountid/$volumeid/$snapshot_uuid
        # 5. verify backup_snap_id was non null in the `snapshots` table
        #Register windows template
        win_template = Template.register(self.apiclient,
                                         self.services["win_template"], 
                                         zoneid=self.zone.id, 
                                         account=self.account.account.name, 
                                         domainid=self.account.account.domainid,
                                         )
        self.cleanup.append(win_template)
        #verify template download status
        win_template.download(self.apiclient)
        template_response=Template.list(self.apiclient,
                                        templatefilter="featured",
					id=win_template.id,
					#zoneid=self.zone.id,
                                        #account=self.account.account.name, 
                                        #domainid=self.account.account.domainid,
                                        #name=self.services["win_template"]["name"],
                                        )
        template_id = template_response[0].id
        #Create virtual machine with small systerm offering and disk offering
        new_virtual_machine = VirtualMachine.create( self.apiclient, self.services["server"], 
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
        #Perform snapshot on the root volume
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
