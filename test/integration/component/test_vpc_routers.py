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

""" Component tests for VPC - Router Operations 
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
    """Test VPC Router services
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
                                    "memory": 64,
                                    },
                         "service_offering_new": {
                                    "name": "Small Instance for Domain Router",
                                    "displaytext": "Small Instance",
                                    "cpunumber": 1,
                                    "cpuspeed": 100,
                                    "memory": 256,
                                    "issystem": "true",
                                    "systemvmtype": "domainrouter"
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
                         "network_offering_no_lb": {
                                    "name": 'VPC Network offering',
                                    "displaytext": 'VPC Network off',
                                    "guestiptype": 'Isolated',
                                    "supportedservices": 'Vpn,Dhcp,Dns,SourceNat,PortForwarding,UserData,StaticNat,NetworkACL',
                                    "traffictype": 'GUEST',
                                    "availability": 'Optional',
                                    "useVpc": 'on',
                                    "serviceProviderList": {
                                            "Vpn": 'VpcVirtualRouter',
                                            "Dhcp": 'VpcVirtualRouter',
                                            "Dns": 'VpcVirtualRouter',
                                            "SourceNat": 'VpcVirtualRouter',
                                            "PortForwarding": 'VpcVirtualRouter',
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
                                    "protocol": "TCP",
                                    "cidrlist": '0.0.0.0/0',
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
                         "http_rule": {
                                    "startport": 80,
                                    "endport": 80,
                                    "cidrlist": '0.0.0.0/0',
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

class TestVPCRoutersBasic(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.apiclient = super(
                               TestVPCRoutersBasic,
                               cls
                               ).getClsTestClient().getApiClient()
        cls.services = Services().services
        # Get Zone, Domain and templates
        cls.domain = get_domain(cls.apiclient, cls.services)
        cls.zone = get_zone(cls.apiclient, cls.services)
        cls.template = get_template(
                            cls.apiclient,
                            cls.zone.id,
                            cls.services["ostype"]
                            )
        cls.services["virtual_machine"]["zoneid"] = cls.zone.id
        cls.services["virtual_machine"]["template"] = cls.template.id

        cls.service_offering = ServiceOffering.create(
                                            cls.apiclient,
                                            cls.services["service_offering"]
                                            )
        cls.vpc_off = VpcOffering.create(
                                     cls.apiclient,
                                     cls.services["vpc_offering"]
                                     )
        cls.vpc_off.update(cls.apiclient, state='Enabled')
        cls.account = Account.create(
                                     cls.apiclient,
                                     cls.services["account"],
                                     admin=True,
                                     domainid=cls.domain.id
                                     )
        cls._cleanup = [cls.account]
        cls._cleanup.append(cls.vpc_off)
        #cls.debug("Enabling the VPC offering created")
        cls.vpc_off.update(cls.apiclient, state='Enabled')

        #cls.debug("creating a VPC network in the account: %s" %
                                                   # cls.account.account.name)
        cls.services["vpc"]["cidr"] = '10.1.1.1/16'
        cls.vpc = VPC.create(
                         cls.apiclient,
                         cls.services["vpc"],
                         vpcofferingid=cls.vpc_off.id,
                         zoneid=cls.zone.id,
                         account=cls.account.account.name,
                         domainid=cls.account.account.domainid
                         )

        cls._cleanup.append(cls.service_offering)
        return

    @classmethod
    def tearDownClass(cls):
        try:
            #Cleanup resources used
            cleanup_resources(cls.apiclient, cls._cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        
        wait_for_cleanup(cls.apiclient, ["account.cleanup.interval"])
        return

    def setUp(self):
        self.apiclient = self.testClient.getApiClient()
        
        return

    def tearDown(self):
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

    def validate_vpc_network(self, network, state=None):
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
        if state:
            self.assertEqual(
                 vpc_networks[0].state,
                 state,
                "VPC state should be '%s'" % state
                )
        self.debug("VPC network validated - %s" % network.name)
        return
   
    def migrate_router(self, router):
        """ Migrate the router """

        self.debug("Checking if the host is available for migration?")
        hosts = Host.list(self.apiclient, zoneid=self.zone.id, type='Routing')

        self.assertEqual(
                         isinstance(hosts, list),
                         True,
                         "List hosts should return a valid list"
                         )
        if len(hosts) < 2:
            raise unittest.SkipTest(
            "No host available for migration. Test requires atleast 2 hosts")

        # Remove the host of current VM from the hosts list
        hosts[:] = [host for host in hosts if host.id != router.hostid]
        host = hosts[0]
        self.debug("Validating if the network rules work properly or not?")

        self.debug("Migrating VM-ID: %s from %s to Host: %s" % (
                                                        router.id,
                                                        router.hostid,
                                                        host.name
                                                        ))
        try:

            #Migrate  the router
            cmd = migrateSystemVm.migrateSystemVmCmd()
            cmd.isAsync = "false"
            cmd.hostid = host.id
            cmd.virtualmachineid = router.id
            self.apiclient.migrateSystemVm(cmd)

        except Exception as e:
            self.fail("Failed to migrate instance, %s" % e)
   
        self.debug("Waiting for Router mgiration ....")
        time.sleep(240) 
        
        #List routers to check state of router
        router_response = list_routers(
                                    self.apiclient,
                                    id=router.id
                                    )
        self.assertEqual(
                            isinstance(router_response, list),
                            True,
                            "Check list response returns a valid list"
                        )
        
        self.assertEqual(router_response[0].hostid, host.id, "Migration to host %s failed. The router host is"
                         "still %s" % (host.id, router_response[0].hostid))
        return

    @attr(tags=["advanced","advancedns", "intervlan"])
    def test_01_stop_start_router_after_creating_vpc(self):
        """ Test to stop and start router after creation of VPC
        """
	
	    # Validate following:
	    # 1. Create a VPC with cidr - 10.1.1.1/16
	    # 2. Stop the VPC Virtual Router which is created as a result of VPC creation.
	    # 3. Start the Stopped VPC Virtual Router

        self.validate_vpc_offering(self.vpc_off)
        self.validate_vpc_network(self.vpc)

	    # Stop the VPC Router
        routers = Router.list(
                              self.apiclient,
                              account=self.account.account.name,
                              domainid=self.account.account.domainid,
                              listall=True
                              )
        self.assertEqual(
                         isinstance(routers, list),
                         True,
                         "List Routers should return a valid list"
                         )
        router = routers[0]	
        self.debug("Stopping the router with ID: %s" % router.id)

        #Stop the router
        cmd = stopRouter.stopRouterCmd()
        cmd.id = router.id
        self.apiclient.stopRouter(cmd)
	
	    #List routers to check state of router
        router_response = list_routers(
                                    self.apiclient,
                                    id=router.id
                                    )
        self.assertEqual(
                            isinstance(router_response, list),
                            True,
                            "Check list response returns a valid list"
                        )
        #List router should have router in stopped state
        self.assertEqual(
                            router_response[0].state,
                            'Stopped',
                            "Check list router response for router state"
                        )

        self.debug("Stopped the router with ID: %s" % router.id)

	    # Start The Router
        self.debug("Starting the router with ID: %s" % router.id)
        cmd = startRouter.startRouterCmd()
        cmd.id = router.id
        self.apiclient.startRouter(cmd)

	    #List routers to check state of router
        router_response = list_routers(
                                    self.apiclient,
                                    id=router.id
                                    )
        self.assertEqual(
                            isinstance(router_response, list),
                            True,
                            "Check list response returns a valid list"
                        )
        #List router should have router in running state
        self.assertEqual(
                            router_response[0].state,
                            'Running',
                            "Check list router response for router state"
                        )
        self.debug("Started the router with ID: %s" % router.id)
        
        return

    @attr(tags=["advanced","advancedns", "intervlan"])
    def test_02_reboot_router_after_creating_vpc(self):
	""" Test to reboot the router after creating a VPC
	"""
	    # Validate the following 
	    # 1. Create a VPC with cidr - 10.1.1.1/16
	    # 2. Reboot the VPC Virtual Router which is created as a result of VPC creation.
        	    # Stop the VPC Router
        
        self.validate_vpc_offering(self.vpc_off)
        self.validate_vpc_network(self.vpc)
        routers = Router.list(
                              self.apiclient,
                              account=self.account.account.name,
                              domainid=self.account.account.domainid,
                              listall=True
                              )
        self.assertEqual(
                         isinstance(routers, list),
                         True,
                         "List Routers should return a valid list"
                         )
        router = routers[0]	

        self.debug("Rebooting the router ...")
        #Reboot the router
        cmd = rebootRouter.rebootRouterCmd()
        cmd.id = router.id
        self.apiclient.rebootRouter(cmd)

        #List routers to check state of router
        router_response = list_routers(
                                    self.apiclient,
                                    id=router.id
                                    )
        self.assertEqual(
                            isinstance(router_response, list),
                            True,
                            "Check list response returns a valid list"
                        )
        #List router should have router in running state and same public IP
        self.assertEqual(
                            router_response[0].state,
                            'Running',
                            "Check list router response for router state"
                        )
        return


    @attr(tags=["advanced","advancedns", "intervlan"])
    def test_03_destroy_router_after_creating_vpc(self):
	""" Test to destroy the router after creating a VPC
	"""
	    # Validate the following 
	    # 1. Create a VPC with cidr - 10.1.1.1/16
	    # 2. Destroy the VPC Virtual Router which is created as a result of VPC creation.
        self.validate_vpc_offering(self.vpc_off)
        self.validate_vpc_network(self.vpc)
        routers = Router.list(
                              self.apiclient,
                              account=self.account.account.name,
                              domainid=self.account.account.domainid,
                              listall=True
                              )
        self.assertEqual(
                         isinstance(routers, list),
                         True,
                         "List Routers should return a valid list"
                         )
     
        Router.destroy( self.apiclient,
		        id=routers[0].id
		      )
		
        routers = Router.list(
                              self.apiclient,
                              account=self.account.account.name,
                              domainid=self.account.account.domainid,
                              listall=True
                              )
        self.assertEqual(
                         isinstance(routers, list),
                         False,
                         "List Routers should be empty"
                         )
        return

    @attr(tags=["advanced","advancedns", "intervlan"])
    def test_04_migrate_router_after_creating_vpc(self):
        """ Test migration of router to another host after creating VPC """

        self.validate_vpc_offering(self.vpc_off)
        self.validate_vpc_network(self.vpc)

        routers = Router.list(
                              self.apiclient,
                              account=self.account.account.name,
                              domainid=self.account.account.domainid,
                              listall=True
                              )
        self.assertEqual(
                         isinstance(routers, list),
                         True,
                         "List Routers should return a valid list"
                         )
        self.migrate_router(routers[0])
    	return

    @attr(tags=["advanced","advancedns", "intervlan"])
    def test_05_change_service_offerring_vpc(self):
	""" Tests to change service offering of the Router after 
	    creating a vpc
	"""
        
	# Validate the following 
	# 1. Create a VPC with cidr - 10.1.1.1/16
	# 2. Change the service offerings of the VPC Virtual Router which is created as a result of VPC creation.
        
        self.validate_vpc_offering(self.vpc_off)
        self.validate_vpc_network(self.vpc)

        routers = Router.list(
                              self.apiclient,
                              account=self.account.account.name,
                              domainid=self.account.account.domainid,
                              listall=True
                              )
        self.assertEqual(
                         isinstance(routers, list),
                         True,
                         "List Routers should return a valid list"
                         )
        
        #Stop the router
        router = routers[0]
        self.debug("Stopping the router with ID: %s" % router.id)
        cmd = stopRouter.stopRouterCmd()
        cmd.id = router.id
        self.apiclient.stopRouter(cmd)

        service_offering = ServiceOffering.create(
                                                  self.apiclient,
                                                  self.services["service_offering_new"]
                                                 )
        self._cleanup.append(service_offering)
        self.debug("Changing service offering for the Router %s" % router.id)
        try:
	    Router.change_service_offering(self.apiclient,
				                           router.id,
				                           service_offering.id
				                          )
        except:
            self.fail("Changing service offering failed")
 
        routers = Router.list(
                              self.apiclient,
                              account=self.account.account.name,
                              domainid=self.account.account.domainid,
                              id=router.id
                              )
        router = routers[0]
        self.assertEqual(
                         router.serviceofferingid,
                         service_offering.id,
                         "Changing service offering failed as id is %s and expected"
                         "is %s" % (router.serviceofferingid, service_offering.id)
                        ) 
    	return

class TestVPCRouterOneNetwork(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.apiclient = super(
                               TestVPCRouterOneNetwork,
                               cls
                               ).getClsTestClient().getApiClient()
        cls.services = Services().services
        # Get Zone, Domain and templates
        cls.domain = get_domain(cls.apiclient, cls.services)
        cls.zone = get_zone(cls.apiclient, cls.services)
        cls.template = get_template(
                            cls.apiclient,
                            cls.zone.id,
                            cls.services["ostype"]
                            )
        cls.services["virtual_machine"]["zoneid"] = cls.zone.id
        cls.services["virtual_machine"]["template"] = cls.template.id

        cls.service_offering = ServiceOffering.create(
                                            cls.apiclient,
                                            cls.services["service_offering"]
                                            )
        cls.vpc_off = VpcOffering.create(
                                     cls.apiclient,
                                     cls.services["vpc_offering"]
                                     )
        cls.vpc_off.update(cls.apiclient, state='Enabled')

        cls.account = Account.create(
                                     cls.apiclient,
                                     cls.services["account"],
                                     admin=True,
                                     domainid=cls.domain.id
                                     )
        cls._cleanup = [cls.account]
       

        cls.services["vpc"]["cidr"] = '10.1.1.1/16'
        cls.vpc = VPC.create(
                         cls.apiclient,
                         cls.services["vpc"],
                         vpcofferingid=cls.vpc_off.id,
                         zoneid=cls.zone.id,
                         account=cls.account.account.name,
                         domainid=cls.account.account.domainid
                         )

        cls.nw_off = NetworkOffering.create(
                                            cls.apiclient,
                                            cls.services["network_offering"],
                                            conservemode=False
                                            )
        # Enable Network offering
        cls.nw_off.update(cls.apiclient, state='Enabled')
        cls._cleanup.append(cls.nw_off)

        # Creating network using the network offering created
        cls.network_1 = Network.create(
                                cls.apiclient,
                                cls.services["network"],
                                accountid=cls.account.account.name,
                                domainid=cls.account.account.domainid,
                                networkofferingid=cls.nw_off.id,
                                zoneid=cls.zone.id,
                                gateway='10.1.1.1',
                                vpcid=cls.vpc.id
                                )

        # Spawn an instance in that network
        vm_1 = VirtualMachine.create(
                                  cls.apiclient,
                                  cls.services["virtual_machine"],
                                  accountid=cls.account.account.name,
                                  domainid=cls.account.account.domainid,
                                  serviceofferingid=cls.service_offering.id,
                                  networkids=[str(cls.network_1.id)]
                                  )
        vm_2 = VirtualMachine.create(
                                  cls.apiclient,
                                  cls.services["virtual_machine"],
                                  accountid=cls.account.account.name,
                                  domainid=cls.account.account.domainid,
                                  serviceofferingid=cls.service_offering.id,
                                  networkids=[str(cls.network_1.id)]
                                  )

        # Spawn an instance in that network
        vm_3 = VirtualMachine.create(
                                  cls.apiclient,
                                  cls.services["virtual_machine"],
                                  accountid=cls.account.account.name,
                                  domainid=cls.account.account.domainid,
                                  serviceofferingid=cls.service_offering.id,
                                  networkids=[str(cls.network_1.id)]
                                  )

        vms = VirtualMachine.list(
                                  cls.apiclient,
                                  account=cls.account.account.name,
                                  domainid=cls.account.account.domainid,
                                  listall=True
                                  )
        public_ip_1 = PublicIPAddress.create(
                                cls.apiclient,
                                accountid=cls.account.account.name,
                                zoneid=cls.zone.id,
                                domainid=cls.account.account.domainid,
                                networkid=cls.network_1.id,
                                vpcid=cls.vpc.id
                                )

        nat_rule = NATRule.create(
                                  cls.apiclient,
                                  vm_1,
                                  cls.services["natrule"],
                                  ipaddressid=public_ip_1.ipaddress.id,
                                  openfirewall=False,
                                  networkid=cls.network_1.id,
                                  vpcid=cls.vpc.id
                                  )

        nwacl_nat = NetworkACL.create(
                                         cls.apiclient,
                                         networkid=cls.network_1.id,
                                         services=cls.services["natrule"],
                                         traffictype='Ingress'
                                         )

        public_ip_2 = PublicIPAddress.create(
                                cls.apiclient,
                                accountid=cls.account.account.name,
                                zoneid=cls.zone.id,
                                domainid=cls.account.account.domainid,
                                networkid=cls.network_1.id,
                                vpcid=cls.vpc.id
                                )
        try:
            StaticNATRule.enable(
                              cls.apiclient,
                              ipaddressid=public_ip_2.ipaddress.id,
                              virtualmachineid=vm_2.id,
                              networkid=cls.network_1.id
                              )
        except Exception as e:
            cls.fail("Failed to enable static NAT on IP: %s - %s" % (
                                        public_ip_2.ipaddress.ipaddress, e))

        public_ips = PublicIPAddress.list(
                                    cls.apiclient,
                                    networkid=cls.network_1.id,
                                    listall=True,
                                    isstaticnat=True,
                                    account=cls.account.account.name,
                                    domainid=cls.account.account.domainid
                                  )
#        cls.assertEqual(
#                         isinstance(public_ips, list),
#                         True,
#                         "List public Ip for network should list the Ip addr"
#                         )
#        cls.assertEqual(
#                         public_ips[0].ipaddress,
#                         public_ip_2.ipaddress.ipaddress,
#                         "List public Ip for network should list the Ip addr"
#                         )
#

        public_ip_3 = PublicIPAddress.create(
                                cls.apiclient,
                                accountid=cls.account.account.name,
                                zoneid=cls.zone.id,
                                domainid=cls.account.account.domainid,
                                networkid=cls.network_1.id,
                                vpcid=cls.vpc.id
                                )


        lb_rule = LoadBalancerRule.create(
                                    cls.apiclient,
                                    cls.services["lbrule"],
                                    ipaddressid=public_ip_3.ipaddress.id,
                                    accountid=cls.account.account.name,
                                    networkid=cls.network_1.id,
                                    vpcid=cls.vpc.id,
                                    domainid=cls.account.account.domainid
                                )

        lb_rule.assign(cls.apiclient, [vm_3])

        nwacl_lb = NetworkACL.create(
                                cls.apiclient,
                                networkid=cls.network_1.id,
                                services=cls.services["lbrule"],
                                traffictype='Ingress'
                                )

        nwacl_internet_1 = NetworkACL.create(
                                cls.apiclient,
                                networkid=cls.network_1.id,
                                services=cls.services["http_rule"],
                                traffictype='Egress'
                                )
        
        private_gateway = PrivateGateway.create(
                                                cls.apiclient,
                                                gateway='10.1.3.1',
                                                ipaddress='10.1.3.101',
                                                netmask='255.255.255.0',
                                                vlan=678,
                                                vpcid=cls.vpc.id
                                                )
        cls.gateways = PrivateGateway.list(
                                       cls.apiclient,
                                       id=private_gateway.id,
                                       listall=True
                                       )
        static_route = StaticRoute.create(
                                          cls.apiclient,
                                          cidr='11.1.1.1/24',
                                          gatewayid=private_gateway.id
                                          )
        cls.static_routes = StaticRoute.list(
                                       cls.apiclient,
                                       id=static_route.id,
                                       listall=True
                                       )

        cls._cleanup = [
                        cls.service_offering,
                        cls.vpc_off
                        ] 
    
    @classmethod
    def tearDownClass(cls):
        try:
            #Cleanup resources used
            cleanup_resources(cls.apiclient, cls._cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        
        wait_for_cleanup(cls.apiclient, ["account.cleanup.interval"])
        return

    def setUp(self):
        self.apiclient = self.testClient.getApiClient()
        self.account = Account.create(
                                     self.apiclient,
                                     self.services["account"],
                                     admin=True,
                                     domainid=self.domain.id
                                     )
        self.cleanup = [self.account]     
        return

    def tearDown(self):
        try:
            #Clean up, terminate the created network offerings
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

    def validate_vpc_network(self, network, state=None):
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
        if state:
            self.assertEqual(
                 vpc_networks[0].state,
                 state,
                "VPC state should be '%s'" % state
                )
        self.debug("VPC network validated - %s" % network.name)
        return

        try:
            ssh_1 = self.vm_1.get_ssh_client(
                                ipaddress=self.public_ip_1.ipaddress.ipaddress)
            self.debug("SSH into VM is successfully")

            self.debug("Verifying if we can ping to outside world from VM?")
            # Ping to outsite world
            res = ssh_1.execute("ping -c 1 www.google.com")
            # res = 64 bytes from maa03s17-in-f20.1e100.net (74.125.236.212):
            # icmp_req=1 ttl=57 time=25.9 ms
            # --- www.l.google.com ping statistics ---
            # 1 packets transmitted, 1 received, 0% packet loss, time 0ms
            # rtt min/avg/max/mdev = 25.970/25.970/25.970/0.000 ms
            result = str(res)
            self.assertEqual(
                         result.count("1 received"),
                         1,
                         "Ping to outside world from VM should be successful"
                         )

            self.debug("We should be allowed to ping virtual gateway")
            self.debug("VM gateway: %s" % self.vm_1.nic[0].gateway)

            res = ssh_1.execute("ping -c 1 %s" % self.vm_1.nic[0].gateway)
            self.debug("ping -c 1 %s: %s" % (self.vm_1.nic[0].gateway, res))

            result = str(res)
            self.assertEqual(
                         result.count("1 received"),
                         1,
                         "Ping to VM gateway should be successful"
                         )
        except Exception as e:
            self.fail("Failed to SSH into VM - %s, %s" %
                                    (self.public_ip_1.ipaddress.ipaddress, e))
        return

    def validate_network_rules(self):
	""" Validate network rules
	"""
        vms = VirtualMachine.list(
                                  self.apiclient,
                                  account=self.account.account.name,
                                  domainid=self.account.account.domainid,
                                  listall=True
                                  )
        public_ips = PublicIPAddress.list(
                                          self.apiclient,
                                          account=self.account.account.name,
                                          domainid=self.account.account.domainid,
                                          listall=True
                                         )
        for vm, public_ip in zip(vms, public_ips):
            try:
                ssh_1 = vm.get_ssh_client(
                                ipaddress=public_ip.ipaddress.ipaddress)
                self.debug("SSH into VM is successfully")

                self.debug("Verifying if we can ping to outside world from VM?")
                # Ping to outsite world
                res = ssh_1.execute("ping -c 1 www.google.com")
                # res = 64 bytes from maa03s17-in-f20.1e100.net (74.125.236.212):
                # icmp_req=1 ttl=57 time=25.9 ms
                # --- www.l.google.com ping statistics ---
                # 1 packets transmitted, 1 received, 0% packet loss, time 0ms
                # rtt min/avg/max/mdev = 25.970/25.970/25.970/0.000 ms
            except Exception as e:
                self.fail("Failed to SSH into VM - %s, %s" %
                                    (public_ip.ipaddress.ipaddress, e))

            result = str(res)
            self.assertEqual(
                             result.count("1 received"),
                             1,
                             "Ping to outside world from VM should be successful"
                             )

    def migrate_router(self, router):
        """ Migrate the router """

        self.debug("Checking if the host is available for migration?")
        hosts = Host.list(self.apiclient, zoneid=self.zone.id, type='Routing')

        self.assertEqual(
                         isinstance(hosts, list),
                         True,
                         "List hosts should return a valid list"
                         )
        if len(hosts) < 2:
            raise unittest.SkipTest(
            "No host available for migration. Test requires atleast 2 hosts")

        # Remove the host of current VM from the hosts list
        hosts[:] = [host for host in hosts if host.id != router.hostid]
        host = hosts[0]
        self.debug("Validating if the network rules work properly or not?")

        self.debug("Migrating VM-ID: %s from %s to Host: %s" % (
                                                        router.id,
                                                        router.hostid,
                                                        host.name
                                                        ))
        try:

            #Migrate  the router
            cmd = migrateSystemVm.migrateSystemVmCmd()
            cmd.isAsync = "false"
            cmd.hostid = host.id
            cmd.virtualmachineid = router.id
            self.apiclient.migrateSystemVm(cmd)

        except Exception as e:
            self.fail("Failed to migrate instance, %s" % e)
   
        self.debug("Waiting for Router mgiration ....")
        time.sleep(240) 
        
        #List routers to check state of router
        router_response = list_routers(
                                    self.apiclient,
                                    id=router.id
                                    )
        self.assertEqual(
                            isinstance(router_response, list),
                            True,
                            "Check list response returns a valid list"
                        )
        
        self.assertEqual(router_response[0].hostid, host.id, "Migration to host %s failed. The router host is"
                         "still %s" % (host.id, router_response[0].hostid))
        return


 
    @attr(tags=["advanced","advancedns", "intervlan"])
    def test_01_start_stop_router_after_addition_of_one_guest_network(self):
	""" Test start/stop of router after addition of one guest network
	"""
        # Validations
	    #1. Create a VPC with cidr - 10.1.1.1/16
        #2. Add network1(10.1.1.1/24) to this VPC. 
        #3. Deploy vm1,vm2 and vm3 such that they are part of network1.
        #4. Create a PF /Static Nat/LB rule for vms in network1.
        #5. Create ingress network ACL for allowing all the above rules from a public ip range on network1.
        #6. Create egress network ACL for network1 to access google.com.
        #7. Create a private gateway for this VPC and add a static route to this gateway.
        #8. Create a VPN gateway for this VPC and add a static route to this gateway.
        #9. Make sure that all the PF,LB and Static NAT rules work as expected. 
        #10. Make sure that we are able to access google.com from all the user Vms.
        #11. Make sure that the newly added private gateway's and VPN gateway's static routes work as expected

        self.validate_vpc_offering(self.vpc_off)
        self.validate_vpc_network(self.vpc)
        #self.validate_network_rules()
        self.assertEqual(
                        isinstance(self.gateways, list),
                        True,
                        "List private gateways should return a valid response"
                        )
        self.assertEqual(
                        isinstance(self.static_routes, list),
                        True,
                        "List static route should return a valid response"
                        )

        # Stop the VPC Router
        routers = Router.list(
                              self.apiclient,
                              account=self.account.account.name,
                              domainid=self.account.account.domainid,
                              listall=True
                              )
        self.assertEqual(
                         isinstance(routers, list),
                         True,
                         "List Routers should return a valid list"
                         )
        router = routers[0]	
        self.debug("Stopping the router with ID: %s" % router.id)

        #Stop the router
        cmd = stopRouter.stopRouterCmd()
        cmd.id = router.id
        self.apiclient.stopRouter(cmd)
	
	    #List routers to check state of router
        router_response = list_routers(
                                    self.apiclient,
                                    id=router.id
                                    )
        self.assertEqual(
                            isinstance(router_response, list),
                            True,
                            "Check list response returns a valid list"
                        )
        #List router should have router in stopped state
        self.assertEqual(
                            router_response[0].state,
                            'Stopped',
                            "Check list router response for router state"
                        )

        self.debug("Stopped the router with ID: %s" % router.id)

	    # Start The Router
        self.debug("Starting the router with ID: %s" % router.id)
        cmd = startRouter.startRouterCmd()
        cmd.id = router.id
        self.apiclient.startRouter(cmd)

	    #List routers to check state of router
        router_response = list_routers(
                                    self.apiclient,
                                    id=router.id
                                    )
        self.assertEqual(
                            isinstance(router_response, list),
                            True,
                            "Check list response returns a valid list"
                        )
        #List router should have router in running state
        self.assertEqual(
                            router_response[0].state,
                            'Running',
                            "Check list router response for router state"
                        )
        self.debug("Started the router with ID: %s" % router.id)
        
        return

    @attr(tags=["advanced","advancedns", "intervlan"])
    def test_02_reboot_router_after_addition_of_one_guest_network(self):
	""" Test reboot of router after addition of one guest network
	"""
        # Validations
	    #1. Create a VPC with cidr - 10.1.1.1/16
        #2. Add network1(10.1.1.1/24) to this VPC. 
        #3. Deploy vm1,vm2 and vm3 such that they are part of network1.
        #4. Create a PF /Static Nat/LB rule for vms in network1.
        #5. Create ingress network ACL for allowing all the above rules from a public ip range on network1.
        #6. Create egress network ACL for network1 to access google.com.
        #7. Create a private gateway for this VPC and add a static route to this gateway.
        #8. Create a VPN gateway for this VPC and add a static route to this gateway.
        #9. Make sure that all the PF,LB and Static NAT rules work as expected. 
        #10. Make sure that we are able to access google.com from all the user Vms.
        #11. Make sure that the newly added private gateway's and VPN gateway's static routes work as expected

        self.validate_vpc_offering(self.vpc_off)
        self.validate_vpc_network(self.vpc)
        self.assertEqual(
                        isinstance(self.gateways, list),
                        True,
                        "List private gateways should return a valid response"
                        )
        self.assertEqual(
                        isinstance(self.static_routes, list),
                        True,
                        "List static route should return a valid response"
                        )

        routers = Router.list(
                              self.apiclient,
                              account=self.account.account.name,
                              domainid=self.account.account.domainid,
                              listall=True
                              )
        self.assertEqual(
                         isinstance(routers, list),
                         True,
                         "List Routers should return a valid list"
                         )
        router = routers[0]	

        self.debug("Rebooting the router ...")
        #Reboot the router
        cmd = rebootRouter.rebootRouterCmd()
        cmd.id = router.id
        self.apiclient.rebootRouter(cmd)

        #List routers to check state of router
        router_response = list_routers(
                                    self.apiclient,
                                    id=router.id
                                    )
        self.assertEqual(
                            isinstance(router_response, list),
                            True,
                            "Check list response returns a valid list"
                        )
        #List router should have router in running state and same public IP
        self.assertEqual(
                            router_response[0].state,
                            'Running',
                            "Check list router response for router state"
                        )
        return

    @attr(tags=["advanced","advancedns", "intervlan"])
    def test_03_destroy_router_after_addition_of_one_guest_network(self):
	""" Test destroy of router after addition of one guest network
	"""
        # Validations
	    #1. Create a VPC with cidr - 10.1.1.1/16
        #2. Add network1(10.1.1.1/24) to this VPC. 
        #3. Deploy vm1,vm2 and vm3 such that they are part of network1.
        #4. Create a PF /Static Nat/LB rule for vms in network1.
        #5. Create ingress network ACL for allowing all the above rules from a public ip range on network1.
        #6. Create egress network ACL for network1 to access google.com.
        #7. Create a private gateway for this VPC and add a static route to this gateway.
        #8. Create a VPN gateway for this VPC and add a static route to this gateway.
        #9. Make sure that all the PF,LB and Static NAT rules work as expected. 
        #10. Make sure that we are able to access google.com from all the user Vms.
        #11. Make sure that the newly added private gateway's and VPN gateway's static routes work as expected

        self.validate_vpc_offering(self.vpc_off)
        self.validate_vpc_network(self.vpc)
        self.assertEqual(
                        isinstance(self.gateways, list),
                        True,
                        "List private gateways should return a valid response"
                        )
        self.assertEqual(
                        isinstance(self.static_routes, list),
                        True,
                        "List static route should return a valid response"
                        )

        routers = Router.list(
                              self.apiclient,
                              account=self.account.account.name,
                              domainid=self.account.account.domainid,
                              listall=True
                              )
        self.assertEqual(
                         isinstance(routers, list),
                         True,
                         "List Routers should return a valid list"
                         )
     
        Router.destroy( self.apiclient,
		        id=routers[0].id
		      )
		
        routers = Router.list(
                              self.apiclient,
                              account=self.account.account.name,
                              domainid=self.account.account.domainid,
                              listall=True
                              )
        self.assertEqual(
                         isinstance(routers, list),
                         False,
                         "List Routers should be empty"
                         )
        return

    @attr(tags=["advanced","advancedns", "intervlan"])
    def test_04_migrate_router_after_addition_of_one_guest_network(self):
	""" Test migrate of router after addition of one guest network
	"""
        # Validations
	    #1. Create a VPC with cidr - 10.1.1.1/16
        #2. Add network1(10.1.1.1/24) to this VPC. 
        #3. Deploy vm1,vm2 and vm3 such that they are part of network1.
        #4. Create a PF /Static Nat/LB rule for vms in network1.
        #5. Create ingress network ACL for allowing all the above rules from a public ip range on network1.
        #6. Create egress network ACL for network1 to access google.com.
        #7. Create a private gateway for this VPC and add a static route to this gateway.
        #8. Create a VPN gateway for this VPC and add a static route to this gateway.
        #9. Make sure that all the PF,LB and Static NAT rules work as expected. 
        #10. Make sure that we are able to access google.com from all the user Vms.
        #11. Make sure that the newly added private gateway's and VPN gateway's static routes work as expected

        self.validate_vpc_offering(self.vpc_off)
        self.validate_vpc_network(self.vpc)
        self.assertEqual(
                        isinstance(self.gateways, list),
                        True,
                        "List private gateways should return a valid response"
                        )
        self.assertEqual(
                        isinstance(self.static_routes, list),
                        True,
                        "List static route should return a valid response"
                        )
        routers = Router.list(
                              self.apiclient,
                              account=self.account.account.name,
                              domainid=self.account.account.domainid,
                              listall=True
                              )
        self.assertEqual(
                         isinstance(routers, list),
                         True,
                         "List Routers should return a valid list"
                         )
        self.migrate_router(routers[0])
    	return

    @attr(tags=["advanced","advancedns", "intervlan"])
    def test_05_chg_srv_off_router_after_addition_of_one_guest_network(self):
	""" Test to change service offering of router after addition of one guest network
	"""
        # Validations
	    #1. Create a VPC with cidr - 10.1.1.1/16
        #2. Add network1(10.1.1.1/24) to this VPC. 
        #3. Deploy vm1,vm2 and vm3 such that they are part of network1.
        #4. Create a PF /Static Nat/LB rule for vms in network1.
        #5. Create ingress network ACL for allowing all the above rules from a public ip range on network1.
        #6. Create egress network ACL for network1 to access google.com.
        #7. Create a private gateway for this VPC and add a static route to this gateway.
        #8. Create a VPN gateway for this VPC and add a static route to this gateway.
        #9. Make sure that all the PF,LB and Static NAT rules work as expected. 
        #10. Make sure that we are able to access google.com from all the user Vms.
        #11. Make sure that the newly added private gateway's and VPN gateway's static routes work as expected

        self.validate_vpc_offering(self.vpc_off)
        self.validate_vpc_network(self.vpc)
        self.assertEqual(
                        isinstance(self.gateways, list),
                        True,
                        "List private gateways should return a valid response"
                        )
        self.assertEqual(
                        isinstance(self.static_routes, list),
                        True,
                        "List static route should return a valid response"
                        )
 
        routers = Router.list(
                              self.apiclient,
                              account=self.account.account.name,
                              domainid=self.account.account.domainid,
                              listall=True
                              )
        self.assertEqual(
                         isinstance(routers, list),
                         True,
                         "List Routers should return a valid list"
                         )
        
        #Stop the router
        router = routers[0]
        self.debug("Stopping the router with ID: %s" % router.id)
        cmd = stopRouter.stopRouterCmd()
        cmd.id = router.id
        self.apiclient.stopRouter(cmd)

        service_offering = ServiceOffering.create(
                                                  self.apiclient,
                                                  self.services["service_offering_new"]
                                                 )
        self._cleanup.append(service_offering)
        self.debug("Changing service offering for the Router %s" % router.id)
        try: 
	    Router.change_service_offering(self.apiclient,
				                           router.id,
				                           service_offering.id
				                          )
        except:
            self.fail("Changing service offering failed")
        
        routers = Router.list(
                              self.apiclient,
                              account=self.account.account.name,
                              domainid=self.account.account.domainid,
                              id=router.id
                              )
        router = routers[0]
        self.assertEqual(
                         router.serviceofferingid,
                         service_offering.id,
                         "Changing service offering failed as id is %s and expected"
                         "is %s" % (router.serviceofferingid, service_offering.id)
                        ) 
    	return
