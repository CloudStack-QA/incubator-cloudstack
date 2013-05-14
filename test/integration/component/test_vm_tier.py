
""" P1 tests for VM tier
"""
# Import Local Modules
from nose.plugins.attrib import attr
from marvin.cloudstackTestCase import cloudstackTestCase, unittest
from marvin.integration.lib.base import (
                                        Account,
                                        ServiceOffering,
                                        VirtualMachine,
                                        InstanceGroup,
                                        Network,
                                        NetworkOffering,
                                        VpcOffering,
                                        VPC
                                        )
from marvin.integration.lib.common import (get_domain,
                                        get_zone,
                                        get_template,
                                        cleanup_resources,
                                        )
from marvin.cloudstackAPI import (startVirtualMachine, stopVirtualMachine)


class Services:
    """Test VPN users Services
    """

    def __init__(self):
        self.services = {
                        "account": {
                                    "email": "test@test.com",
                                    "firstname": "Test",
                                    "lastname": "User",
                                    "username": "vmtier",
                                    # Random characters are appended for unique
                                    # username
                                    "password": "password",
                         },
                         "service_offering": {
                                    "name": "Tiny Instance",
                                    "displaytext": "Tiny Instance",
                                    "cpunumber": 1,
                                    "cpuspeed": 100,    # in MHz
                                    "memory": 128,    # In MBs
                        },
                        "disk_offering": {
                                    "displaytext": "Small Disk Offering",
                                    "name": "Small Disk Offering",
                                    "disksize": 1
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
                         "vpn_user": {
                                   "username": "test",
                                   "password": "test",
                                },
                         "natrule": {
                                   "privateport": 1701,
                                   "publicport": 1701,
                                   "protocol": "UDP"
                                },
                         "network": {
                                "name": "Test Network",
                                "displaytext": "Test Network",
                                "netmask": '255.255.255.0'
                                },
                         "lbrule": {
                                    "name": "SSH",
                                    "alg": "roundrobin",
                                    # Algorithm used for load balancing
                                    "privateport": 22,
                                    "publicport": 2222,
                                    "openfirewall": False,
                                    "startport": 22,
                                    "endport": 2222,
                                    "protocol": "TCP",
                                    "cidrlist": '0.0.0.0/0',
                                },
                        "nw_off_vpc": {
                                    "name": 'VPC Network offering',
                                    "displaytext": 'VPC Network off',
                                    "guestiptype": 'Isolated',
                                    "supportedservices": 'Vpn,Dhcp,Dns,SourceNat,PortForwarding,Lb,UserData,StaticNat,NetworkACL',
                                    "traffictype": 'GUEST',
                                    "availability": 'Optional',
                                    "useVpc": 'on',
                                    "serviceProviderList": {
                                            "Vpn": 'VpcVirtualRouter',
                                            "Dhcp": 'VpcVirtualRouter',
                                            "Dns": 'VpcVirtualRouter',
                                            "SourceNat": 'VpcVirtualRouter',
                                            "PortForwarding": 'VpcVirtualRouter',
                                            "Lb": 'VpcVirtualRouter',
                                            "UserData": 'VpcVirtualRouter',
                                            "StaticNat": 'VpcVirtualRouter',
                                            "NetworkACL": 'VpcVirtualRouter'
                                        },
                                    "servicecapabilitylist": {
                                    },
                                },
                         "network_offering": {
                                    "name": 'Network_Off',
                                    "displaytext": 'Network_Off',
                                    "guestiptype": 'Isolated',
                                    "supportedservices": 'Dhcp,Dns,SourceNat,PortForwarding,Vpn,Firewall,Lb,UserData,StaticNat',
                                    "traffictype": 'GUEST',
                                    "availability": 'Optional',
                                    "serviceProviderList": {
                                            "Dhcp": 'VirtualRouter',
                                            "Dns": 'VirtualRouter',
                                            "SourceNat": 'VirtualRouter',
                                            "PortForwarding": 'VirtualRouter',
                                            "Vpn": 'VirtualRouter',
                                            "Firewall": 'VirtualRouter',
                                            "Lb": 'VirtualRouter',
                                            "UserData": 'VirtualRouter',
                                            "StaticNat": 'VirtualRouter',
                                    },
                         },
                         "vpc_offering": {
                                    "name": 'VPC off',
                                    "displaytext": 'VPC off',
                                    "supportedservices": 'Dhcp,Dns,SourceNat,PortForwarding,Vpn,Lb,UserData,StaticNat',
                                },
                        "vpc": {
                                "name": "TestVPC",
                                "displaytext": "TestVPC",
                                "cidr": '10.0.0.1/24'
                                },
                        "ostype": 'CentOS 5.3 (64-bit)',
                        "sleep": 60,
                        "timeout": 10,
                        "mode": 'advanced',
                        # Networking mode: Advanced, Basic
                    }

@unittest.skip("Skipping - work in progress")
class TestVMTier(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_client = super(TestVMTier,
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
        cls.service_offering = ServiceOffering.create(
                                            cls.api_client,
                                            cls.services["service_offering"]
                                            )

        cls._cleanup = [cls.service_offering, ]
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
        self.account = Account.create(
                            self.apiclient,
                            self.services["account"],
                            domainid=self.domain.id
                            )
        self.cleanup = [self.account, ]
        return

    def tearDown(self):
        try:
            # Clean up, terminate the created instance, volumes and snapshots
            cleanup_resources(self.apiclient, self.cleanup)
            pass
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def create_Instance(self, group=None, startvm=True, networks=None):
        """Creates an instance in account"""
        self.debug("Deploying an instance in account: %s" %
                                                self.account.account.name)
        try:
            vm = VirtualMachine.create(
                                self.apiclient,
                                self.services["virtual_machine"],
                                templateid=self.template.id,
                                accountid=self.account.account.name,
                                domainid=self.account.account.domainid,
                                startvm=startvm,
                                networkids=networks,
                                serviceofferingid=self.service_offering.id,
                                group=group)
            vms = VirtualMachine.list(self.apiclient, id=vm.id, listall=True)
            self.assertIsInstance(vms,
                                  list,
                                  "List VMs should return a valid response")
            if startvm:
                self.assertEqual(vms[0].state, "Running",
                             "Vm state should be running after deployment")
            else:
                self.assertEqual(vms[0].state, "Stopped",
                             "Vm state should be stopped after deployment")
            return vm
        except Exception as e:
            self.fail("Failed to deploy an instance: %s" % e)

    def add_Vm_To_InstanceGroup(self, vms=[], group=None):
        """Adds VM to instance group"""

        if group is not None:
            self.debug("Adding VMs to group: %s" % group)
        else:
            self.debug("Removing VMs from existing group")
        for vm in vms:
            vm.update(self.apiclient, group=group)
        return

    def validate_Vm_InstanceGroup(self, vms=[], group=None, state="Running"):
        """Validates if VMs belong to instance group"""

        self.debug("Checking if vm belong to tier: %s" % group.id)
        for vm in vms:
            self.debug("Name: %s, Group: %s" % (vm.name, group.name))
            instances = VirtualMachine.list(self.apiclient,
                                            id=vm.id,
                                            groupid=group.id,
                                            listall=True)
            self.assertIsInstance(instances,
                                list,
                                "List vms should return vm belonging to group")
            instance = instances[0]
            self.assertEqual(instance.group, group.name,
                             "Group name should match for instance")
            self.assertEqual(instance.state, state,
                             "Instance state should be %s" % state)
        return

    def get_Network(self, account):
        """Returns a network for account"""

        networks = Network.list(
                                self.apiclient,
                                account=account.account.name,
                                domainid=account.account.domainid,
                                listall=True
                                )
        self.assertIsInstance(networks,
                              list,
                              "List networks should return a valid response")
        return networks[0]

    def create_VM_Tier(self):
        """Create and validate the VM tier"""

        self.debug("Creating VM tier in network: %s" %
                                            self.get_Network(self.account))
        try:
            network = self.get_Network(self.account)
            vm_tier = InstanceGroup.create(self.apiclient,
                                name="VMTier",
                                account=self.account.account.name,
                                domainid=self.account.account.domainid,
                                networkid=network.id)
            self.debug("Created VM tier: %s" % vm_tier.name)
            self.debug("Validating VM tier after creation")
            self.validate_VM_Tier(vm_tier)
            return vm_tier
        except Exception as e:
            self.fail("Failed to create VM tier: %s" % e)

    def validate_VM_Tier(self, vm_tier, name=None):
        """Validates the VM tier"""

        vm_tiers = InstanceGroup.list(self.apiclient,
                                             id=vm_tier.id,
                                             listall=True)
        self.assertIsInstance(vm_tiers,
                              list,
                              "List VM tier should return a valid response")

        tier = vm_tiers[0]

        name = vm_tier.name if name == None else name
        self.assertEqual(tier.name,
                         name,
                         "Names of VM tier should match")
        return

    def create_VPC(self, cidr='10.1.2.1/16'):
        self.debug("Creating a VPC offering..")
        self.services["vpc_offering"]["name"] = self.services["vpc_offering"]["name"] + str(cidr)
        vpc_off = VpcOffering.create(
                                    self.apiclient,
                                    self.services["vpc_offering"]
                                    )

        self._cleanup.append(self.vpc_off)
        self.debug("Enabling the VPC offering created")
        vpc_off.update(self.apiclient, state='Enabled')

        self.debug("Creating a VPC network in the account: %s" %
                                                    self.account.account.name)
        self.services["vpc"]["cidr"] = cidr
        vpc = VPC.create(
                        self.apiclient,
                        self.services["vpc"],
                        vpcofferingid=vpc_off.id,
                        zoneid=self.zone.id,
                        account=self.account.account.name,
                        domainid=self.account.account.domainid
                        )
        return vpc

    def create_Network(self, network_off, gateway='10.1.1.1', vpc=None):
        try:
            self.services["network"]["name"] = "NETWORK-" + str(gateway)
            self.debug('Adding Network=%s' % self.services["network"])
            if vpc is not None:
                vpcid = vpc.id
            else:
                vpcid = None
            obj_network = Network.create(self.apiclient,
                                    self.services["network"],
                                    accountid=self.account.account.name,
                                    domainid=self.account.account.domainid,
                                    networkofferingid=network_off.id,
                                    zoneid=self.zone.id,
                                    gateway=gateway,
                                    vpcid=vpcid)
            self.debug("Created network with ID: %s" % obj_network.id)
            return obj_network
        except Exception as e:
            self.fail('Unable to create a Network with offering %s' % e)

    def create_VM_in_Network(self, network, host_id=None):
        try:
            self.debug('Creating VM in network=%s' % network.name)
            vm = VirtualMachine.create(
                                    self.apiclient,
                                    self.services["virtual_machine"],
                                    accountid=self.account.account.name,
                                    domainid=self.account.account.domainid,
                                    serviceofferingid=self.service_offering.id,
                                    networkids=[str(network.id)],
                                    hostid=host_id
                                    )
            self.debug('Created VM=%s in network=%s' % (vm.id, network.name))

            return vm
        except:
            self.fail('Unable to create VM in a Network=%s' % network.name)

    @attr(tags=["advanced", "advancedns"])
    def test_01_create_update_delete_vm_tier(self):
        """Test create/update/delete Vm tier with network ID"""

        # Validate the following
        # 1. Create VM tier by passing networkID as parameter
        # 2. Vm tier should be created successfully

        self.debug("Creating VM tier for account: %s" %
                                                    self.account.account.name)
        vm_tier = self.create_VM_Tier()
        self.debug("Validating VM tier created: %s" % vm_tier.name)
        self.validate_VM_Tier(vm_tier)

        self.debug("Update VM tier: %s" % vm_tier.name)
        vm_tier.update(self.apiclient, name="UpdatedVMTier")

        self.debug("Validating VM tier updated: %s" % vm_tier.id)
        self.validate_VM_Tier(vm_tier, name="UpdatedVMTier")

        self.debug("Deleting VM tier: %s" % vm_tier.id)
        try:
            vm_tier.delete(self.apiclient)
        except Exception as e:
            self.fail("Failed to delete VM tier: %s" % e)

        self.debug("Validating VM tier delete using list instance group")
        vm_tiers = InstanceGroup.list(self.apiclient, id=vm_tier.id)
        self.assertEqual(vm_tiers, None, "List VM tiers should not response")
        return

    @attr(tags=["advanced", "advancedns"])
    @unittest.skip("Tested")
    def test_02_add_vms_to_vmtier(self):
        """Test add VMs to the vmtier"""

        # 1. Create a VMTier
        # 2. Join the VM to Tier by Deploying a VM using default template,
        #    small service offering , small data disk offering,TierName(Group
        #    name) and  defaultnetwork id(which is same as network id provided
        #    in the Tier creation  i.e. step1)
        #    deployVM should be successful and  Vm added toTier  successfully.

        self.debug("Creating VM tier for account: %s" %
                                                    self.account.account.name)
        vm_tier = self.create_VM_Tier()

        self.debug("Adding instance to vm tier: %s" % vm_tier.name)
        vm = self.create_Instance(group=vm_tier.name)

        self.debug("Verifying if VM %s belongs to VM tier" % vm.name)
        self.validate_Vm_InstanceGroup(vms=[vm], group=vm_tier)
        return

    @attr(tags=["advanced", "advancedns"])
    @unittest.skip("Skip")
    def test_03_start_all_vms_from_vmtier(self):
        """Test start VMs beloging to the vmtier"""

        # 1. Create a VMTier
        # 2. Join the VM to Tier by Deploying a VM using default template,
        #    small service offering , small data disk offering,TierName(Group
        #    name) and  default network id(which is same as network id provided
        #    in the Tier creation  i.e. step1)
        #    deployVM should be successful and Vm added toTier successfully.
        # 3. Start all virtual machines in vm tier. VMs should be running

        self.debug("Creating VM tier for account: %s" %
                                                    self.account.account.name)
        vm_tier = self.create_VM_Tier()

        self.debug("Adding instance to vm tier: %s" % vm_tier.name)
        vm_1 = self.create_Instance(group=vm_tier.name, startvm=False)
        vm_2 = self.create_Instance(group=vm_tier.name, startvm=False)

        self.debug("Verifying if VM belongs to VM tier %s" % vm_tier.name)
        self.validate_Vm_InstanceGroup(vms=[vm_1, vm_2],
                                       group=vm_tier, state="Stopped")

        self.debug("Starting all VMs in vm tier: %s" % vm_tier.name)
        vm_tier.startInstances(self.apiclient)

        self.debug("Verifying VM state after starting")
        self.validate_Vm_InstanceGroup(vms=[vm_1, vm_2],
                                       group=vm_tier,
                                       state="Running")
        return

    @attr(tags=["advanced", "advancedns"])
    @unittest.skip("Skip")
    def test_04_stop_all_vms_from_vmtier(self):
        """Test stop all VM belonging to the vmtier"""

        # 1. Create a VMTier
        # 2. Join the VM to Tier by Deploying a VM using default template,
        #    small service offering , small data disk offering,TierName(Group
        #    name) and  defaultnetwork id(which is same as network id provided
        #    in the Tier creation  i.e. step1)
        #    deployVM should be successful and  Vm added toTier  successfully.
        # 3. Stop all virtual machines in vm tier. VMs should be stopped

        self.debug("Creating VM tier for account: %s" %
                                                    self.account.account.name)
        vm_tier = self.create_VM_Tier()

        self.debug("Adding instance to vm tier: %s" % vm_tier.name)
        vm_1 = self.create_Instance(group=vm_tier.name)
        vm_2 = self.create_Instance(group=vm_tier.name)

        self.debug("Verifying if VM belongs to VM tier %s" % vm_tier.name)
        self.validate_Vm_InstanceGroup(vms=[vm_1, vm_2],
                                       group=vm_tier, state="Running")

        self.debug("Stopping all VMs in vm tier: %s" % vm_tier.name)
        vm_tier.stopInstances(self.apiclient)

        self.debug("Verifying VM state after stopping")
        self.validate_Vm_InstanceGroup(vms=[vm_1, vm_2],
                                       group=vm_tier,
                                       state="Stopped")
        return

    @attr(tags=["advanced", "advancedns"])
    @unittest.skip("Skip")
    def test_05_reboot_all_vms_from_vmtier(self):
        """Test reboot all VM belonging to the vmtier"""

        # 1. Create a VMTier
        # 2. Join the VM to Tier by Deploying a VM using default template,
        #    small service offering , small data disk offering,TierName(Group
        #    name) and  defaultnetwork id(which is same as network id provided
        #    in the Tier creation  i.e. step1)
        #    deployVM should be successful and  Vm added toTier  successfully.
        # 3. Reboot all virtual machines in vm tier. VMs should be Running

        self.debug("Creating VM tier for account: %s" %
                                                    self.account.account.name)
        vm_tier = self.create_VM_Tier()

        self.debug("Adding instance to vm tier: %s" % vm_tier.name)
        vm_1 = self.create_Instance(group=vm_tier.name)
        vm_2 = self.create_Instance(group=vm_tier.name)

        self.debug("Verifying if VM belongs to VM tier %s" % vm_tier.name)
        self.validate_Vm_InstanceGroup(vms=[vm_1, vm_2],
                                       group=vm_tier, state="Running")

        self.debug("Rebooting all VMs in vm tier: %s" % vm_tier.name)
        vm_tier.rebootInstances(self.apiclient)

        self.debug("Verifying VM state after rebooting")
        self.validate_Vm_InstanceGroup(vms=[vm_1, vm_2],
                                       group=vm_tier,
                                       state="Running")
        return

    @attr(tags=["advanced", "advancedns"])
    @unittest.skip("Skip")
    def test_06_destroy_all_vms_from_vmtier(self):
        """Test destroy all VM belonging to the vmtier"""

        # 1. Create a VMTier
        # 2. Join the VM to Tier by Deploying a VM using default template,
        #    small service offering , small data disk offering,TierName(Group
        #    name) and  defaultnetwork id(which is same as network id provided
        #    in the Tier creation  i.e. step1)
        #    deployVM should be successful and  Vm added toTier  successfully.
        # 3. Destroy all virtual machines in vm tier. VMs should be Destroyed

        self.debug("Creating VM tier for account: %s" %
                                                    self.account.account.name)
        vm_tier = self.create_VM_Tier()

        self.debug("Adding instance to vm tier: %s" % vm_tier.name)
        vm_1 = self.create_Instance(group=vm_tier.name)
        vm_2 = self.create_Instance(group=vm_tier.name)

        self.debug("Verifying if VM belongs to VM tier %s" % vm_tier.name)
        self.validate_Vm_InstanceGroup(vms=[vm_1, vm_2],
                                       group=vm_tier, state="Running")

        self.debug("Destroying all VMs in vm tier: %s" % vm_tier.name)
        vm_tier.deleteInstances(self.apiclient)

        self.debug("Verifying VM state after destroy")
        self.validate_Vm_InstanceGroup(vms=[vm_1, vm_2],
                                       group=vm_tier,
                                       state="Destroyed")
        return

    @attr(tags=["advanced", "advancedns"])
    @unittest.skip("Skip")
    def test_07_recover_all_vms_from_vmtier(self):
        """Test recover all VM belonging to the vmtier"""

        # 1. Create a VMTier
        # 2. Join the VM to Tier by Deploying a VM using default template,
        #    small service offering , small data disk offering,TierName(Group
        #    name) and  defaultnetwork id(which is same as network id provided
        #    in the Tier creation  i.e. step1)
        #    deployVM should be successful and  Vm added toTier  successfully.
        # 3. Destroy all virtual machines in vm tier. VMs should be Destroyed
        # 4. Recover all virtual machines in vm tier. VMs should be Running

        self.debug("Creating VM tier for account: %s" %
                                                    self.account.account.name)
        vm_tier = self.create_VM_Tier()

        self.debug("Adding instance to vm tier: %s" % vm_tier.name)
        vm_1 = self.create_Instance(group=vm_tier.name)
        vm_2 = self.create_Instance(group=vm_tier.name)

        self.debug("Verifying if VM belongs to VM tier %s" % vm_tier.name)
        self.validate_Vm_InstanceGroup(vms=[vm_1, vm_2],
                                       group=vm_tier, state="Running")

        self.debug("Destroying all VMs in vm tier: %s" % vm_tier.name)
        vm_tier.deleteInstances(self.apiclient)

        self.debug("Verifying VM state after destroy")
        self.validate_Vm_InstanceGroup(vms=[vm_1, vm_2],
                                       group=vm_tier,
                                       state="Destroyed")

        self.debug("Recovering all VMs in vm tier: %s" % vm_tier.name)
        vm_tier.recoverInstances(self.apiclient)

        self.debug("Verifying VM state after recovering")
        self.validate_Vm_InstanceGroup(vms=[vm_1, vm_2],
                                       group=vm_tier,
                                       state="Running")
        return

    @attr(tags=["advanced", "advancedns"])
    @unittest.skip("Skip")
    def test_08_change_service_off_vms_from_vmtier(self):
        """Test change service offering of all VM belonging to the vmtier"""

        # 1. Create a VMTier
        # 2. Join the VM to Tier by Deploying a VM using default template,
        #    small service offering , small data disk offering,TierName(Group
        #    name) and  defaultnetwork id(which is same as network id provided
        #    in the Tier creation  i.e. step1)
        #    deployVM should be successful and  Vm added toTier  successfully.
        # 3. Change service offering of all virtual machines in vm tier.
        #    Service offering should be successfully changed

        self.debug("Creating VM tier for account: %s" %
                                                    self.account.account.name)
        vm_tier = self.create_VM_Tier()

        self.debug("Adding instance to vm tier: %s" % vm_tier.name)
        vm_1 = self.create_Instance(group=vm_tier.name)
        vm_2 = self.create_Instance(group=vm_tier.name)

        self.debug("Verifying if VM belongs to VM tier %s" % vm_tier.name)
        self.validate_Vm_InstanceGroup(vms=[vm_1, vm_2],
                                       group=vm_tier, state="Running")
        self.debug("Creating a service offering")
        service_offering = ServiceOffering.create(self.apiclient,
                                            self.services["service_offering"])

        # Adding service offering to cleanup
        self.cleanup.append(service_offering)

        self.debug("Changing service offering from %s to %s" %
                        (self.service_offering.name, service_offering.name))
        with self.assertRaises(Exception):
            vm_tier.changeServiceOffering(self.apiclient,
                                      serviceOfferingId=service_offering.id)
        self.debug("Change service offering failed as VM running in vm tier")

        self.debug("Stopping all VMs in vm tier: %s" % vm_tier.name)
        vm_tier.stopInstances(self.apiclient)

        self.debug("Verifying VM state after stop")
        self.validate_Vm_InstanceGroup(vms=[vm_1, vm_2],
                                       group=vm_tier,
                                       state="Stopped")
        self.debug("Changing service offering from %s to %s" %
                        (self.service_offering.name, service_offering.name))
        vm_tier.changeServiceOffering(self.apiclient,
                                      serviceOfferingId=service_offering.id)

        self.debug("Starting all VMs in vm tier: %s" % vm_tier.name)
        vm_tier.stopInstances(self.apiclient)

        self.debug("Verifying VM state after starting")
        self.validate_Vm_InstanceGroup(vms=[vm_1, vm_2],
                                       group=vm_tier,
                                       state="Running")
        return

    @attr(tags=["advanced", "advancedns"])
    @unittest.skip("Skip")
    def test_09_add_vm_multiple_networks(self):
        """Test Join the Vms to tier having more than 1 guest NW"""

        # Validate the following
        # 1. Create VMTier using createInstanceGroup by providing network id
        # 2. Join the VM to Tier by deploying the VM by providing Tiername as
        #    well providing additional GuestNetwrok.
        # 3. DeployVM should be successful and Joins to exiting VM Tier

        self.debug("Creating VM tier for account: %s" %
                                                    self.account.account.name)
        vm_tier = self.create_VM_Tier()

        self.debug("Create a guest network offering")

        nw_off = NetworkOffering.create(self.apiclient,
                                        self.services["network_offering"],
                                        conservemode=True)
        # Enable Network offering
        nw_off.update(self.apiclient, state='Enabled')
        nw_1 = self.create_Network(nw_off)
        nw_2 = self.create_Network(nw_off)

        self.debug("Adding instance to vm tier: %s" % vm_tier.name)
        vm_1 = self.create_Instance(group=vm_tier.name, networks=[nw_1.id,
                                                                  nw_2.id])

        self.debug("Verifying if VM belongs to VM tier %s" % vm_tier.name)
        self.validate_Vm_InstanceGroup(vms=[vm_1], group=vm_tier,
                                       state="Running")
        return

    @attr(tags=["advanced", "advancedns"])
    @unittest.skip("Skip")
    def test_10_start_stop_when_not_in_sync(self):
        """Test Start VMs in VM tier  when VMs state in Tier is not synch"""

        # Validate the following
        # 1. make sure Vms statein VM tier are not synch(I.e some Vms state are
        #    in stopped state and some VM s in Running state)
        # 2. Run startVM commond on Vms in Vmtier. All the VMs in the VM Tier
        #    should up and running state
        # 3. Run stop VM commond on Vms in VmTire. All the VMs in the VM Tier
        #    should be in Stopped state
        # 4. Run destroyVM commond on Vms in VmTire. All the VMs in the VM Tier
        #    should up destroyed
        # 5. Run rebootVirtualmachine commond on Vms in VmTire. Final Job
        #    should be failed with proper message

        self.debug("Creating VM tier for account: %s" %
                                                    self.account.account.name)
        vm_tier = self.create_VM_Tier()

        self.debug("Adding instance to vm tier: %s" % vm_tier.name)
        vm_1 = self.create_Instance(group=vm_tier.name)
        self.debug("Verifying if VM belongs to VM tier %s" % vm_tier.name)
        self.validate_Vm_InstanceGroup(vms=[vm_1], group=vm_tier,
                                       state="Running")

        vm_2 = self.create_Instance(group=vm_tier.name, startvm=False)
        self.debug("Verifying if VM belongs to VM tier %s" % vm_tier.name)
        self.validate_Vm_InstanceGroup(vms=[vm_2], group=vm_tier,
                                       state="Stopped")

        self.debug("Stopping all instances in vm tier: %s" % vm_tier.name)
        vm_tier.stopInstances(self.apiclient)

        self.debug("Verifying VM state after stop")
        self.validate_Vm_InstanceGroup(vms=[vm_1, vm_2], group=vm_tier,
                                       state="Stopped")
        self.debug("Stopping instance: %s" % vm_2.name)
        vm_2.stop(self.apiclient)
        self.validate_Vm_InstanceGroup(vms=[vm_2], group=vm_tier,
                                       state="Stopped")

        self.debug("Starting all VMs in vm tier: %s" % vm_tier.name)
        vm_tier.startInstances(self.apiclient)

        self.debug("Verifying VM state after stop")
        self.validate_Vm_InstanceGroup(vms=[vm_1, vm_2], group=vm_tier,
                                       state="Running")

        self.debug("Stopping instance: %s" % vm_2.name)
        vm_2.stop(self.apiclient)
        self.validate_Vm_InstanceGroup(vms=[vm_2], group=vm_tier,
                                       state="Stopped")

        self.debug("Rebooting all VMs in vm tier: %s" % vm_tier.name)
        vm_tier.rebootInstances(self.apiclient)

        self.debug("Verifying VM state after stop")
        self.validate_Vm_InstanceGroup(vms=[vm_1, vm_2], group=vm_tier,
                                       state="Running")

        self.debug("Stopping instance: %s" % vm_2.name)
        vm_2.stop(self.apiclient)
        self.validate_Vm_InstanceGroup(vms=[vm_2], group=vm_tier,
                                       state="Stopped")
        self.debug("Destroying all VMs in vm tier: %s" % vm_tier.name)
        vm_tier.deleteInstances(self.apiclient)

        self.debug("Verifying VM state after destroy")
        self.validate_Vm_InstanceGroup(vms=[vm_1, vm_2],
                                       group=vm_tier,
                                       state="Destroyed")
        return

    @attr(tags=["advanced", "advancedns"])
    @unittest.skip("Skip")
    def test_11_join_group(self):
        """Test Edit instance to join the Tier"""

        # Validate the following
        # 1. Deploy A VM
        # 2. Create VMTier using createInstanceGroup by providing network id
        # 3. Edit the Instance using updateVirtualMachine API to Join the VM to
        #    VMTier by updating value of group parameter
        # 4. VM Instance to be joined to VM Tier Successfully.

        self.debug("Creating VM tier for account: %s" %
                                                    self.account.account.name)
        vm_tier = self.create_VM_Tier()

        self.debug("Adding instance to vm tier: %s" % vm_tier.name)
        vm = self.create_Instance()
        self.debug("Adding instance %s to group %s" % (vm.name, vm_tier.name))
        self.add_Vm_To_InstanceGroup(vms=[vm], group=vm_tier)

        self.debug("Verifying if VM belongs to VM tier %s" % vm_tier.name)
        self.validate_Vm_InstanceGroup(vms=[vm], group=vm_tier,
                                       state="Running")
        return

    @attr(tags=["advanced", "advancedns"])
    @unittest.skip("Skip")
    def test_12_vpc_start_stop_instances(self):
        """Test start/stop all instances in VPC"""

        # Validate the following
        # 1.create a VPC
        # 2.create 2 Guest networks and attached VPC
        # 3.deployVms using the guest networks.
        # 4.startVms by passing the VPC VM tier name
        #   All the VMs in the VPC VM Tier should up and running state
        # 5.stopVms by passing the VPC VM tier name
        #   All the VMs in the VPC VM Tier should up and stopped state

        self.debug("Creating VPC offering for account: %s" %
                                                self.account.account.name)
        vpc = self.create_VPC()
        self.debug("Creating the network inside VPC: %s" % vpc.name)
        network_1 = self.create_Network(self.services["nw_off_vpc"], vpc=vpc)
        self.create_Instance(startvm=False, networks=[network_1.id])

        self.debug("Creating the network inside VPC: %s" % vpc.name)
        network_2 = self.create_Network(self.services["network_offering"],)
        self.create_Instance(networks=[network_2.id])

        self.debug("Starting all VMs in vm tier: %s" % vpc.name)
        cmd = startVirtualMachine.startVirtualMachineCmd()
        cmd.group = vpc.id
        self.apiclient.startVirtualMachine(cmd)

        self.debug("Fetching the details of vms running for account: %s" %
                                                    self.account.account.name)
        vms = VirtualMachine.list(self.apiclient,
                                 account=self.account.account.name,
                                 domainid=self.account.account.domainid,
                                 listall=True)
        self.assertIsInstance(vms, list, "Listvm should return valid response")

        for vm in vms:
            self.assertEqual(vm.state, "Running", "VM state should be running")

        self.debug("Stopping all VMs in the vm tier: %s" % vpc.name)
        cmd = stopVirtualMachine.stopVirtualMachineCmd()
        cmd.group = vpc.id
        self.apiclient.stopVirtualMachine(cmd)

        self.debug("Fetching the details of vms for account: %s" %
                                                    self.account.account.name)
        vms = VirtualMachine.list(self.apiclient,
                                 account=self.account.account.name,
                                 domainid=self.account.account.domainid,
                                 listall=True)
        self.assertIsInstance(vms, list, "Listvm should return valid response")

        for vm in vms:
            self.assertEqual(vm.state, "Stopped", "VM state should be stopped")
        return

    @attr(tags=["advanced", "advancedns"])
    @unittest.skip("Skip")
    def test_13_vpc_start_instances_diff_guest_nw(self):
        """Test start all instances deployed in different types of guest nw"""

        # Validate the following
        # 1.create a VPC
        # 2.create 2 Guest networks and attach only one to VPC
        # 3.deployVms using the guest networks.
        # 4.startVms by passing the VPC VM tier name
        #   All the VMs in the VPC VM Tier should up and running state

        self.debug("Creating VPC offering for account: %s" %
                                                self.account.account.name)
        vpc = self.create_VPC()
        self.debug("Creating the network inside VPC: %s" % vpc.name)
        network_1 = self.create_Network(self.services["nw_off_vpc"], vpc=vpc)
        self.debug("Creating the network inside VPC: %s" % vpc.name)
        network_2 = self.create_Network(self.services["network_offering"])

        self.debug("deploying instances in with different quest networks")
        self.create_Instance(startvm=False, networks=[network_1.id,
                                                      network_2.id])

        self.create_Instance(startvm=False, networks=[network_1.id,
                                                      network_2.id])

        self.debug("Starting all VMs in vm tier: %s" % vpc.name)
        cmd = startVirtualMachine.startVirtualMachineCmd()
        cmd.group = vpc.id
        self.apiclient.startVirtualMachine(cmd)

        self.debug("Fetching the details of vms running for account: %s" %
                                                    self.account.account.name)
        vms = VirtualMachine.list(self.apiclient,
                                 account=self.account.account.name,
                                 domainid=self.account.account.domainid,
                                 listall=True)
        self.assertIsInstance(vms, list, "Listvm should return valid response")

        for vm in vms:
            self.assertEqual(vm.state, "Running", "VM state should be running")
        return
