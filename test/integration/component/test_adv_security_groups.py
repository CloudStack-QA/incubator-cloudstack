""" P1 tests for shared networks
"""
# Import Local Modules
from nose.plugins.attrib import attr
from marvin.cloudstackTestCase import cloudstackTestCase, unittest
from marvin.integration.lib.base import (NetworkOffering,
                                         Network,
                                         Domain,
                                         Account,
                                         ServiceOffering,
                                         VirtualMachine,
                                         PhysicalNetwork,
                                         VpcOffering,
                                         VPC,
                                         Iso,
                                         Host,
                                         SecurityGroup)
from marvin.integration.lib.common import (get_domain,
                                           get_zone,
                                           get_template,
                                           cleanup_resources,
                                           wait_for_cleanup
                                           )
from marvin.cloudstackAPI import (deleteSecurityGroup)
import random


class Services:
    """ Test shared networks """

    def __init__(self):
        self.services = {
                        "domain": {
                            "name": "DOM",
                        },
                        "project": {
                            "name": "Project",
                            "displaytext": "Test project",
                        },
                        "account": {
                            "email": "user@test.com",
                            "firstname": "user",
                            "lastname": "user",
                            "username": "secgrp",
                            # Random characters are appended for unique name
                            "password": "fr3sca",
                        },
                        "service_offering": {
                            "name": "Tiny Instance",
                            "displaytext": "Tiny Instance",
                            "cpunumber": 1,
                            "cpuspeed": 100,    # in MHz
                            "memory": 128,    # In MBs
                        },
                        "network_offering": {
                            "name": 'MySharedOffering',
                            "displaytext": 'MySharedOffering',
                            "guestiptype": 'Shared',
                            "supportedservices": 'Dhcp,Dns,UserData',
                            "specifyVlan": "True",
                            "specifyIpRanges": "True",
                            "traffictype": 'GUEST',
                            "serviceProviderList": {
                                "Dhcp": 'VirtualRouter',
                                "Dns": 'VirtualRouter',
                                "UserData": 'VirtualRouter'
                            },
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
                        "network": {
                            "name": "MySharedNetwork - Test",
                            "displaytext": "MySharedNetwork",
                            "networkofferingid": "1",
                            "vlan": 1456,
                            "gateway": "172.16.15.1",
                            "netmask": "255.255.255.0",
                            "startip": "172.16.15.2",
                            "endip": "172.16.15.20",
                            "acltype": "Domain",
                            "scope": "all",
                            "startvLan": 600,
                            "endvLan": 700
                        },
                        "network1": {
                            "name": "MySharedNetwork - Test1",
                            "displaytext": "MySharedNetwork1",
                            "vlan": 1313,
                            "gateway": "172.16.15.1",
                            "netmask": "255.255.255.0",
                            "startip": "172.16.15.21",
                            "endip": "172.16.15.41",
                            "acltype": "Domain",
                            "scope": "all",
                        },
                        "isolated_network_offering": {
                            "name": 'Network offering',
                            "displaytext": 'Network offering',
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
                        "security_group": {
                            "name": 'SSH',
                            "protocol": 'TCP',
                            "startport": 22,
                            "endport": 22,
                            "cidrlist": '0.0.0.0/0',
                        },
                        "isolated_network": {
                            "name": "Isolated Network",
                            "displaytext": "Isolated Network",
                        },
                        "fw_rule": {
                            "startport": 22,
                            "endport": 22,
                            "cidr": '0.0.0.0/0',
                        },
                        "virtual_machine": {
                            "displayname": "Test VM",
                            "username": "root",
                            "password": "password",
                            "ssh_port": 22,
                            "hypervisor": 'XenServer',
                            # Hypervisor type should be same as
                            # hypervisor type of cluster
                            "privateport": 22,
                            "publicport": 22,
                            "protocol": 'TCP',
                        },
                        "ostype": 'CentOS 5.3 (64-bit)',
                        # Cent OS 5.3(64 bit)
                        "sleep": 90,
                        "timeout": 10,
                        "mode": 'advanced'
                    }


class TestSharedNetworks(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_client = super(TestSharedNetworks,
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
        cls.services["virtual_machine"]["template"] = cls.template.id

        cls.service_offering = ServiceOffering.create(
                                            cls.api_client,
                                            cls.services["service_offering"]
                                            )

        cls._cleanup = [
                        cls.service_offering,
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
        self.cleanup_networks = []
        self.cleanup_projects = []
        self.cleanup_accounts = []
        self.cleanup_domains = []
        self.cleanup_vms = []
        return

    def tearDown(self):
        # below components is not a part of cleanup because to mandate
        # the order and to cleanup network
        try:
            for vm in self.cleanup_vms:
                vm.delete(self.apiclient)
        except Exception as e:
            raise Exception(
                        "Exception during virtual machines cleanup: %s" % e)

        try:
            for project in self.cleanup_projects:
                project.delete(self.apiclient)
        except Exception as e:
            raise Exception("Warning:Exception during project cleanup: %s" % e)

        try:
            for account in self.cleanup_accounts:
                account.delete(self.apiclient)
        except Exception as e:
            raise Exception("Warning:Exception during project cleanup: %s" % e)

        try:
            for domain in self.cleanup_domains:
                domain.delete(self.apiclient)
        except Exception as e:
            raise Exception("Warning:Exception during project cleanup: %s" % e)

        # Wait till all resources created are cleaned up completely and
        # then attempt to delete Network
        wait_for_cleanup(self.apiclient, ["expunge.delay",
                                           "expunge.interval"])

        try:
            for network in self.cleanup_networks:
                network.delete(self.apiclient)
        except Exception as e:
            raise Exception("Warning:Exception during network cleanup: %s" % e)
        try:
            # Clean up, terminate the created network offerings
            cleanup_resources(self.apiclient, self.cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def create_Sec_Group(self, account):
        """Creates a custom security group"""

        self.debug("Creates a security group in account: %s" %
                                                    account.account.name)
        try:
            security_group = SecurityGroup.create(self.apiclient,
                                          self.services["security_group"],
                                          account=account.account.name,
                                          domainid=account.account.domainid)
        except Exception as e:
            self.fail("Failed to create security group: %s" % e)

        self.debug("Created security group with ID: %s" % security_group.id)

        sercurity_groups = SecurityGroup.list(self.apiclient,
                                            account=account.account.name,
                                            domainid=account.account.domainid)
        self.assertEqual(isinstance(sercurity_groups, list), True,
                         "Check for list security groups response")
        return security_group

    def create_Domain(self, parent='ROOT'):
        """Creates a domain"""

        self.debug("Finding parent domain information")
        domains = Domain.list(self.apiclient, name=parent, listall=True)

        self.assertIsInstance(domains, list,
                              "List domains should return a valid response")

        parent = domains[0]
        try:
            domain = Domain.create(self.apiclient,
                               services=self.services["domain"],
                               parentdomainid=parent.id)
        except Exception as e:
            self.fail("Failed to create domain : %s" % e)
        self.debug("Validating the domain created: %s" % domain.name)
        domains = Domain.list(self.apiclient, id=domain.id, listall=True)
        self.assertIsInstance(domains, list,
                              "List domains should return a valid response")
        return domain

    def create_NetworkOffering(self, services):
        """Create network offering"""

        # Create Network Offering
        nw_off = NetworkOffering.create(self.apiclient,
                                            services,
                                            conservemode=False)

        # Verify that the network offering got created
        nw_offs = NetworkOffering.list(self.apiclient, id=nw_off.id)
        self.assertIsInstance(nw_offs, list,
            "listNetworkOfferings returned invalid object in response")

        self.assertEqual(nw_offs[0].state, "Disabled",
            "The network offering created should be by default disabled.")

        # Update network offering state from disabled to enabled.
        nw_off.update(self.apiclient, state="enabled")
        # Verify that the state of the network offering is updated
        nw_offs = NetworkOffering.list(self.apiclient, id=nw_off.id)
        self.assertIsInstance(nw_offs, list,
            "listNetworkOfferings returned invalid object in response")
        self.assertEqual(nw_offs[0].state, "Enabled",
            "The network offering state should get updated to Enabled")
        return nw_off

    def get_Rand_vLan(self):
        vLan = random.sample(range(self.services["network"]["startvLan"],
                                    self.services["network"]["endvLan"]), 1)
        # TODO: Check if vLAN in use
        return vLan

    def create_Shared_Network(self, account, nw_off=None, acltype="Account",
                              subdomainaccess=None, services=None,
                              newApiClient=False):
        """Creates a network"""

        # There should be at least 1 physical network present in zone
        phy_nws = PhysicalNetwork.list(self.apiclient, zoneid=self.zone.id)
        self.assertIsInstance(phy_nws, list,
                "listPhysicalNetworks returned invalid object in response.")
        physical_network = phy_nws[0]
        self.debug("Physical network found: %s" % physical_network.id)

        if nw_off is None:
            self.debug("Creating network offering")
            nw_off = self.create_NetworkOffering(
                                services=self.services["network_offering"])
            self.cleanup.append(nw_off)
        self.debug("Creating shared network from network offering: %s" %
                                                                nw_off.name)
        # create network using the shared network offering created
        self.services["network"]["acltype"] = acltype
        self.services["network"]["physicalnetworkid"] = physical_network.id

        try:
            api_client = self.apiclient
            if newApiClient:
                self.debug("Creating API client for newly created user")
                api_client = self.testClient.createUserApiClient(
                                    UserName=account.account.name,
                                    DomainName=account.account.domain)
            if services is None:
                services = self.services["network"]
                services["vlan"] = self.get_Rand_vLan()[0]
                self.debug("VLAN used: %s" % str(services["vlan"]))
            network = Network.create(api_client, services,
                            accountid=account.account.name,
                            domainid=account.account.domainid,
                            networkofferingid=nw_off.id,
                            subdomainaccess=subdomainaccess,
                            zoneid=self.zone.id)
        except Exception as e:
            self.fail("Failed to create shared network: %s" % e)
        self.debug("Shared network created: %s" % network.name)
        return network

    def validate_Ingress_Rule(self, vm):
        self.debug("SSH into VM: %s" % vm.name)
        try:
            vm.get_ssh_client()
        except Exception as e:
            self.fail("SSH Access failed for %s: %s" % (vm.ipaddress, e))
        return

    def find_Suitable_Host(self, vm):
        """Returns a suitable host for VM migration"""

        try:
            hosts = Host.list(self.apiclient,
                              virtualmachineid=vm.id,
                              listall=True)
            self.assertIsInstance(hosts, list, "Failed to find suitable host")
            return hosts[0]
        except Exception as e:
            self.fail("Failed to find suitable host vm migration: %s" % e)
        return

    def validate_Shared_Network(self, network, state="Setup"):
        """Validates the shared network"""

        self.debug("Fetching list of networks with ID: %s" % network.id)
        networks = Network.list(self.apiclient, id=network.id, listall=True)
        self.assertIsInstance(networks, list,
                              "List networks should return avalid resposne")
        nw = networks[0]

        self.assertEqual(nw.state, state,
                         "network state should be implemented")
        return

    def create_Iso(self, account, services=None):
        """Creates an ISO in account"""

        self.debug("Registering a ISO in account: %s" % account.account.name)
        if services == None:
            services = self.services["iso"]
        iso = Iso.create(self.apiclient,
                         services,
                         account=self.account.account.name,
                         domainid=self.account.account.domainid)

        self.debug("Successfully created ISO with ID: %s" % iso.id)
        try:
            iso.download(self.apiclient)
        except Exception as e:
            self.fail("Exception while downloading ISO %s: %s"\
                      % (iso.id, e))
        return iso

    def configure_Ingress(self, account, sec_group, services=None):
        """Configures ingress rule for security group"""

        self.debug("Configuring ingress rule for security group: %s" %
                                                                sec_group.name)
        ingress_rule = sec_group.authorize(self.apiclient,
                                            services,
                                            account=account.account.name,
                                            domainid=account.account.domainid)
        self.assertEqual(isinstance(ingress_rule, dict), True,
                        "Check ingress rule created properly")
        return ingress_rule

    def create_Instance(self, account, startvm=True, networks=None,
                        sec_groups=None):
        """Creates an instance in account"""
        self.debug("Deploying an instance in account: %s" %
                                                    account.account.name)
        try:
            vm = VirtualMachine.create(
                                self.apiclient,
                                self.services["virtual_machine"],
                                templateid=self.template.id,
                                accountid=account.account.name,
                                domainid=account.account.domainid,
                                startvm=startvm,
                                networkids=networks,
                                securitygroupids=sec_groups,
                                serviceofferingid=self.service_offering.id)
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

    @attr(tags=["advancedsg"])
    def test_01_create_shared_account_spec_nw(self):
        """Test ADV zone SG enabled add 1 shared account specific network"""

        # Validate the following
        # 1. In ADV zone 1 SG enabled, create:Domain D1, account d1A
        #    domain-admin d1domain, user d1user
        # 2. add shared account specific network 1 for account d1A
        # In ADV zone SG enabled  shared account specific networks added

        self.debug("Creating a domain in zone: %s" % self.zone.name)
        domain = self.create_Domain()
        self.cleanup_domains.append(domain)
        self.debug("Creating account in domain: %s" % domain.name)
        account = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=domain.id)
        self.cleanup_accounts.append(account)
        self.debug("Creating shared network for account: %s" %
                                                        account.account.name)
        network = self.create_Shared_Network(account)
        self.debug("Verifying the shared network created: %s" % network.name)

        self.validate_Shared_Network(network)
        return

    @attr(tags=["advancedsg"])
    def test_02_create_shared_domain_spec_nw(self):
        """Test ADV zone SG enabled add 1 shared domain wide network with
            sub-domain access set to true """

        # Validate the following
        # 1. In ADV zone 1 SG enabled, create:Domain D1, account d1A
        #    domain-admin d1domain, user d1user
        # 2. Add shared domain wide  network nw1 with subdomain access set to
        #    true for domain D1
        #    In ADV zone SG enabled  shared domain wide networks added

        self.debug("Creating a domain in zone: %s" % self.zone.name)
        domain = self.create_Domain()
        self.cleanup_domains.append(domain)
        self.debug("Creating account in domain: %s" % domain.name)
        account = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=domain.id)
        self.cleanup_accounts.append(account)

        self.debug("Creating domain wide shared network for account: %s" %
                                                        account.account.name)
        network = self.create_Shared_Network(account, acltype="Domain",
                                             subdomainaccess=True)
        self.debug("Verifying the shared network created: %s" % network.name)

        self.validate_Shared_Network(network)
        self.cleanup_networks.append(network)
        return

    @attr(tags=["advancedsg"])
    def test_03_create_zone_wide_shared_nw(self):
        """Test ADV zone SG enabled add multiple shared zone wide network
            per zone"""

        # Validate the following
        # 1. In ADV zone 1 SG enabled add 3 shared zone wide networks
        #    z1znetwork1, z1znetwork2, z1znetwork3
        # 2. In each ADV zone SG enabled multiple shared zone wide networks
        #    added

        self.debug("Creating a domain in zone: %s" % self.zone.name)
        domain = self.create_Domain()
        self.cleanup_domains.append(domain)
        self.debug("Creating account in domain: %s" % domain.name)
        account = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=domain.id)
        self.cleanup_accounts.append(account)

        self.debug("Creating domain wide shared network for account: %s" %
                                                        account.account.name)
        network_1 = self.create_Shared_Network(account, acltype="Domain")
        network_2 = self.create_Shared_Network(account, acltype="Domain")
        self.debug("Verifying the shared network created: %s" % network_1.name)
        self.validate_Shared_Network(network_1)
        self.debug("Verifying the shared network created: %s" % network_2.name)
        self.validate_Shared_Network(network_2)

        # Cleanup the networks created
        self.cleanup_networks.append(network_1)
        self.cleanup_networks.append(network_2)
        return

    @attr(tags=["advancedsg"])
    def test_04_create_multi_shared_account_spec_nw(self):
        """Test ADV zone SG enabled add multiple shared account specific
            networks per zone"""

        # Validate the following
        # 1. In ADV zone 1 SG enabled, create multiple domains and accounts
        # 2. add shared account specific networks for accounts
        # In ADV zone SG enabled  shared account specific networks added

        for x in range(3):
            self.debug("Creating a domain in zone: %s" % self.zone.name)
            domain = self.create_Domain()
            self.cleanup_domains.append(domain)
            self.debug("Creating account in domain: %s" % domain.name)
            account = Account.create(self.apiclient, self.services["account"],
                                     admin=True, domainid=domain.id)
            self.cleanup_accounts.append(account)
            self.debug("Creating shared network for account: %s" %
                                                        account.account.name)
            network = self.create_Shared_Network(account)
            self.debug("Verifying the shared network created: %s" %
                                                                network.name)
            self.validate_Shared_Network(network)
        return

    @attr(tags=["advancedsg"])
    def test_05_create_multi_shared_domain_spec_nw(self):
        """Test ADV zone SG enabled add multiple shared domain wide network
            with sub-domain access set to true for domain per zone"""

        # Validate the following
        # 1. In ADV zone 1 SG enabled create multiple domain wide networks
        # 2. Add shared domain wide  network nw1 with sub-domain access set to
        #    true for domain D1
        #    In ADV zone SG enabled  shared domain wide networks added

        for x in range(3):
            self.debug("Creating a domain in zone: %s" % self.zone.name)
            domain = self.create_Domain()
            self.cleanup_domains.append(domain)
            self.debug("Creating account in domain: %s" % domain.name)
            account = Account.create(self.apiclient, self.services["account"],
                                     admin=True, domainid=domain.id)
            self.cleanup_accounts.append(account)

            self.debug("Creating domain wide shared network for account: %s" %
                                                        account.account.name)
            network = self.create_Shared_Network(account, acltype="Domain",
                                                 subdomainaccess=True)
            self.debug("Verifying the shared network created: %s" %
                                                                network.name)

            self.validate_Shared_Network(network)
            self.cleanup_networks.append(network)
        return

    @attr(tags=["advancedsg"])
    def test_06_create_isolated_nw(self):
        """Test create isolated networks in Advanced security group zone"""

        # Validate the following
        # 1. Try to create isolated network in advanced security group zone
        # 2. Network creation should fail with proper exception

        self.debug("Creating account in domain: %s" % self.domain.name)
        account = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=self.domain.id)
        self.cleanup_accounts.append(account)
        self.debug("Creating isolated network for account: %s" %
                                                    account.account.name)

        nw_off = NetworkOffering.create(self.apiclient,
                                    self.services["isolated_network_offering"])
        nw_off.update(self.apiclient, state="Enabled")
        self.cleanup.append(nw_off)
        with self.assertRaises(Exception):
            Network.create(self.apiclient,
                           self.services["network"],
                           accountid=account.account.name,
                           domainid=account.account.domainid,
                           zoneid=self.zone.id)
        return

    @attr(tags=["advancedsg"])
    def test_07_create_vpc(self):
        """Test ADV zone SG enabled VPC networks not supported"""

        # Validate the following
        # 1. In ADV zone 1 SG enabled, add VPC network
        # 2. In ADV zone 1 SG enabled, add VPC network fail

        self.debug("Creating account in domain: %s" % self.domain.name)
        account = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=self.domain.id)
        self.cleanup_accounts.append(account)

        self.debug("Creating a VPC offering in zone: %s" % self.zone.name)
        vpc_off = VpcOffering.create(self.apiclient,
                                     self.services["vpc_offering"])
        self.debug("Enabling the VPC offering created")
        vpc_off.update(self.apiclient, state='Enabled')

        self.cleanup.append(vpc_off)
        self.debug("Creating a VPC network in the account: %s" %
                                                        account.account.name)
        with self.assertRaises(Exception):
            VPC.create(
                        self.apiclient,
                        self.services["vpc"],
                        vpcofferingid=vpc_off.id,
                        zoneid=self.zone.id,
                        account=account.account.name,
                        domainid=account.account.domainid
                        )
        return

    @attr(tags=["advancedsg"])
    def test_08_create_network_normal_user(self):
        """Test In advance zone SG enabled, only admin allowed to create
            guest networks"""

        # Validate the following
        # 1. Create Advance  zone SG enabled
        # 2. Add domain d1 domain admin d1domain acct d1domainA
        #    Add domain d2 user d2user, acct d2userA
        # 3. login d1domain try add guest network via API
        #    No provision in UI  for d1domain to add guest network
        # 4. login d2user try add guest network via API
        #    No provision in UI  for d2user to add guest network

        self.debug("Creating normal account in domain: %s" % self.domain.name)
        account = Account.create(self.apiclient, self.services["account"],
                                 admin=False, domainid=self.domain.id)
        self.cleanup_accounts.append(account)
        self.debug("Creating shared network for account: %s" %
                                                        account.account.name)
        with self.assertRaises(Exception):
            self.create_Shared_Network(account, acltype="Account",
                                       newApiClient=True)
        self.debug("Shared network cannot be created by normal user")
        return

    @attr(tags=["advancedsg"])
    def test_09_create_shared_nw_reuse_vpc(self):
        """Test Admin should be allowed to add a Shared Network with a Vlan Id
            that is already associated with another Shared network."""

        # Validate the following
        # 1. As Admin, create a shared network with vlan id say 123
        # 2. As Admin, try to create shared network with same vlanid 123
        #    User should be allowed to create this network.

        self.debug("Creating a domain in zone: %s" % self.zone.name)
        domain = self.create_Domain()
        self.cleanup_domains.append(domain)
        self.debug("Creating account in domain: %s" % domain.name)
        account = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=domain.id)
        self.cleanup_accounts.append(account)

        self.debug("Creating domain wide shared network for account: %s" %
                                                        account.account.name)
        network_1 = self.create_Shared_Network(account, acltype="Domain")
        network_2 = self.create_Shared_Network(account, acltype="Domain")
        self.debug("Verifying the shared network created: %s" % network_1.name)
        self.validate_Shared_Network(network_1)
        self.debug("Verifying the shared network created: %s" % network_2.name)
        self.validate_Shared_Network(network_2)

        # Cleanup the networks created
        self.cleanup_networks.append(network_1)
        self.cleanup_networks.append(network_2)
        return

    @attr(tags=["advancedsg"])
    def test_10_create_shared_nw_invalid_param(self):
        """Test Admin should not be allowed to add a Shared Network without
            specifying  a Vlan Id ,Guest Gateway,Guest Netmask,Guest start IP,
            Guest End IP"""

        # Validate the following
        # 1. As Admin, create a shared network with out specifying Vlan Id,
        #    Guest Gateway,Guest Netmask,Guest start IP,Guest End IP
        # 2. User should not be allowed to create this network.He should be
        #    forced to add all the required values.Following error message is
        #    presented to the user "StartIp/endIp/gateway/netmask are required
        #    when create network of type Shared and network of type Isolated
        #    with service SourceNat disabled"

        self.debug("Creating a domain in zone: %s" % self.zone.name)
        domain = self.create_Domain()
        self.cleanup_domains.append(domain)
        self.debug("Creating account in domain: %s" % domain.name)
        account = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=domain.id)
        self.cleanup_accounts.append(account)

        self.debug("Creating shared network without specifying VLAN ID")
        network_config = self.services["network"]
        self.debug("Removing VLAN ID from network config")
        del network_config["vlan"]

        with self.assertRaises(Exception):
            self.create_Shared_Network(account, acltype="Domain",
                                                    services=network_config)
        self.debug("Creating shared network without guest gateway")
        network_config = self.services["network"]
        self.debug("Removing gateway from network config")
        del network_config["gateway"]
        with self.assertRaises(Exception):
            self.create_Shared_Network(account, acltype="Domain",
                                                    services=network_config)

        self.debug("Creating shared network without guest netmask")
        network_config = self.services["network"]
        self.debug("Removing netmask from network config")
        del network_config["netmask"]
        with self.assertRaises(Exception):
            self.create_Shared_Network(account, acltype="Domain",
                                                    services=network_config)

        self.debug("Creating shared network without guest start IP")
        network_config = self.services["network"]
        self.debug("Removing startip from network config")
        del network_config["startip"]
        with self.assertRaises(Exception):
            self.create_Shared_Network(account, acltype="Domain",
                                                    services=network_config)

        self.debug("Creating shared network without guest end IP")
        network_config = self.services["network"]
        self.debug("Removing endip from network config")
        del network_config["endip"]
        with self.assertRaises(Exception):
            self.create_Shared_Network(account, acltype="Domain",
                                                    services=network_config)
        return

    @attr(tags=["advancedsg"])
    def test_11_create_shared_nw_reuse_zone_vlan(self):
        """Test Admin should be allowed to add a Shared Network with a VlanId
            that is already associated with Zone vlan"""

        # Validate the following
        # 1. As Admin, create a shared network by providing a vlan that is part
        #    of Zone Vlan.
        # 2. User should be allowed to create this network.

        self.debug("Creating a domain in zone: %s" % self.zone.name)
        domain = self.create_Domain()
        self.cleanup_domains.append(domain)
        self.debug("Creating account in domain: %s" % domain.name)
        account = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=domain.id)
        self.cleanup_accounts.append(account)

        self.debug("Creating domain wide shared network for account: %s" %
                                                        account.account.name)
        network_1 = self.create_Shared_Network(account, acltype="Domain")
        network_2 = self.create_Shared_Network(account, acltype="Account")
        self.debug("Verifying the shared network created: %s" % network_1.name)
        self.validate_Shared_Network(network_1)
        self.debug("Verifying the shared network created: %s" % network_2.name)
        self.validate_Shared_Network(network_2)

        # Cleanup the networks created
        self.cleanup_networks.append(network_1)
        return

    @attr(tags=["advancedsg"])
    def test_12_deploy_vm_multiple_phy_nws(self):
        """Test DeployVM on Adv zone SG enabled  shared nw in with more than 1
            physical network"""

        # Validate the following
        # 1. ADV zone  SG enabled. make sure that shared GuestNetwork is
        #    present on PhysicalNetwork0(Nic0)
        # 2. While setting up, create more than 1 physical network with
        #    different traffic labels  (Ex:- PhysicalNetwork1 -> Label as NIC1,
        #    PhysicalNetwork2 -> Label as NIC0). VM deployment should be
        #    successful without  any issues and the communication is fine.
        # 3. deploy VMs in physicalNetwork0 (Nic0)

        self.debug("Fetching the number of physical networks in zone: %s" %
                                                                self.zone.name)
        # There should be at least 1 physical network present in zone
        phy_nws = PhysicalNetwork.list(self.apiclient, zoneid=self.zone.id)
        self.assertIsInstance(phy_nws, list,
                "listPhysicalNetworks returned invalid object in response.")

        names = []
        for phy_nw in phy_nws:
            names.append(phy_nw.name)
        if len(phy_nws) < 2:
            raise unittest.SkipTest(
                            "Test requires atleast 2 physical networks")
        else:
            for name in names:
                if name.lower().count("nic") == 0:
                    raise unittest.SkipTest(
                            "Test requires physical networks named as NIC-X")

        self.debug("Creating a domain in zone: %s" % self.zone.name)
        domain = self.create_Domain()
        self.cleanup_domains.append(domain)
        self.debug("Creating account in domain: %s" % domain.name)
        account = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=domain.id)
        self.cleanup_accounts.append(account)

        network = self.create_Shared_Network(account, acltype="Account")
        self.debug("Verifying the shared network created: %s" % network.name)

        self.validate_Shared_Network(network)
        return

    @attr(tags=["advancedsg"])
    def test_13_deply_vm_in_zone_wide_nw(self):
        """Test ADV zone SG enabled multiple shared nw zone wide, Only Users in
            any account of any domain in that zone allowed to deploy VMs to
            that shared nw"""

        # Validate the following
        # 1. Create ADV zone 1 SG enabled , ADV zone 2 SG enabled
        # 2. zone 1 Add domain d1 domainadmin d1domain account d1domainA,
        #    domain d2 user d2user  acct d2userA. zone 2 Add domain d3
        #    domainadmin d3domain account d3domainA,  domain d4 user d4user
        #    acct d4userA
        # 3. Create shared nw1  and nw2 zone wide  for zone 1
        # 4. Deploy VMs in both the networks from any account

        self.debug("Creating a domain in zone: %s" % self.zone.name)
        domain_1 = self.create_Domain()
        self.cleanup_domains.append(domain_1)
        self.debug("Creating account in domain: %s" % domain_1.name)
        account_1 = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=domain_1.id)
        self.cleanup_accounts.append(account_1)

        self.debug("Creating a domain in zone: %s" % self.zone.name)
        domain_2 = self.create_Domain()
        self.cleanup_domains.append(domain_2)
        self.debug("Creating account in domain: %s" % domain_2.name)
        account_2 = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=domain_2.id)
        self.cleanup_accounts.append(account_2)

        self.debug("Creating domain wide shared network for account: %s" %
                                                        account_1.account.name)
        network_1 = self.create_Shared_Network(account_1, acltype="Domain")
        network_2 = self.create_Shared_Network(account_2, acltype="Domain")
        self.debug("Verifying the shared network created: %s" % network_1.name)
        self.validate_Shared_Network(network_1)
        self.debug("Verifying the shared network created: %s" % network_2.name)
        self.validate_Shared_Network(network_2)

        # Cleanup the networks created
        self.cleanup_networks.append(network_1)
        self.cleanup_networks.append(network_2)

        self.debug("Deplying VMs in the networks: %s & %s" % (network_1.name,
                                                              network_2.name))
        self.create_Instance(account=account_1, networks=[network_1.id])
        self.create_Instance(account=account_2, networks=[network_2.id])
        return

    @attr(tags=["advancedsg"])
    def test_14_deply_vm_in_account_wide_nw(self):
        """Test ADV zone SG enabled multiple shared nw account specific,
            Only Users in that account allowed to deploy VMs to that shared
            network"""

        # Validate the following
        # 1. Create ADV zone 1 SG enabled , ADV zone 2 SG enabled
        # 2. zone 1 Add domain d1 domainadmin d1domain account d1domainA,
        #    domain d2 user d2user  acct d2userA. zone 2 Add domain d3
        #    domainadmin d3domain account d3domainA,  domain d4 user d4user
        #    acct d4userA
        # 3. Create shared nw1  scope account, account d1domainA
        #    Create shared nw2  scope account, account d1userA
        #    Create shared nw3  scope account, account d2userA
        #    shared networks account specific nw1, nw2, nw3 added. Admin
        #    should not be able to add VM to any nw

        self.debug("Creating a domain in zone: %s" % self.zone.name)
        domain_1 = self.create_Domain()
        self.cleanup_domains.append(domain_1)
        self.debug("Creating account in domain: %s" % domain_1.name)
        account_1 = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=domain_1.id)
        self.cleanup_accounts.append(account_1)

        self.debug("Creating a domain in zone: %s" % self.zone.name)
        domain_2 = self.create_Domain()
        self.cleanup_domains.append(domain_2)
        self.debug("Creating account in domain: %s" % domain_2.name)
        account_2 = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=domain_2.id)
        self.cleanup_accounts.append(account_2)

        self.debug("Creating another account in domain: %s" % domain_2.name)
        account_3 = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=domain_2.id)
        self.cleanup_accounts.append(account_3)

        self.debug("Creating account wide shared network for account: %s" %
                                                        account_1.account.name)
        network_1 = self.create_Shared_Network(account_1, acltype="Account")
        network_2 = self.create_Shared_Network(account_2, acltype="Account")
        network_3 = self.create_Shared_Network(account_2, acltype="Account")

        self.debug("Verifying the shared network created: %s" % network_1.name)
        self.validate_Shared_Network(network_1)
        self.debug("Verifying the shared network created: %s" % network_2.name)
        self.validate_Shared_Network(network_2)
        self.debug("Verifying the shared network created: %s" % network_3.name)
        self.validate_Shared_Network(network_3)

        self.debug(
            "Deplying VMs in the networks %s, %s & %s" % (network_1.name,
                                                          network_2.name,
                                                          network_3.name))
        vm = self.create_Instance(account=account_1, networks=[network_1.id])
        self.cleanup_vms.append(vm) 
        vm = self.create_Instance(account=account_2, networks=[network_2.id])
        self.cleanup_vms.append(vm) 
        return

    @attr(tags=["advancedsg"])
    @unittest.skip("Work in progress")
    def test_15_deply_vm_in_domain_wide_nw(self):
        """Test ADV zone SG enabled multiple shared nw domain wide, Only Users
        in accounts of that domain allowed to deploy VMs to that shared nw"""

        # Validate the following
        # 1. Create ADV zone 1 SG enabled , ADV zone 2 SG enabled
        # 2. zone 1 Add domain d1 domainadmin d1domain account d1domainA,
        #    domain d2 user d2user  acct d2userA. zone 2 Add domain d3
        #    domainadmin d3domain account d3domainA,  domain d4 user d4user
        #    acct d4userA
        # 3. Create shared nw1 domain wide domain d1
        #    Create shared nw2  domain wide domain d1
        #    Create shared nw3  domain wide domain d2
        #    shared networks domain wide nw1, nw2, nw3 added. Admin
        #    should not be able to add VM to any nw

        self.debug("Creating a domain in zone: %s" % self.zone.name)
        domain_1 = self.create_Domain()
        self.cleanup_domains.append(domain_1)
        self.debug("Creating account in domain: %s" % domain_1.name)
        account_1 = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=domain_1.id)
        self.cleanup_accounts.append(account_1)

        self.debug("Creating a domain in zone: %s" % self.zone.name)
        domain_2 = self.create_Domain()
        self.cleanup_domains.append(domain_2)
        self.debug("Creating account in domain: %s" % domain_2.name)
        account_2 = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=domain_2.id)
        self.cleanup_accounts.append(account_2)

        self.debug("Creating domain wide shared network for account: %s" %
                                                        account_1.account.name)
        network_1 = self.create_Shared_Network(account_1, acltype="Domain")
        network_2 = self.create_Shared_Network(account_2, acltype="Domain")

        self.debug("Verifying the shared network created: %s" % network_1.name)
        self.validate_Shared_Network(network_1)
        self.debug("Verifying the shared network created: %s" % network_2.name)
        self.validate_Shared_Network(network_2)

        self.debug(
            "Deplying VMs in the networks %s & %s" % (network_1.name,
                                                          network_2.name))
        vm = self.create_Instance(account=account_1, networks=[network_1.id])
        self.cleanup_vms.append(vm)
        vm = self.create_Instance(account=account_2, networks=[network_2.id])
        self.cleanup_vms.append(vm)
        return

    @attr(tags=["advancedsg"])
    @unittest.skip("Work in progress")
    def test_16_delete_account(self):
        """Test -In advance zone SG enabled, delete account which has shared
            networks scope account """

        # Steps for validation
        # 1. Create Advance  zone SG enabled
        # 2. Add domain d1 user d1domain acct d1domainA role domainadmin domain
        #    d2 userd2user acct d2userA role user
        # 3. Create a guest networks scope account account d1domainA with
        #    network offering shared
        # 4. Create a guest networks scope account account d2userA with network
        #    offering shared
        # 5. login d1domain  create VMs. loout. login admin delete account
        #    d1domainA
        # Validate the follwing
        # 1. guest netowork for account d1domainA added
        # 2. guest netowork for account d2userA added
        # 3. account d1domainA, all its VMs, shared networks deleted

        self.debug("Creating a domain in zone: %s" % self.zone.name)
        domain_1 = self.create_Domain()
        self.cleanup_domains.append(domain_1)
        self.debug("Creating account in domain: %s" % domain_1.name)
        account_1 = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=domain_1.id)
        self.cleanup_accounts.append(account_1)

        self.debug("Creating a domain in zone: %s" % self.zone.name)
        domain_2 = self.create_Domain()
        self.cleanup_domains.append(domain_2)
        self.debug("Creating account in domain: %s" % domain_2.name)
        account_2 = Account.create(self.apiclient, self.services["account"],
                                   admin=False, domainid=domain_2.id)
        self.cleanup_accounts.append(account_2)

        self.debug("Creating account wide shared network for account: %s" %
                                                        account_1.account.name)
        network_11 = self.create_Shared_Network(account_1, acltype="Account")

        self.debug("Verifying the shared network created: %s" % network_11.name)
        self.validate_Shared_Network(network_11)

        self.debug("Creating account wide shared network for account: %s" %
                                                        account_2.account.name)
        network_21 = self.create_Shared_Network(account_2, acltype="Account")

        self.debug("Verifying the shared network created: %s" %
                                                            network_21.name)
        self.validate_Shared_Network(network_21)

        # Cleanup the networks created
        self.cleanup_networks.append(network_11)
        self.cleanup_networks.append(network_21)

        self.debug("Deplying VMs in the networks %s & %s" % network_21.name)
        self.create_Instance(account=account_2, networks=[network_21.id])

        self.debug("Creating API client for user: %s" % account_1.account.name)
        api_client = self.testClient.createUserApiClient(
                                    UserName=account_1.account.name,
                                    DomainName=account_1.account.domain)
        self.debug("Deleting account %s from account %s" %
                                        (account_2.account.name,
                                         account_1.account.name))
        try:
            account_2.delete(api_client)
        except Exception as e:
            self.fail("Failed to delete account: %s" % e)
        return

    @attr(tags=["advancedsg"])
    @unittest.skip("Work in progress")
    def test_17_deploy_vm_custom_sec_group(self):
        """Test - DeployVM with CustomSG with shared network"""

        # Steps for validation
        # 1. Create SG enabled Advance zone
        # 2. create a  custmer network offering with SG
        # 3. Create Shared GuestNetwork
        # 4. deployVM by passing  custom SG id and Shared network ID.
        # 5. deployVM by passing first SG enabled Advanced Zone ID
        # Validate the following
        # 1. VM deployment should be successful
        # 2. its should fail  and shows error messge like "errortext":
        #    Only support one network per VM if security group enabled"

        self.debug("Creating account in domain: %s" % self.domain.name)
        account = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=self.domain.id)
        self.cleanup_accounts.append(account)
        self.debug("Create a security group in account %s" %
                                                        account.account.name)

        sec_group = self.create_Sec_Group(account=account)

        self.debug("Creating account wide shared network for account: %s" %
                                                        account.account.name)
        network = self.create_Shared_Network(account, acltype="Account")

        self.debug("Verifying the shared network created: %s" % network.name)
        self.validate_Shared_Network(network)

        # Cleanup the networks created
        self.cleanup_networks.append(network)

        self.debug("Deplying VMs in the networks %s & %s" % network.name)
        self.create_Instance(account=account, networks=[network.id],
                             sec_grps=[sec_group.id])

        self.debug("Creating account wide shared network for account: %s" %
                                                        account.account.name)
        network_2 = self.create_Shared_Network(account, acltype="Account")

        self.debug("Verifying the shared network created: %s" % network_2.name)
        self.validate_Shared_Network(network_2)
        self.cleanup_networks.append(network_2)
        self.debug("Deplying VMs in 2 networks %s & %s with sec groups" %
                                                (network.name, network_2.name))

        with self.assertRaises(Exception):
            self.create_Instance(account=account,
                                 networks=[network.id, network_2.id],
                                 sec_grps=[sec_group.id])
        return

    @attr(tags=["advancedsg"])
    @unittest.skip("Work in progress")
    def test_18_deploy_vm_multiple_shared_nws(self):
        """Test-Deplpoy VM with more than 1 Nic  with shared networks"""

        # Steps for validation
        # 1. Deply vm in multiple shared networks in adv sec group zone
        # Validate the following
        # 1. Deploy VM should be successful

        self.debug("Creating account in domain: %s" % self.domain.name)
        account = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=self.domain.id)
        self.cleanup_accounts.append(account)

        self.debug("Creating account wide shared network for account: %s" %
                                                        account.account.name)
        network = self.create_Shared_Network(account, acltype="Account")

        self.debug("Verifying the shared network created: %s" % network.name)
        self.validate_Shared_Network(network)

        # Cleanup the networks created
        self.cleanup_networks.append(network)

        self.debug("Creating account wide shared network for account: %s" %
                                                        account.account.name)
        network_2 = self.create_Shared_Network(account, acltype="Account")

        self.debug("Verifying the shared network created: %s" % network_2.name)
        self.validate_Shared_Network(network_2)
        self.cleanup_networks.append(network_2)
        self.debug("Deplying VMs in 2 networks %s & %s" %
                                                (network.name, network_2.name))
        self.create_Instance(account=account, networks=[network.id,
                                                        network_2.id])
        return

    @attr(tags=["advancedsg"])
    @unittest.skip("Work in progress")
    def test_19_network_rules_with_vm_start_stop(self):
        """Test-Stop/Start/reboot/destroy/restore/expunge the VMs"""

        # Steps for validation
        # 1. Create an account
        # 2. Using this account, Deploy few Vms in the "Zone wide shared SG
        #    enabled" network
        # 3. Add a TCP ingress rule  for a port range (22-80) for any ipaddress
        #    (cidr2).
        # 4. Deploy vms inthis network
        # 5. access the VM using Guest IP
        # 6. stop and start the VM
        # 7. Reboot  the VM
        # 8. Destroy and resore VM
        # 9. Migrate VM to another host
        # 10. Destroy and expunge VM
        # Validate the following
        # 7. VM should be Up and running, all the rules existing rules should
        #    programmed correctly
        # 10. All the rules belongs to expunged VM should be removed/free

        self.debug("Creating account in domain: %s" % self.domain.name)
        account = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=self.domain.id)
        self.cleanup_accounts.append(account)
        self.debug("Creating account wide shared network for account: %s" %
                                                        account.account.name)
        network = self.create_Shared_Network(account, acltype="Domain")
        self.debug("Create a security group in account %s" %
                                                        account.account.name)
        sec_group = self.create_Sec_Group(account=account)

        self.debug("Verifying the shared network created: %s" % network.name)
        self.validate_Shared_Network(network)
        self.cleanup_networks.append(network)

        self.debug("Deplying VMs in network %s" % network.name)
        vm = self.create_Instance(account=account, networks=[network.id],
                            sec_groups=sec_group)
        self.debug("Creating and configuring ingress rules")
        self.configure_Ingress(account, sec_group, self.services["ingress"])

        self.debug("Stopping the instance: %s" % vm.name)
        vm.stop(self.apiclient)
        self.debug("Starting the instance: %s" % vm.name)
        vm.start(self.apiclient)
        self.debug("Checking if VM is still accessible?")
        self.validate_Ingress_Rule(vm)
        self.debug("Reboot the instance: %s" % vm.name)
        vm.reboot(self.apiclient)
        self.debug("Checking if VM is still accessible?")
        self.validate_Ingress_Rule(vm)

        self.debug("Destroy the instance: %s" % vm.name)
        vm.delete(self.apiclient)
        self.debug("Recovering the instance: %s" % vm.name)
        vm.recover(self.apiclient)
        self.debug("Checking if VM is still accessible?")
        self.validate_Ingress_Rule(vm)

        host = self.find_Suitable_Host(vm)
        self.debug("Migrating instance: %s to host: %s" % (vm.name, host.name))
        try:
            vm.migrate(self.apiclient, host.id)
        except Exception as e:
            self.fail("Failed to migrate instance: %s" % e)
        self.validate_Ingress_Rule(vm)

        self.debug("Destroy the instance: %s" % vm.name)
        vm.delete(self.apiclient)

        self.debug("Waiting for expunge interval")
        wait_for_cleanup(self.apiclient, ["expunge.delay",
                                           "expunge.interval"])
        with self.assertRaises(Exception):
            vm.get_ssh_client()
        return

    @attr(tags=["advancedsg"])
    @unittest.skip("Work in progress")
    def test_20_create_network_without_vlan(self):
        """Test Check creation of default SG enable network without VLAN"""

        # Steps for validation
        # 1. Check creation of default SG enable network without VLAN
        # Validate the following
        # 1. Creation shoud be failed with proper error message

        self.debug("Creating account in domain: %s" % self.domain.name)
        account = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=self.domain.id)
        self.cleanup_accounts.append(account)
        self.debug("Creating shared network for account: %s without vlan" %
                                                        account.account.name)
        services = {"name": "MySharedNetwork - Test",
                    "displaytext": "MySharedNetwork",
                    "gateway": "172.16.15.1",
                    "netmask": "255.255.255.0",
                    "startip": "172.16.15.2",
                    "endip": "172.16.15.20",
                    "acltype": "Domain",
                    "scope": "all"}
        with self.assertRaises(Exception):
            self.create_Shared_Network(account, acltype="Account",
                                       services=services)
        return

    @attr(tags=["advancedsg"])
    @unittest.skip("Work in progress")
    def test_21_delete_default_sec_group(self):
        """Test Delete the default security groups"""

        # Steps for validation
        # 1. Delete the default SG
        # Validate the following
        # 1. Delete SG group should be successful if no VMS asiiocated with
        #    default SG

        self.debug("Creating account in domain: %s" % self.domain.name)
        account = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=self.domain.id)
        self.cleanup_accounts.append(account)
        self.debug("Creating shared network for account: %s" %
                                                        account.account.name)
        network = self.create_Shared_Network(account, acltype="Account")

        self.debug(
            "Fetching details of default security group in network: %s" %
                                                                network.name)
        sec_grps = SecurityGroup.list(self.apiclient,
                                      account=account.account.name,
                                      domainid=account.account.domainid,
                                      listall=True)
        self.assertIsInstance(sec_grps, list,
                              "List sec groups should return a valid resposne")
        default = sec_grps[0]
        self.debug("Remiving the defualt security group")
        try:
            cmd = deleteSecurityGroup.deleteSecurityGroupCmd()
            cmd.id = default.id
            self.apiclient.deleteSecurityGroup(cmd)
        except Exception as e:
            self.fail("Failed to delete default security group: %s" % e)
        return

    @attr(tags=["advancedsg"])
    @unittest.skip("Work in progress")
    def test_22_attach_iso_shared_nw(self):
        """Test - Attach ISO to VM in shared network scope account"""

        # Steps for validation
        # 1. Attach ISO to VM in shared network scope account
        # 2. Detach ISO from VM in shared network scope account
        # Validate the following
        # 1. Attach ISO to VM in shared network scope account successful
        # 2. Detach ISO from VM in shared network scope account successful

        self.debug("Creating account in domain: %s" % self.domain.name)
        account = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=self.domain.id)
        self.cleanup_accounts.append(account)

        self.debug("Creating account wide shared network for account: %s" %
                                                        account.account.name)
        network = self.create_Shared_Network(account, acltype="Account")

        self.debug("Verifying the shared network created: %s" % network.name)
        self.validate_Shared_Network(network)

        # Cleanup the networks created
        self.cleanup_networks.append(network)

        self.debug("Deplying VMs in the networks %s & %s" % network.name)
        vm = self.create_Instance(account=account, networks=[network.id])

        self.debug("Registering ISO in account: %s" % account.account.name)
        iso = self.create_Iso(account)

        self.debug("Attaching ISO %s to vm %s" % (iso.name, vm.name))
        try:
            vm.attach_iso(self.apiclient, iso)
        except Exception as e:
            self.fail("Failed to attach ISO: %s" % e)

        self.debug("Detaching ISO %s to vm %s" % (iso.name, vm.name))
        try:
            vm.detach_iso(self.apiclient)
        except Exception as e:
            self.fail("Failed to detach ISO: %s" % e)
        return

    @attr(tags=["advancedsg"])
    @unittest.skip("Work in progress")
    def test_23_attach_iso_sec_grp_nw(self):
        """Test - Attach ISO to VM in shared network SG enabled"""

        # Steps for validation
        # 1. Attach ISO to VM in shared network SG enabled
        # 2. Detach ISO from VM in shared network SG enabled
        # Validate the following
        # 1. Attach ISO to VM in shared network SG enabled account successful
        # 2. Detach ISO from VM in shared network SG enabled successful

        self.debug("Creating account in domain: %s" % self.domain.name)
        account = Account.create(self.apiclient, self.services["account"],
                                 admin=True, domainid=self.domain.id)
        self.cleanup_accounts.append(account)

        self.debug("Creating account wide shared network for account: %s" %
                                                        account.account.name)
        network = self.create_Shared_Network(account, acltype="Account")

        self.debug("Verifying the shared network created: %s" % network.name)
        self.validate_Shared_Network(network)

        self.debug("Create a security group in account %s" %
                                                        account.account.name)
        sec_group = self.create_Sec_Group(account=account)

        # Cleanup the networks created
        self.cleanup_networks.append(network)

        self.debug("Deplying VMs in the networks %s & %s" % network.name)
        vm = self.create_Instance(account=account, networks=[network.id],
                                  sec_grps=[sec_group.id])

        self.debug("Registering ISO in account: %s" % account.account.name)
        iso = self.create_Iso(account)

        self.debug("Attaching ISO %s to vm %s" % (iso.name, vm.name))
        try:
            vm.attach_iso(self.apiclient, iso)
        except Exception as e:
            self.fail("Failed to attach ISO: %s" % e)

        self.debug("Detaching ISO %s to vm %s" % (iso.name, vm.name))
        try:
            vm.detach_iso(self.apiclient)
        except Exception as e:
            self.fail("Failed to detach ISO: %s" % e)
        return
