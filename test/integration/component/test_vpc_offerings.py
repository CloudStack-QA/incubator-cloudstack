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
import unittest

""" Component tests for inter VLAN functionality
"""
#Import Local Modules
import marvin
from nose.plugins.attrib import attr
from marvin.cloudstackTestCase import *
from marvin.cloudstackAPI import *
from marvin.integration.lib.utils import *
from marvin.integration.lib.base import *
from marvin.integration.lib.common import *
from marvin.remoteSSHClient import remoteSSHClient
import datetime


class Services:
    """Test inter VLAN services
    """

    def __init__(self):
        self.services = {
                         "account": {
                                    "email": "test@test.com",
                                    "firstname": "Test",
                                    "lastname": "User",
                                    "username": "test",
                                    # Random characters are appended for unique
                                    # username
                                    "password": "password",
                                    },
                         "service_offering": {
                                    "name": "Tiny Instance",
                                    "displaytext": "Tiny Instance",
                                    "cpunumber": 1,
                                    "cpuspeed": 100,
                                    "memory": 128,
                                    },
                         "network_offering": {
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
                                  "name": "Test Network",
                                  "displaytext": "Test Network",
                                  "netmask": '255.255.255.0'
                                },
                         "lbrule": {
                                    "name": "SSH",
                                    "alg": "leastconn",
                                    # Algorithm used for load balancing
                                    "privateport": 22,
                                    "publicport": 2222,
                                    "openfirewall": False,
                                    "startport": 2222,
                                    "endport": 2222,
                                    "cidrlist": '0.0.0.0/0',
                                    "protocol": 'TCP'
                                },
                         "natrule": {
                                    "privateport": 22,
                                    "publicport": 22,
                                    "startport": 22,
                                    "endport": 22,
                                    "protocol": "TCP",
                                    "cidrlist": '0.0.0.0/0',
                                },
                         "fw_rule": {
                                    "startport": 1,
                                    "endport": 6000,
                                    "cidr": '0.0.0.0/0',
                                    # Any network (For creating FW rule)
                                    "protocol": "TCP"
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
                         # Cent OS 5.3 (64 bit)
                         "sleep": 60,
                         "timeout": 10,
                         "mode": 'advanced'
                    }


class TestVPCOffering(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_client = super(
                               TestVPCOffering,
                               cls
                               ).getClsTestClient().getApiClient()
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
            #Cleanup resources used
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
                                     admin=True,
                                     domainid=self.domain.id
                                     )
        self.cleanup = []
        return

    def tearDown(self):
        try:
            #Clean up, terminate the created network offering
            self.account.delete(self.apiclient)
            interval = list_configurations(
                                    self.apiclient,
                                    name='network.gc.interval'
                                    )
            wait = list_configurations(
                                    self.apiclient,
                                    name='network.gc.wait'
                                    )
            # Sleep to ensure that all resources are deleted
            time.sleep(int(interval[0].value) + int(wait[0].value))
            cleanup_resources(self.apiclient, self.cleanup)
            interval = list_configurations(
                                    self.apiclient,
                                    name='network.gc.interval'
                                    )
            wait = list_configurations(
                                    self.apiclient,
                                    name='network.gc.wait'
                                    )
            # Sleep to ensure that all resources are deleted
            time.sleep(int(interval[0].value) + int(wait[0].value))
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def validate_vpc_offering(self, vpc_offering):
        """Validates the VPC offering"""

        self.debug("Check if the VPC offering is created successfully?")
        vpc_offs = VpcOffering.list(
                                    self.apiclient,
                                    id=vpc_offering.id
                                    )
        self.assertEqual(
                         isinstance(vpc_offs, list),
                         True,
                         "List VPC offerings should return a valid list"
                         )
        self.assertEqual(
                 vpc_offering.name,
                 vpc_offs[0].name,
                "Name of the VPC offering should match with listVPCOff data"
                )
        self.debug(
                "VPC offering is created successfully - %s" %
                                                        vpc_offering.name)
        return

    def validate_vpc_network(self, network):
        """Validates the VPC network"""

        self.debug("Check if the VPC network is created successfully?")
        vpc_networks = VPC.list(
                                    self.apiclient,
                                    id=network.id
                          )
        self.assertEqual(
                         isinstance(vpc_networks, list),
                         True,
                         "List VPC network should return a valid list"
                         )
        self.assertEqual(
                 network.name,
                 vpc_networks[0].name,
                 "Name of the VPC network should match with listVPC data"
                )
        self.debug("VPC network created successfully - %s" % network.name)
        return

    @attr(tags=["advanced","advancedns", "intervlan"])
    def test_01_create_vpc_offering(self):
        """ Test create VPC offering
        """

        # Steps for validation
        # 1. Create VPC Offering by specifying all supported Services
        # 2. VPC offering should be created successfully.

        self.debug("Creating inter VPC offering")
        vpc_off = VpcOffering.create(
                                     self.apiclient,
                                     self.services["vpc_offering"]
                                     )

        self.debug("Check if the VPC offering is created successfully?")
        self.cleanup.append(vpc_off)
        self.validate_vpc_offering(vpc_off)
        return

    @attr(tags=["advanced","advancedns", "intervlan"])
    @unittest.skip("Skipping - Issue: Deleting account doesn't clean VPC")
    def test_02_deploy_vms_in_vpc_nw(self):
        """Test deploy virtual machines in VPC networks"""

        # 1. Create VPC Offering by specifying all supported Services
        #   (Vpn,dhcpdns,UserData, SourceNat,Static NAT and PF,LB,NetworkAcl)
        # 2. Create a VPC using the above VPC offering
        # 3. Create a network as part of this VPC.
        # 4. Deploy few Vms.
        # 5. Create a LB rule for this VM.
        # 6. Create a PF rule for this VM.
        # 7. Create a  Static Nat rule for this VM.
        # 8. Create Ingress rules on the network to open the above created
        #    LB PF and Static Nat rule
        # 9. Create Egress Network ACL for this network to access google.com.
        # 10. Enable VPN services

        self.debug("Creating a VPC offering..")
        vpc_off = VpcOffering.create(
                                     self.apiclient,
                                     self.services["vpc_offering"]
                                     )

        self._cleanup.append(vpc_off)
        self.validate_vpc_offering(vpc_off)

        self.debug("Enabling the VPC offering created")
        vpc_off.update(self.apiclient, state='Enabled')

        self.debug("creating a VPC network in the account: %s" %
                                                    self.account.account.name)
        vpc = VPC.create(
                         self.apiclient,
                         self.services["vpc"],
                         vpcofferingid=vpc_off.id,
                         zoneid=self.zone.id,
                         account=self.account.account.name,
                         domainid=self.account.account.domainid
                         )
        self.validate_vpc_network(vpc)

        self.network_offering = NetworkOffering.create(
                                            self.apiclient,
                                            self.services["network_offering"],
                                            conservemode=False
                                            )
        # Enable Network offering
        self.network_offering.update(self.apiclient, state='Enabled')
        self._cleanup.append(self.network_offering)

        gateway = vpc.cidr.split('/')[0]
        # Split the cidr to retrieve gateway
        # for eg. cidr = 10.0.0.1/24
        # Gateway = 10.0.0.1

        # Creating network using the network offering created
        self.debug("Creating network with network offering: %s" %
                                                    self.network_offering.id)
        network = Network.create(
                                self.apiclient,
                                self.services["network"],
                                accountid=self.account.account.name,
                                domainid=self.account.account.domainid,
                                networkofferingid=self.network_offering.id,
                                zoneid=self.zone.id,
                                gateway=gateway,
                                vpcid=vpc.id
                                )
        self.debug("Created network with ID: %s" % network.id)
        # Spawn an instance in that network
        virtual_machine = VirtualMachine.create(
                                  self.apiclient,
                                  self.services["virtual_machine"],
                                  accountid=self.account.account.name,
                                  domainid=self.account.account.domainid,
                                  serviceofferingid=self.service_offering.id,
                                  networkids=[str(network.id)]
                                  )
        self.debug("Deployed VM in network: %s" % network.id)

        self.debug("Associating public IP for network: %s" % network.name)
        public_ip = PublicIPAddress.create(
                                self.apiclient,
                                accountid=self.account.account.name,
                                zoneid=self.zone.id,
                                domainid=self.account.account.domainid,
                                networkid=network.id,
                                vpcid=vpc.id
                                )
        self.debug("Associated %s with network %s" % (
                                        public_ip.ipaddress.ipaddress,
                                        network.id
                                        ))

        self.debug("Creating LB rule for IP address: %s" %
                                        public_ip.ipaddress.ipaddress)

        lb_rule = LoadBalancerRule.create(
                                    self.apiclient,
                                    self.services["lbrule"],
                                    ipaddressid=public_ip.ipaddress.id,
                                    accountid=self.account.account.name,
                                    networkid=network.id,
                                    vpcid=vpc.id,
                                    domainid=self.account.account.domainid
                                )

        self.debug("Associating public IP for network: %s" % vpc.name)
        public_ip_2 = PublicIPAddress.create(
                                self.apiclient,
                                accountid=self.account.account.name,
                                zoneid=self.zone.id,
                                domainid=self.account.account.domainid,
                                networkid=network.id,
                                vpcid=vpc.id
                                )
        self.debug("Associated %s with network %s" % (
                                        public_ip_2.ipaddress.ipaddress,
                                        network.id
                                        ))

        nat_rule = NATRule.create(
                                  self.apiclient,
                                  virtual_machine,
                                  self.services["natrule"],
                                  ipaddressid=public_ip_2.ipaddress.id,
                                  openfirewall=False,
                                  networkid=network.id,
                                  vpcid=vpc.id
                                  )

        self.debug("Adding NetwrokACl rules to make PF and LB accessible")
        networkacl_1 = NetworkACL.create(
                self.apiclient,
                networkid=network.id,
                services=self.services["natrule"],
                traffictype='Ingress'
                )

        networkacl_2 = NetworkACL.create(
                                self.apiclient,
                                networkid=network.id,
                                services=self.services["lbrule"],
                                traffictype='Ingress'
                                )
        self.debug("Checking if we can SSH into VM?")
        try:
            virtual_machine.get_ssh_client(
                ipaddress=public_ip_2.ipaddress.ipaddress,
                )
            self.debug("SSH into VM is successfully")
        except Exception as e:
            self.fail("Failed to SSH into VM - %s, %s" %
                    (public_ip_2.ipaddress.ipaddress, e))

        self.debug("Associating public IP for network: %s" % network.name)
        public_ip_3 = PublicIPAddress.create(
                                self.apiclient,
                                accountid=self.account.account.name,
                                zoneid=self.zone.id,
                                domainid=self.account.account.domainid,
                                networkid=network.id,
                                vpcid=vpc.id
                                )
        self.debug("Associated %s with network %s" % (
                                        public_ip_3.ipaddress.ipaddress,
                                        network.id
                                        ))
        self.debug("Enabling static NAT for IP: %s" %
                                            public_ip_3.ipaddress.ipaddress)
        try:
            StaticNATRule.enable(
                              self.apiclient,
                              ipaddressid=public_ip_3.ipaddress.id,
                              virtualmachineid=virtual_machine.id,
                              networkid=network.id
                              )
            self.debug("Static NAT enabled for IP: %s" %
                                            public_ip_3.ipaddress.ipaddress)
        except Exception as e:
            self.fail("Failed to enable static NAT on IP: %s - %s" % (
                                            public_ip_3.ipaddress.ipaddress, e))

        public_ips = PublicIPAddress.list(
                                          self.apiclient,
                                          networkid=network.id,
                                          listall=True,
                                          isstaticnat=True,
                                          account=self.account.account.name,
                                          domainid=self.account.account.domainid
                                          )
        self.assertEqual(
                         isinstance(public_ips, list),
                         True,
                         "List public Ip for network should list the Ip addr"
                         )
        self.assertEqual(
                         public_ips[0].ipaddress,
                         public_ip_3.ipaddress.ipaddress,
                         "List public Ip for network should list the Ip addr"
                         )
        # TODO: Remote Access VPN is not yet supported in VPC
#        self.debug("Associating public IP for network: %s" % network.name)
#        public_ip_4 = PublicIPAddress.create(
#                                self.apiclient,
#                                accountid=self.account.account.name,
#                                zoneid=self.zone.id,
#                                domainid=self.account.account.domainid,
#                                networkid=network.id,
#                                vpcid=vpc.id
#                                )
#        self.debug("Associated %s with network %s" % (
#                                        public_ip_4.ipaddress.ipaddress,
#                                        network.id
#                                        ))
#
#        self.debug("Creating a remote access VPN for account: %s" %
#                                                self.account.account.name)
#
#        try:
#            vpn = Vpn.create(
#                         self.apiclient,
#                         publicipid=public_ip_4.ipaddress.id,
#                         account=self.account.account.name,
#                         domainid=self.account.account.domainid,
#                         networkid=network.id,
#                         vpcid=vpc.id
#                         )
#        except Exception as e:
#            self.fail("Failed to create VPN for account: %s - %s" % (
#                                                 self.account.account.name, e))
#
#        try:
#            vpnuser = VpnUser.create(
#                                 self.apiclient,
#                                 username="root",
#                                 password="password",
#                                 account=self.account.account.name,
#                                 domainid=self.account.account.domainid
#                                 )
#        except Exception as e:
#            self.fail("Failed to create VPN user: %s" % e)
#
#        self.debug("Checking if the remote access VPN is created or not?")
#        remote_vpns = Vpn.list(
#                               self.apiclient,
#                               account=self.account.account.name,
#                               domainid=self.account.account.domainid,
#                               publicipid=public_ip_4.ipaddress.id,
#                               listall=True
#                               )
#        self.assertEqual(
#                         isinstance(remote_vpns, list),
#                         True,
#                         "List remote VPNs should not return empty response"
#                         )
#        self.debug("Deleting the remote access VPN for account: %s" %
#                                                self.account.account.name)
        return

    @attr(tags=["advanced","advancedns", "intervlan"])
    def test_03_vpc_off_without_lb(self):
        """Test VPC offering without load balancing service"""

        # Validate the following
        # 1. Create VPC Offering by specifying all supported Services except
        #    LB services.
        # 2. Create a VPC using the above VPC offering.
        # 3. Create a network as part of this VPC.
        # 4. Deploy few Vms.
        # 5. Try to create a LB rule for this VM. LB creation should fail

        self.debug(
                   "Creating a VPC offering with Vpn,dhcpdns,UserData," +
                   " SourceNat,Static NAT and PF services"
                   )

        self.services["vpc_offering"]["supportedservices"] = 'Vpn,Dhcp,Dns,SourceNat,PortForwarding,UserData,StaticNat,NetworkACL'
        self.services["network_offering"]["supportedservices"] = 'Vpn,Dhcp,Dns,SourceNat,PortForwarding,UserData,StaticNat,NetworkACL'
        self.services["network_offering"]["serviceProviderList"] = {
                                            "Vpn": 'VpcVirtualRouter',
                                            "Dhcp": 'VpcVirtualRouter',
                                            "Dns": 'VpcVirtualRouter',
                                            "SourceNat": 'VpcVirtualRouter',
                                            "PortForwarding": 'VpcVirtualRouter',
                                            "UserData": 'VpcVirtualRouter',
                                            "StaticNat": 'VpcVirtualRouter',
                                            "NetworkACL": 'VpcVirtualRouter'
                                        }

        self.network_offering = NetworkOffering.create(
                                            self.apiclient,
                                            self.services["network_offering"],
                                            conservemode=False
                                            )
        # Enable Network offering
        self.network_offering.update(self.apiclient, state='Enabled')
        self._cleanup.append(self.network_offering)

        vpc_off = VpcOffering.create(
                                     self.apiclient,
                                     self.services["vpc_offering"]
                                     )

        self.cleanup.append(vpc_off)
        self.validate_vpc_offering(vpc_off)

        self.debug("Enabling the VPC offering created")
        vpc_off.update(self.apiclient, state='Enabled')

        self.debug("creating a VPC network in the account: %s" %
                                                    self.account.account.name)
        vpc = VPC.create(
                         self.apiclient,
                         self.services["vpc"],
                         vpcofferingid=vpc_off.id,
                         zoneid=self.zone.id,
                         account=self.account.account.name,
                         domainid=self.account.account.domainid
                         )
        self.validate_vpc_network(vpc)

        gateway = vpc.cidr.split('/')[0]
        # Split the cidr to retrieve gateway
        # for eg. cidr = 10.0.0.1/24
        # Gateway = 10.0.0.1

        # Creating network using the network offering created
        self.debug("Creating network with network offering: %s" %
                                                    self.network_offering.id)
        network = Network.create(
                                self.apiclient,
                                self.services["network"],
                                accountid=self.account.account.name,
                                domainid=self.account.account.domainid,
                                networkofferingid=self.network_offering.id,
                                zoneid=self.zone.id,
                                gateway=gateway,
                                vpcid=vpc.id
                                )
        self.debug("Created network with ID: %s" % network.id)

        self.debug("Deploying virtual machines in network: %s" % vpc.name)
        # Spawn an instance in that network
        virtual_machine = VirtualMachine.create(
                                  self.apiclient,
                                  self.services["virtual_machine"],
                                  accountid=self.account.account.name,
                                  domainid=self.account.account.domainid,
                                  serviceofferingid=self.service_offering.id,
                                  networkids=[str(network.id)]
                                  )
        self.debug("Deployed VM in network: %s" % network.id)

        self.debug("Associating public IP for network: %s" % network.name)
        public_ip = PublicIPAddress.create(
                                self.apiclient,
                                accountid=self.account.account.name,
                                zoneid=self.zone.id,
                                domainid=self.account.account.domainid,
                                networkid=network.id,
                                vpcid=vpc.id
                                )
        self.debug("Associated %s with network %s" % (
                                        public_ip.ipaddress.ipaddress,
                                        vpc.id
                                        ))

        self.debug("Trying to LB rule for IP address: %s" %
                                        public_ip.ipaddress.ipaddress)
        with self.assertRaises(Exception):
            LoadBalancerRule.create(
                                    self.apiclient,
                                    self.services["lbrule"],
                                    ipaddressid=public_ip.ipaddress.id,
                                    accountid=self.account.account.name,
                                    networkid=network.id,
                                    vpcid=vpc.id
                                )
        return

    @attr(tags=["advanced","advancedns", "intervlan"])
    def test_04_vpc_off_without_static_nat(self):
        """Test VPC offering without static NAT service"""

        # Validate the following
        # 1. Create VPC Offering by specifying all supported Services except
        #    static NAT services.
        # 2. Create a VPC using the above VPC offering.
        # 3. Create a network as part of this VPC.
        # 4. Deploy few Vms
        # 5. Try to create NAT rule for this VMStatic NAT creation should fail

        self.debug("Creating a VPC offering with Vpn,dhcpdns,UserData," +
                   "SourceNat,lb and PF services")

        self.services["vpc_offering"]["supportedservices"] = 'Vpn,Dhcp,Dns,SourceNat,Lb,UserData,PortForwarding,NetworkACL'
        self.services["network_offering"]["supportedservices"] = 'Vpn,Dhcp,Dns,SourceNat,Lb,UserData,PortForwarding,NetworkACL'
        self.services["network_offering"]["serviceProviderList"] = {
                                            "Vpn": 'VpcVirtualRouter',
                                            "Dhcp": 'VpcVirtualRouter',
                                            "Dns": 'VpcVirtualRouter',
                                            "SourceNat": 'VpcVirtualRouter',
                                            "Lb": 'VpcVirtualRouter',
                                            "UserData": 'VpcVirtualRouter',
                                            "PortForwarding": 'VpcVirtualRouter',
                                            "NetworkACL": 'VpcVirtualRouter'
                                        }

        self.network_offering = NetworkOffering.create(
                                            self.apiclient,
                                            self.services["network_offering"],
                                            conservemode=False
                                            )
        # Enable Network offering
        self.network_offering.update(self.apiclient, state='Enabled')
        self._cleanup.append(self.network_offering)

        vpc_off = VpcOffering.create(
                                     self.apiclient,
                                     self.services["vpc_offering"]
                                     )

        self.cleanup.append(vpc_off)
        self.validate_vpc_offering(vpc_off)

        self.debug("Enabling the VPC offering created")
        vpc_off.update(self.apiclient, state='Enabled')

        self.debug("creating a VPC network in the account: %s" %
                                                    self.account.account.name)
        vpc = VPC.create(
                         self.apiclient,
                         self.services["vpc"],
                         vpcofferingid=vpc_off.id,
                         zoneid=self.zone.id,
                         account=self.account.account.name,
                         domainid=self.account.account.domainid
                         )
        self.validate_vpc_network(vpc)

        gateway = vpc.cidr.split('/')[0]
        # Split the cidr to retrieve gateway
        # for eg. cidr = 10.0.0.1/24
        # Gateway = 10.0.0.1

        # Creating network using the network offering created
        self.debug("Creating network with network offering: %s" %
                                                    self.network_offering.id)
        network = Network.create(
                                self.apiclient,
                                self.services["network"],
                                accountid=self.account.account.name,
                                domainid=self.account.account.domainid,
                                networkofferingid=self.network_offering.id,
                                zoneid=self.zone.id,
                                gateway=gateway,
                                vpcid=vpc.id
                                )
        self.debug("Created network with ID: %s" % network.id)

        self.debug("Deploying virtual machines in network: %s" % vpc.name)
        # Spawn an instance in that network
        virtual_machine = VirtualMachine.create(
                                  self.apiclient,
                                  self.services["virtual_machine"],
                                  accountid=self.account.account.name,
                                  domainid=self.account.account.domainid,
                                  serviceofferingid=self.service_offering.id,
                                  networkids=[str(network.id)]
                                  )
        self.debug("Deployed VM in network: %s" % network.id)

        self.debug("Associating public IP for network: %s" % network.name)
        public_ip = PublicIPAddress.create(
                                self.apiclient,
                                accountid=self.account.account.name,
                                zoneid=self.zone.id,
                                domainid=self.account.account.domainid,
                                networkid=network.id,
                                vpcid=vpc.id
                                )
        self.debug("Associated %s with network %s" % (
                                        public_ip.ipaddress.ipaddress,
                                        network.id
                                        ))

        with self.assertRaises(Exception):
            static_nat = StaticNATRule.create(
                                    self.apiclient,
                                    self.services["fw_rule"],
                                    ipaddressid=public_ip.ipaddress.id
                                  )
            static_nat.enable(
                              self.apiclient,
                              ipaddressid=public_ip.ipaddress.id,
                              virtualmachineid=virtual_machine.id
                              )
        return

    @attr(tags=["advanced","advancedns", "intervlan"])
    def test_05_vpc_off_without_pf(self):
        """Test VPC offering without port forwarding service"""

        # Validate the following
        # 1. Create VPC Offering by specifying all supported Services except
        #    PF services.
        # 2. Create a VPC using the above VPC offering.
        # 3. Create a network as part of this VPC.
        # 4. Deploy few Vms.
        # 5. Try to create a PF rule for this VM. PF creation should fail

        self.debug(
                   "Creating a VPC offering with Vpn,dhcpdns,UserData," +
                   "SourceNat,Static NAT and lb services"
                   )

        self.services["vpc_offering"]["supportedservices"] = 'Vpn,Dhcp,Dns,SourceNat,Lb,UserData,StaticNat,NetworkACL'
        self.services["network_offering"]["supportedservices"] = 'Vpn,Dhcp,Dns,SourceNat,Lb,UserData,StaticNat,NetworkACL'
        self.services["network_offering"]["serviceProviderList"] = {
                                            "Vpn": 'VpcVirtualRouter',
                                            "Dhcp": 'VpcVirtualRouter',
                                            "Dns": 'VpcVirtualRouter',
                                            "SourceNat": 'VpcVirtualRouter',
                                            "Lb": 'VpcVirtualRouter',
                                            "UserData": 'VpcVirtualRouter',
                                            "StaticNat": 'VpcVirtualRouter',
                                            "NetworkACL": 'VpcVirtualRouter'
                                        }

        self.network_offering = NetworkOffering.create(
                                            self.apiclient,
                                            self.services["network_offering"],
                                            conservemode=False
                                            )
        # Enable Network offering
        self.network_offering.update(self.apiclient, state='Enabled')
        self._cleanup.append(self.network_offering)

        vpc_off = VpcOffering.create(
                                     self.apiclient,
                                     self.services["vpc_offering"]
                                     )

        self.cleanup.append(vpc_off)
        self.validate_vpc_offering(vpc_off)

        self.debug("Enabling the VPC offering created")
        vpc_off.update(self.apiclient, state='Enabled')

        self.debug("creating a VPC network in the account: %s" %
                                                    self.account.account.name)
        vpc = VPC.create(
                         self.apiclient,
                         self.services["vpc"],
                         vpcofferingid=vpc_off.id,
                         zoneid=self.zone.id,
                         account=self.account.account.name,
                         domainid=self.account.account.domainid
                         )
        self.validate_vpc_network(vpc)

        gateway = vpc.cidr.split('/')[0]
        # Split the cidr to retrieve gateway
        # for eg. cidr = 10.0.0.1/24
        # Gateway = 10.0.0.1

        # Creating network using the network offering created
        self.debug("Creating network with network offering: %s" %
                                                    self.network_offering.id)
        network = Network.create(
                                self.apiclient,
                                self.services["network"],
                                accountid=self.account.account.name,
                                domainid=self.account.account.domainid,
                                networkofferingid=self.network_offering.id,
                                zoneid=self.zone.id,
                                gateway=gateway,
                                vpcid=vpc.id
                                )
        self.debug("Deploying virtual machines in network: %s" % vpc.name)
        # Spawn an instance in that network
        virtual_machine = VirtualMachine.create(
                                  self.apiclient,
                                  self.services["virtual_machine"],
                                  accountid=self.account.account.name,
                                  domainid=self.account.account.domainid,
                                  serviceofferingid=self.service_offering.id,
                                  networkids=[str(network.id)]
                                  )
        self.debug("Deployed VM in network: %s" % network.id)

        self.debug("Associating public IP for network: %s" % network.name)
        public_ip = PublicIPAddress.create(
                                self.apiclient,
                                accountid=self.account.account.name,
                                zoneid=self.zone.id,
                                domainid=self.account.account.domainid,
                                networkid=network.id,
                                vpcid=vpc.id
                                )
        self.debug("Associated %s with network %s" % (
                                        public_ip.ipaddress.ipaddress,
                                        network.id
                                        ))

        self.debug("Trying to create NAT rule for the IP: %s" %
                                            public_ip.ipaddress.ipaddress)
        with self.assertRaises(Exception):
            NATRule.create(
                        self.apiclient,
                        virtual_machine,
                        self.services["natrule"],
                        ipaddressid=public_ip.ipaddress.id,
                        openfirewall=True
                        )
        return

    @attr(tags=["advanced","advancedns", "intervlan"])
    @unittest.skip("Skipping - API should not allow to create VPC offering without SourceNAT, Firewall")
    def test_06_vpc_off_invalid_services(self):
        """Test VPC offering with invalid services"""

        # Validate the following
        # 1. Creating VPC Offering with no SourceNat service should FAIL.
        # 2. Creating VPC Offering with services NOT supported by VPC
        #    like Firewall should not be allowed
        # 3. Creating VPC Offering with services NOT supported by VPC
        #    like Firewall should not be allowed

        self.debug("Creating a VPC offering without sourceNAT")
        self.services["vpc_offering"]["supportedservices"] = 'Dhcp,Dns,PortForwarding,Vpn,Firewall,Lb,UserData,StaticNat'

        with self.assertRaises(Exception):
            VpcOffering.create(
                                self.apiclient,
                                self.services["vpc_offering"]
                             )

        self.debug("Creating a VPC offering without Firewall")
        self.services["vpc_offering"]["supportedservices"] = 'Dhcp,Dns,PortForwarding,Vpn,SourceNat,Lb,UserData,StaticNat'

        with self.assertRaises(Exception):
            VpcOffering.create(
                                self.apiclient,
                                self.services["vpc_offering"]
                             )

        self.debug("Creating a VPC offering with only sourceNAT service")
        self.services["vpc_offering"]["supportedservices"] = 'SourceNat'

        try:
            vpc_off = VpcOffering.create(
                                self.apiclient,
                                self.services["vpc_offering"]
                             )
            self.validate_vpc_offering(vpc_off)
            # Appending to cleanup to delete after test
            self.cleanup.append(vpc_off)
        except Exception as e:
            self.fail("Failed to create the VPC offering - %s" % e)
        return

    @attr(tags=["advanced","advancedns", "intervlan"])
    def test_07_update_vpc_off(self):
        """Test update VPC offering"""

        # Validate the following
        # 1. Create a VPC Offering.
        # 2. Disable this VPC offering.
        # 3. Create a VPC using this VPC offering. VPC creation should fail.
        # 4. Enable the VPC offering again and create VPC. VPC should be
        #    created successfully
        # 5. Change name and displaytext of the VPCOffering. Name and
        #    displaytext chnages should be reflected in listVPCPffering call

        self.debug("Creating a VPC offering..")
        vpc_off = VpcOffering.create(
                                     self.apiclient,
                                     self.services["vpc_offering"]
                                     )

        self.cleanup.append(vpc_off)
        self.validate_vpc_offering(vpc_off)

        self.debug("Enabling the VPC offering created")
        vpc_off.update(self.apiclient, state='Disabled')

        self.debug("creating a VPC network in the account: %s" %
                                                    self.account.account.name)
        with self.assertRaises(Exception):
            VPC.create(
                         self.apiclient,
                         self.services["vpc"],
                         vpcofferingid=vpc_off.id,
                         zoneid=self.zone.id,
                         account=self.account.account.name,
                         domainid=self.account.account.domainid
                         )
        self.debug("VPC network creation failed! (Test succeeded)")
        self.debug("Enabling the VPC offering created")
        vpc_off.update(self.apiclient, state='Enabled')

        self.debug("creating a VPC network in the account: %s" %
                                                    self.account.account.name)
        vpc = VPC.create(
                         self.apiclient,
                         self.services["vpc"],
                         vpcofferingid=vpc_off.id,
                         zoneid=self.zone.id,
                         account=self.account.account.name,
                         domainid=self.account.account.domainid
                         )
        self.validate_vpc_network(vpc)

        self.debug("Updating name & display text of the vpc offering created")
        new_name = random_gen()
        new_displaytext = random_gen()

        try:
            vpc_off.update(
                       self.apiclient,
                       name=new_name,
                       displaytext=new_displaytext
                       )
        except Exception as e:
            self.fail("Failed to update VPC offering- %s" % e)

        self.debug("Cheking if the changes are reflected to listVPC call?")
        vpc_offs = vpc_off.list(
                                self.apiclient,
                                id=vpc_off.id,
                                listall=True
                                )
        self.assertEqual(
                         isinstance(vpc_offs, list),
                         True,
                         "List VPC offerings shall return a valid list"
                         )
        list_reposnse_vpc = vpc_offs[0]
        self.assertEqual(
                         list_reposnse_vpc.name,
                         new_name,
                         "VPC off Name should be updated with new one"
                         )
        self.assertEqual(
                         list_reposnse_vpc.displaytext,
                         new_displaytext,
                         "VPC off display text should be updated with new one"
                         )
        return

    @attr(tags=["advanced","advancedns", "intervlan"])
    def test_08_list_vpc_off(self):
        """Test list VPC offering"""

        # Validate the following
        # 1. Create multiple VPC Offerings
        # 2. Delete few of the VPC offerings
        # 3. List all the VPC offerings. Deleted VPC offering should not be
        #    returned by list VPC offerings command
        # 4. List offerings by ID. Only offering having ID should get listed
        # 5. List VPC Offerings by displaytext. Only offerings with same
        #    display text should be listed
        # 6. List VPC Offerings by name. Only offerings with same
        #    name should be listed
        # 7. List VPC Offerings by supported services. Only offerings with same
        #    supported services should be listed
        # 8. All VPC offering in "Enabled" state should get listed.
        # 9. All VPC offering in "Disabled" state should get listed

        self.debug("Creating multiple VPC offerings")
        self.services["vpc_offering"]["supportedservices"] = 'SourceNat'

        vpc_off_1 = VpcOffering.create(
                                     self.apiclient,
                                     self.services["vpc_offering"]
                                     )
        self.cleanup.append(vpc_off_1)
        self.validate_vpc_offering(vpc_off_1)
        self.debug("Disabling the VPC offering created")
        vpc_off_1.update(self.apiclient, state='Disabled')

        vpc_off_2 = VpcOffering.create(
                                     self.apiclient,
                                     self.services["vpc_offering"]
                                     )

        self.cleanup.append(vpc_off_2)
        self.validate_vpc_offering(vpc_off_2)
        self.debug("Enabling the VPC offering created")
        vpc_off_2.update(self.apiclient, state='Enabled')

        vpc_off_3 = VpcOffering.create(
                                     self.apiclient,
                                     self.services["vpc_offering"]
                                     )

        self.cleanup.append(vpc_off_3)
        self.validate_vpc_offering(vpc_off_3)
        self.debug("Enabling the VPC offering created")
        vpc_off_3.update(self.apiclient, state='Enabled')

        vpc_off_4 = VpcOffering.create(
                                     self.apiclient,
                                     self.services["vpc_offering"]
                                     )
        self.validate_vpc_offering(vpc_off_4)
        self.debug("Enabling the VPC offering created")
        vpc_off_4.update(self.apiclient, state='Enabled')

        self.debug("Deleting the VPC offering: %s" % vpc_off_4.name)
        vpc_off_4.delete(self.apiclient)

        self.debug("Cheking if listVPCOff return the deleted VPC off")
        vpc_offs = VpcOffering.list(
                             self.apiclient,
                             id=vpc_off_4.id,
                             listall=True
                             )
        self.assertEqual(
                        vpc_offs,
                        None,
                        "List VPC offerings should nt return any response for deleted offering"
                    )

        self.debug("Validating the listVPCOfferings repsonse by ids")
        self.validate_vpc_offering(vpc_off_3)

        self.debug("ListVPCOfferings by displaytext & verifying the response")
        vpc_offs = VpcOffering.list(
                             self.apiclient,
                             displaytext=vpc_off_3.displaytext,
                             listall=True
                             )
        self.assertEqual(
                         isinstance(vpc_offs, list),
                         True,
                         "List VPC offerings shall return a valid response"
                         )
        list_vpc_off_response = vpc_offs[0]
        self.assertIn(
                    vpc_off_3.id,
                    [vpc.id for vpc in vpc_offs],
                    "ListVPC Off with displaytext should return same VPC off"
                 )

        self.debug("ListVPCOfferings by name and verifying the response")
        vpc_offs = VpcOffering.list(
                             self.apiclient,
                             name=vpc_off_2.name,
                             listall=True
                             )
        self.assertEqual(
                         isinstance(vpc_offs, list),
                         True,
                         "List VPC offerings shall return a valid response"
                         )
        list_vpc_off_response = vpc_offs[0]
        self.assertEqual(
                    list_vpc_off_response.id,
                    vpc_off_2.id,
                    "ListVPC Off with name should return same VPC off"
                 )

        self.debug(
            "ListVPCOfferings by supported services & verifying the response")
        vpc_offs = VpcOffering.list(
                             self.apiclient,
                             supportedservices='SourceNat',
                             listall=True
                             )
        self.assertEqual(
                         isinstance(vpc_offs, list),
                         True,
                         "List VPC offerings shall return a valid response"
                         )
        for vpc_off in vpc_offs:
            self.debug(vpc_off)
            self.assertEqual(
                    'SourceNat' in str(vpc_off),
                    True,
                    "ListVPC Off with name should return same VPC off"
                 )

        self.debug("ListVPCOfferings by state & verifying the response")
        vpc_offs = VpcOffering.list(
                             self.apiclient,
                             state='Enabled',
                             listall=True
                             )
        self.assertEqual(
                         isinstance(vpc_offs, list),
                         True,
                         "List VPC offerings shall return a valid response"
                         )
        for vpc_off in vpc_offs:
            self.assertEqual(
                    vpc_off.state,
                    'Enabled',
                    "List VPC offering should return only offerings that are enabled"
                 )

        self.debug("ListVPCOfferings by state & verifying the response")
        vpc_offs = VpcOffering.list(
                             self.apiclient,
                             state='Disabled',
                             listall=True
                             )
        self.assertEqual(
                         isinstance(vpc_offs, list),
                         True,
                         "List VPC offerings shall return a valid response"
                         )
        for vpc_off in vpc_offs:
            self.assertEqual(
                    vpc_off.state,
                    'Disabled',
                    "List VPC offering should return only offerings that are disabled"
                 )
        return
