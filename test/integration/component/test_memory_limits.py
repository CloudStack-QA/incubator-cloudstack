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
""" P1 tests for memory resource limits
"""
# Import Local Modules
from nose.plugins.attrib import attr
from marvin.cloudstackTestCase import cloudstackTestCase, unittest
from marvin.integration.lib.base import (
                                        Account,
                                        ServiceOffering,
                                        VirtualMachine,
                                        Network,
                                        Resources,
                                        Host,
                                        Domain,
                                        Project
                                        )
from marvin.integration.lib.common import (get_domain,
                                        get_zone,
                                        get_template,
                                        cleanup_resources,
					wait_for_cleanup
                                        )
from marvin.integration.lib.utils import get_resource_type


class Services:
    """Test memory resource limit services
    """

    def __init__(self):
        self.services = {
                        "account": {
                                "email": "test@test.com",
                                "firstname": "Test",
                                "lastname": "User",
                                "username": "resource",
                                # Random characters are appended for unique
                                # username
                                "password": "password",
                         },
                         "service_offering": {
                                "name": "Tiny Instance",
                                "displaytext": "Tiny Instance",
                                "cpunumber": 1,
                                "cpuspeed": 100,    # in MHz
                                "memory": 5120,    # In MBs
                        },
                        "virtual_machine": {
                                "displayname": "TestVM",
                                "username": "root",
                                "password": "password",
                                "ssh_port": 22,
                                "hypervisor": 'KVM',
                                "privateport": 22,
                                "publicport": 22,
                                "protocol": 'TCP',
                                },
                         "network": {
                                "name": "Test Network",
                                "displaytext": "Test Network",
                                "netmask": '255.255.255.0'
                                },
                         "project": {
                                "name": "Project",
                                "displaytext": "Test project",
                                },
                         "domain": {
                                "name": "Domain",
                                },
                        "ostype": 'CentOS 5.3 (64-bit)',
                        "sleep": 60,
                        "timeout": 10,
                        "mode": 'advanced',
                        # Networking mode: Advanced, Basic
                    }


class TestMemoryLimits(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_client = super(TestMemoryLimits,
                               cls).getClsTestClient().getApiClient()
        cls.services = Services().services
        # Get Zone, Domain and templates
        cls.domain = get_domain(cls.api_client, cls.services)
        cls.zone = get_zone(cls.api_client, cls.services)
	cls.services["mode"] = cls.zone.networktype

        cls.template = get_template(
                            cls.api_client,
                            cls.zone.id,
                            cls.services["ostype"]
                            )

        cls.services["virtual_machine"]["zoneid"] = cls.zone.id

        cls._cleanup = []
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
                            admin=True
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

    def createInstance(self, service_off, networks=None):
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
                                networkids=networks,
                                serviceofferingid=service_off.id)
            vms = VirtualMachine.list(self.apiclient, id=vm.id, listall=True)
            self.assertIsInstance(vms,
                                  list,
                                  "List VMs should return a valid response")
            self.assertEqual(vms[0].state, "Running",
                             "Vm state should be running after deployment")
            return vm
        except Exception as e:
            self.fail("Failed to deploy an instance: %s" % e)

    def getNetwork(self, account):
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

    def checkResourceCount(self, account, rtype, delete=False):
        """Validates the resource count
            8     - CPUs
            9    - RAM
            10    - Primary (shared) storage (Volumes)
            11    - Secondary storage (Snapshots, Templates & ISOs)
            12    - Network bandwidth rate (in bps)
            13    - Number of times a OS template can be deployed"""
	
	allowedResourceTypes = [8,9,10,11,12,13]
	self.assertTrue(rtype in allowedResourceTypes,"Invalid resource type")

        self.debug("Updating the Memory resource count for account: %s" %
                                                    account.account.name)
        responses = Resources.updateCount(self.apiclient,
                              domainid=account.account.domainid,
                              account=account.account.name,
                              resourcetype=rtype
                              )
        self.assertIsInstance(responses, list,
                        "Update resource count should return valid response")
        response = responses[0]
        self.debug(response.resourcecount)

	if delete:
            self.assertEqual(response.resourcecount,
                         0,
                         "Resource count for %s should be 0" %
                                        get_resource_type(rtype))
        else:
            self.assertNotEqual(response.resourcecount,
                         0,
                         "Resource count for %s should not be 0" %
                                        get_resource_type(rtype)) 
        return

    def findSuitableHost(self, vm):
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

    @unittest.skip("Skip")
    @attr(tags=["advanced", "advancedns","simulator"])
    def test_01_deploy_vm_with_5_gb_ram(self):
        """Test Deploy VM with 5 GB RAM & verify the usage"""

        # Validate the following
        # 1. Create compute offering with 5 GB RAM & Deploy VM as root admin
        # 2. Update Resource count for the root admin Memory usage

        self.debug("Creating service offering with 5 GB RAM")
        self.service_offering = ServiceOffering.create(
                                            self.apiclient,
                                            self.services["service_offering"]
                                            )
        # Adding to cleanup list after execution
        self.cleanup.append(self.service_offering)

        self.debug("Creating an instance with service offering: %s" %
                                                    self.service_offering.name)
        vm = self.createInstance(service_off=self.service_offering)

        self.checkResourceCount(account=self.account, rtype=9)
        self.debug("Stopping instance: %s" % vm.name)
        try:
            vm.stop(self.apiclient)
        except Exception as e:
            self.fail("Failed to stop instance: %s" % e)
        self.checkResourceCount(account=self.account, rtype=9)

        self.debug("Starting instance: %s" % vm.name)
        try:
            vm.start(self.apiclient)
        except Exception as e:
            self.fail("Failed to start instance: %s" % e)
        self.checkResourceCount(account=self.account, rtype=9)

        host = self.findSuitableHost(vm)
        self.debug("Migrating instance: %s to host: %s" % (vm.name, host.name))
        try:
            vm.migrate(self.apiclient, host.id)
        except Exception as e:
            self.fail("Failed to migrate instance: %s" % e)
        self.checkResourceCount(account=self.account, rtype=9)

        self.debug("Destroying instance: %s" % vm.name)
        try:
            vm.delete(self.apiclient)
        except Exception as e:
            self.fail("Failed to delete instance: %s" % e)

	# Wait for expunge interval to cleanup Memory
	wait_for_cleanup(self.apiclient, ["expunge.delay", "expunge.interval"])

        self.checkResourceCount(account=self.account, rtype=9, delete=True)
        return

    @unittest.skip("Skip")
    @attr(tags=["advanced", "advancedns","simulator"])
    def test_02_deploy_multiple_vm_with_5gb_ram(self):
        """Test Deploy multiple VM with 5 GB RAM & verify the usage"""

        # Validate the following
        # 1. Create compute offering with 5 GB RAM
        # 2. Deploy multiple VMs with this service offering
        # 3. Update Resource count for the root admin Memory usage
        # 4. Memory usage should list properly

        self.debug("Creating service offering with 5 GB RAM")
        self.service_offering = ServiceOffering.create(
                                            self.apiclient,
                                            self.services["service_offering"]
                                            )
        # Adding to cleanup list after execution
        self.cleanup.append(self.service_offering)

        self.debug("Creating an instance with service offering: %s" %
                                                    self.service_offering.name)
        vm_1 = self.createInstance(service_off=self.service_offering)
        vm_2 = self.createInstance(service_off=self.service_offering)
        vm_3 = self.createInstance(service_off=self.service_offering) 
 
        self.checkResourceCount(account=self.account, rtype=9)
        self.debug("Destroying instance: %s" % vm_1.name)
        try:
            vm_1.delete(self.apiclient)
        except Exception as e:
            self.fail("Failed to delete instance: %s" % e)
        self.checkResourceCount(account=self.account, rtype=9) 
        return


class TestDomainMemoryLimits(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_client = super(TestDomainMemoryLimits,
                               cls).getClsTestClient().getApiClient()
        cls.services = Services().services
        # Get Zone, Domain and templates
        cls.domain = get_domain(cls.api_client, cls.services)
        cls.zone = get_zone(cls.api_client, cls.services)
	cls.services["mode"] = cls.zone.networktype

        cls.template = get_template(
                            cls.api_client,
                            cls.zone.id,
                            cls.services["ostype"]
                            )

        cls.services["virtual_machine"]["zoneid"] = cls.zone.id

        cls._cleanup = []
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
            pass
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def createInstance(self, service_off, networks=None):
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
                                networkids=networks,
                                serviceofferingid=service_off.id)
            vms = VirtualMachine.list(self.apiclient, id=vm.id, listall=True)
            self.assertIsInstance(vms,
                                  list,
                                  "List VMs should return a valid response")
            self.assertEqual(vms[0].state, "Running",
                             "Vm state should be running after deployment")
            return vm
        except Exception as e:
            self.fail("Failed to deploy an instance: %s" % e)

    def getNetwork(self, account):
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

    def checkResourceCount(self, account, rtype, delete=False):
        """Validates the resource count
            8     - CPUs
            9    - RAM
            10    - Primary (shared) storage (Volumes)
            11    - Secondary storage (Snapshots, Templates & ISOs)
            12    - Network bandwidth rate (in bps)
            13    - Number of times a OS template can be deployed"""

        allowedResourceTypes = [8,9,10,11,12,13]
	self.assertTrue(rtype in allowedResourceTypes,"Invalid resource type")

	self.debug("Updating the Memory resource count for account: %s" %
                                                    account.account.name)
        responses = Resources.updateCount(self.apiclient,
                              domainid=account.account.domainid,
                              account=account.account.name,
                              resourcetype=rtype
                              )
        self.assertIsInstance(responses, list,
                        "Update resource count should return valid response")
        response = responses[0]
        self.debug(response.resourcecount)

	if delete:
            self.assertEqual(response.resourcecount,
                         0,
                         "Resource count for %s should be 0" %
                                        get_resource_type(rtype))
        else:
            self.assertNotEqual(response.resourcecount,
                         0,
                         "Resource count for %s should not be 0" %
                                        get_resource_type(rtype)) 
        return

    def findSuitableHost(self, vm):
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

    def setupAccounts(self):

        self.debug("Creating a sub-domain under: %s" % self.domain.name)
        self.child_domain = Domain.create(self.apiclient,
                                        services=self.services["domain"],
                                        parentdomainid=self.domain.id)
        self.child_do_admin = Account.create(
                                        self.apiclient,
                                        self.services["account"],
                                        admin=True,
                                        domainid=self.child_domain.id
                                        )
        # Cleanup the resources created at end of test
        self.cleanup.append(self.child_do_admin)
        self.cleanup.append(self.child_domain)

        Resources.updateLimit(self.apiclient,
                              resourcetype=9,
                              max=5120,
                              account=self.child_do_admin.account.name,
                              domainid=self.child_do_admin.account.domainid)
	
	self.domain = Domain.create(self.apiclient,
                                services=self.services["domain"],
                                parentdomainid=self.domain.id)

        self.admin = Account.create(
                                    self.apiclient,
                                    self.services["account"],
                                    admin=True,
                                    domainid=self.domain.id)
	
        # Cleanup the resources created at end of test
        self.cleanup.append(self.admin)
	self.cleanup.append(self.domain)

        Resources.updateLimit(self.apiclient,
                              resourcetype=9,
                              max=5120,
                              account=self.admin.account.name,
                              domainid=self.admin.account.domainid)
        return

    @unittest.skip("Skip")
    @attr(tags=["advanced", "advancedns","simulator"])
    @unittest.skip("Skip")
    @attr(configuration='max.account.memory')
    def test_01_deploy_vm_with_5gb_ram(self):
        """Test Deploy VM with 5 GB RAM & verify the usage"""

        # Validate the following
        # 1. Create compute offering with 5 GB RAM & Deploy VM as root admin
        # 2. Update Resource count for the root admin Memory usage

        self.debug("Creating service offering with 5 GB RAM")
        self.service_offering = ServiceOffering.create(
                                            self.apiclient,
                                            self.services["service_offering"]
                                            )
        # Adding to cleanup list after execution
        self.cleanup.append(self.service_offering)

        self.debug("Setting up account and domain hierarchy")
        self.setupAccounts()
        users =  { self.domain: self.admin,
                   self.child_domain: self.child_do_admin
                 }
        for domain, admin in users.items():
            self.account = admin
            self.domain = domain
            self.debug("Creating an instance with service offering: %s" %
                                                    self.service_offering.name)
            vm = self.createInstance(service_off=self.service_offering)

            self.checkResourceCount(account=self.account, rtype=9)
            self.debug("Stopping instance: %s" % vm.name)
            try:
                vm.stop(self.apiclient)
            except Exception as e:
                self.fail("Failed to stop instance: %s" % e)
            self.checkResourceCount(account=self.account, rtype=9)

            self.debug("Creating service offering with 7 GB RAM")
            self.services["service_offering"]["memory"] = 7168
            self.service_offering_7gb = ServiceOffering.create(
                                            self.apiclient,
                                            self.services["service_offering"]
                                            )
            # Adding to cleanup list after execution
            self.cleanup.append(self.service_offering_7gb)

            self.debug(
                "Upgrade service offering of instance %s from %s to %s" %
                                            (vm.name,
                                             self.service_offering.name,
                                             self.service_offering_7gb.name))

            try:
                vm.change_service_offering(self.apiclient,
                                serviceOfferingId=self.service_offering_7gb.id)
            except Exception as e:
                self.fail("Failed to change service offering of vm %s - %s" %
                                                                (vm.name, e))
            self.checkResourceCount(account=self.account, rtype=9)

            self.debug(
                "Down grade service offering of instance %s from %s to %s" %
                                            (vm.name,
                                             self.service_offering_7gb.name,
                                             self.service_offering.name))

            try:
                vm.change_service_offering(self.apiclient,
                                serviceOfferingId=self.service_offering.id)
            except Exception as e:
                self.fail("Failed to change service offering of vm %s - %s" %
                                                                (vm.name, e))
            self.checkResourceCount(account=self.account, rtype=9)

            self.debug("Starting instance: %s" % vm.name)
            try:
                vm.start(self.apiclient)
            except Exception as e:
                self.fail("Failed to start instance: %s" % e)
            self.checkResourceCount(account=self.account, rtype=9)

            self.debug("Assigning VM to account: %s in domain: %s" %
                                                (self.admin.account.name,
                                                self.admin.account.domain))
            # TODO: Assign Virtual Machine function implementation

            host = self.findSuitableHost(vm)
            self.debug("Migrating instance: %s to host: %s" %
                                                        (vm.name, host.name))
            try:
                vm.migrate(self.apiclient, host.id)
            except Exception as e:
                self.fail("Failed to migrate instance: %s" % e)
            self.checkResourceCount(account=self.account, rtype=9)

            self.debug("Destroying instance: %s" % vm.name)
            try:
                vm.delete(self.apiclient)
            except Exception as e:
                self.fail("Failed to delete instance: %s" % e)

	    # Wait for expunge interval to cleanup Memory
	    wait_for_cleanup(self.apiclient, ["expunge.delay", "expunge.interval"])

            self.checkResourceCount(account=self.account, rtype=9, delete=True)
        return

    @unittest.skip("Skip")
    @attr(tags=["advanced", "advancedns","simulator"])
    @unittest.skip("Skip")
    @attr(configuration='max.account.memory')
    def test_02_deploy_multiple_vm_with_5gb_ram(self):
        """Test Deploy multiple VM with 5 GB RAM & verify the usage"""

        # Validate the following
        # 1. Create compute offering with 5 GB RAM
        # 2. Deploy multiple VMs with this service offering
        # 3. Update Resource count for the root admin Memory usage
        # 4. Memory usage should list properly

        self.debug("Creating service offering with 5 GB RAM")
        self.service_offering = ServiceOffering.create(
                                            self.apiclient,
                                            self.services["service_offering"]
                                            )
        # Adding to cleanup list after execution
        self.cleanup.append(self.service_offering)

        self.debug("Setting up account and domain hierarchy")
        self.setupAccounts()
        users =  { self.domain: self.admin,
                   self.child_domain: self.child_do_admin
                 }
        for domain, admin in users.items():
            self.account = admin
            self.domain = domain
            self.debug("Creating an instance with service offering: %s" %
                                                    self.service_offering.name)
            vm_1 = self.createInstance(service_off=self.service_offering)
            vm_2 = self.createInstance(service_off=self.service_offering)
            vm_3 = self.createInstance(service_off=self.service_offering)
            #vm_4 = self.createInstance(service_off=self.service_offering)

            self.debug("Deploying instance - Memory capacity is fully utilized")
            with self.assertRaises(Exception):
                self.createInstance(service_off=self.service_offering)

            self.checkResourceCount(account=self.account, rtype=9)
            self.debug("Destroying instance: %s" % vm_1.name)
            try:
                vm_1.delete(self.apiclient)
            except Exception as e:
                self.fail("Failed to delete instance: %s" % e)
            self.checkResourceCount(account=self.account, rtype=9)

            host = self.findSuitableHost(vm_2)
            self.debug("Migrating instance: %s to host: %s" % (vm_2.name,
                                                               host.name))
            try:
                vm_2.migrate(self.apiclient, host.id)
            except Exception as e:
                self.fail("Failed to migrate instance: %s" % e)
            self.checkResourceCount(account=self.account, rtype=9)
	    vm_2.delete(self.apiclient)
	    vm_3.delete(self.apiclient)
        return


class TestMemoryUpdateResources(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_client = super(TestMemoryUpdateResources,
                               cls).getClsTestClient().getApiClient()
        cls.services = Services().services
        # Get Zone, Domain and templates
        cls.domain = get_domain(cls.api_client, cls.services)
        cls.zone = get_zone(cls.api_client, cls.services)
	cls.services["mode"] = cls.zone.networktype

        cls.template = get_template(
                            cls.api_client,
                            cls.zone.id,
                            cls.services["ostype"]
                            )

        cls.services["virtual_machine"]["zoneid"] = cls.zone.id

        cls._cleanup = []
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
            pass
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def createInstance(self, service_off, networks=None):
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
                                networkids=networks,
                                serviceofferingid=service_off.id)
            vms = VirtualMachine.list(self.apiclient, id=vm.id, listall=True)
            self.assertIsInstance(vms,
                                  list,
                                  "List VMs should return a valid response")
            self.assertEqual(vms[0].state, "Running",
                             "Vm state should be running after deployment")
            return vm
        except Exception as e:
            self.fail("Failed to deploy an instance: %s" % e)

    def getNetwork(self, account):
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

    def checkResourceCount(self, account, rtype, delete=False):
        """Validates the resource count
            8     - CPUs
            9    - RAM
            10    - Primary (shared) storage (Volumes)
            11    - Secondary storage (Snapshots, Templates & ISOs)
            12    - Network bandwidth rate (in bps)
            13    - Number of times a OS template can be deployed"""

        allowedResourceTypes = [8,9,10,11,12,13]
	self.assertTrue(rtype in allowedResourceTypes,"Invalid resource type")

	self.debug("Updating the Memory resource count for account: %s" %
                                                    account.account.name)
        responses = Resources.updateCount(self.apiclient,
                              domainid=account.account.domainid,
                              account=account.account.name,
                              resourcetype=rtype
                              )
        self.assertIsInstance(responses, list,
                        "Update resource count should return valid response")
        response = responses[0]
        self.debug(response.resourcecount)

	if delete:
            self.assertEqual(response.resourcecount,
                         0,
                         "Resource count for %s should be 0" %
                                        get_resource_type(rtype))
        else:
            self.assertNotEqual(response.resourcecount,
                         0,
                         "Resource count for %s should not be 0" %
                                        get_resource_type(rtype)) 
        return

    def findSuitableHost(self, vm):
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

    def setupAccounts(self):

        self.debug("Creating a domain under: %s" % self.domain.name)
        self.child_domain = Domain.create(self.apiclient,
                                        services=self.services["domain"],
                                        parentdomainid=self.domain.id)
        self.child_do_admin = Account.create(
                            self.apiclient,
                            self.services["account"],
                            admin=True,
                            domainid=self.child_domain.id
                            )
        # Cleanup the resources created at end of test
        self.cleanup.append(self.child_do_admin)
        self.cleanup.append(self.child_domain)

        self.debug("Updating the Memory resource count for domain: %s" %
                                                            self.domain.name)
        Resources.updateLimit(self.apiclient,
                              resourcetype=10,
                              max=10240,
                              account=self.child_do_admin.account.name,
                              domainid=self.child_do_admin.account.domainid)

        self.debug("Creating a domain under: %s" % self.domain.name)

        self.domain = Domain.create(self.apiclient,
                                        services=self.services["domain"],
                                        parentdomainid=self.domain.id)
        self.admin = Account.create(
                                    self.apiclient,
                                    self.services["account"],
                                    admin=True,
                                    domainid=self.domain.id)
        # Cleanup the resources created at end of test	
	self.cleanup.append(self.admin)
        self.cleanup.append(self.domain)

        Resources.updateLimit(self.apiclient,
                              resourcetype=10,
                              max=5120,
                              account=self.admin.account.name,
                              domainid=self.admin.account.domainid)
        return

    @unittest.skip("Skip")
    @attr(tags=["advanced", "advancedns","simulator"])
    def test_01_deploy_vm_with_5gb_ram(self):
        """Test Deploy VM with 5 GB RAM & verify the usage"""

        # Validate the following
        # 1. Create compute offering with 5 GB RAM & Deploy VM as root admin
        # 2. Update Resource count for the root admin Memory usage

        self.debug("Creating service offering with 5 GB RAM")
        self.service_offering = ServiceOffering.create(
                                            self.apiclient,
                                            self.services["service_offering"]
                                            )
        # Adding to cleanup list after execution
        self.cleanup.append(self.service_offering)

        self.debug("Setting up account and domain hierarchy")
        self.setupAccounts()
        users = {self.domain: self.admin,
                 self.child_domain: self.child_do_admin
                 }
        for domain, admin in users.items():
            self.account = admin
            self.domain = domain
            self.debug("Creating an instance with service offering: %s" %
                                                    self.service_offering.name)
            vm = self.createInstance(service_off=self.service_offering)

            self.checkResourceCount(account=self.account, rtype=9)
            self.debug("Stopping instance: %s" % vm.name)
            try:
                vm.stop(self.apiclient)
            except Exception as e:
                self.fail("Failed to stop instance: %s" % e)
            self.checkResourceCount(account=self.account, rtype=9)

            self.debug("Creating service offering with 7 GB RAM")
            self.services["service_offering"]["memory"] = 7168
            self.service_offering_7gb = ServiceOffering.create(
                                            self.apiclient,
                                            self.services["service_offering"])
            # Adding to cleanup list after execution
            self.cleanup.append(self.service_offering_7gb)

            self.debug(
                "Upgrade service offering of instance %s from %s to %s" %
                                            (vm.name,
                                             self.service_offering.name,
                                             self.service_offering_7gb.name))

            try:
                vm.change_service_offering(self.apiclient,
                                serviceOfferingId=self.service_offering_7gb.id)
            except Exception as e:
                self.fail("Failed to change service offering of vm %s - %s" %
                                                                (vm.name, e))
            self.checkResourceCount(account=self.account, rtype=9)

            self.debug(
                "Down grade service offering of instance %s from %s to %s" %
                                            (vm.name,
                                             self.service_offering_7gb.name,
                                             self.service_offering.name))

            try:
                vm.change_service_offering(self.apiclient,
                                serviceOfferingId=self.service_offering.id)
            except Exception as e:
                self.fail("Failed to change service offering of vm %s - %s" %
                                                                (vm.name, e))
            self.checkResourceCount(account=self.account, rtype=9)

            self.debug("Starting instance: %s" % vm.name)
            try:
                vm.start(self.apiclient)
            except Exception as e:
                self.fail("Failed to start instance: %s" % e)
            self.checkResourceCount(account=self.account, rtype=9)

            host = self.findSuitableHost(vm)
            self.debug("Migrating instance: %s to host: %s" %
                                                        (vm.name, host.name))
            try:
                vm.migrate(self.apiclient, host.id)
            except Exception as e:
                self.fail("Failed to migrate instance: %s" % e)
            self.checkResourceCount(account=self.account, rtype=9)

            self.debug("Assigning VM to account: %s in domain: %s" %
                                                (self.admin.account.name,
                                                self.admin.account.domain))
            # TODO: Assign Virtual Machine function implementation

            self.debug("Destroying instance: %s" % vm.name)
            try:
                vm.delete(self.apiclient)
            except Exception as e:
                self.fail("Failed to delete instance: %s" % e)

	    # Wait for expunge interval to cleanup Memory
            wait_for_cleanup(self.apiclient, ["expunge.delay", "expunge.interval"])

            self.checkResourceCount(account=self.account, rtype=9, delete=True)
        return

    @unittest.skip("Skip")
    @attr(tags=["advanced", "advancedns","simulator"])
    def test_02_deploy_multiple_vm_with_5gb_ram(self):
        """Test Deploy multiple VM with 5 GB RAM& verify the usage"""

        # Validate the following
        # 1. Create compute offering with 5 GB RAM
        # 2. Deploy multiple VMs with this service offering
        # 3. Update Resource count for the root admin Memory usage
        # 4. Memory usage should list properly

        self.debug("Creating service offering with 5 GB RAM")
        self.service_offering = ServiceOffering.create(
                                            self.apiclient,
                                            self.services["service_offering"]
                                            )
        # Adding to cleanup list after execution
        self.cleanup.append(self.service_offering)

        self.debug("Setting up account and domain hierarchy")
        self.setupAccounts()
        users =  { self.domain: self.admin,
                   self.child_domain: self.child_do_admin
                 }
        for domain, admin in users.items():
            self.account = admin
            self.domain = domain
            self.debug("Creating an instance with service offering: %s" %
                                                    self.service_offering.name)
            vm_1 = self.createInstance(service_off=self.service_offering)
            vm_2 = self.createInstance(service_off=self.service_offering)
            vm_3 = self.createInstance(service_off=self.service_offering)
            #vm_4 = self.createInstance(service_off=self.service_offering)

            self.debug("Deploying instance - Memory capacity is fully utilized")
#            with self.assertRaises(Exception):
#                self.createInstance(service_off=self.service_offering)

            self.checkResourceCount(account=self.account, rtype=10)
            self.debug("Destroying instance: %s" % vm_1.name)
            try:
                vm_1.delete(self.apiclient)
            except Exception as e:
                self.fail("Failed to delete instance: %s" % e)
            self.checkResourceCount(account=self.account, rtype=10)

            host = self.findSuitableHost(vm_2)
            self.debug("Migrating instance: %s to host: %s" % (vm_2.name,
                                                               host.name))
            try:
                vm_2.migrate(self.apiclient, host.id)
            except Exception as e:
                self.fail("Failed to migrate instance: %s" % e)
            self.checkResourceCount(account=self.account, rtype=10)
	    vm_2.delete(self.apiclient)
	    vm_3.delete(self.apiclient)  
        return


class TestMultipleChildDomainsMemory(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_client = super(TestMultipleChildDomainsMemory,
                               cls).getClsTestClient().getApiClient()
        cls.services = Services().services
        # Get Zone, Domain and templates
        cls.domain = get_domain(cls.api_client, cls.services)
        cls.zone = get_zone(cls.api_client, cls.services)
	cls.services["mode"] = cls.zone.networktype

        cls.template = get_template(
                            cls.api_client,
                            cls.zone.id,
                            cls.services["ostype"]
                            )

        cls.services["virtual_machine"]["zoneid"] = cls.zone.id

        cls._cleanup = []
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
            pass
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    def createInstance(self, account, service_off, networks=None):
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
                                networkids=networks,
                                serviceofferingid=service_off.id)
            vms = VirtualMachine.list(self.apiclient, id=vm.id, listall=True)
            self.assertIsInstance(vms,
                                  list,
                                  "List VMs should return a valid response")
            self.assertEqual(vms[0].state, "Running",
                             "Vm state should be running after deployment")
            return vm
        except Exception as e:
            self.fail("Failed to deploy an instance: %s" % e)

    def getNetwork(self, account):
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

    def checkResourceCount(self, account, rtype, delete=False):
        """Validates the resource count
            9     - CPUs
            10    - RAM
            11    - Primary (shared) storage (Volumes)
            12    - Secondary storage (Snapshots, Templates & ISOs)
            13    - Network bandwidth rate (in bps)
            14    - Number of times a OS template can be deployed"""

        allowedResourceTypes = [9,10,11,12,13,14]
	self.assertTrue(rtype in allowedResourceTypes,"Invalid resource type")

	self.debug("Updating the Memory resource count for account: %s" %
                                                    account.account.name)
        responses = Resources.updateCount(self.apiclient,
                              domainid=account.account.domainid,
                              account=account.account.name,
                              resourcetype=rtype
                              )
        self.assertIsInstance(responses, list,
                        "Update resource count should return valid response")
        response = responses[0]
        self.debug(response.resourcecount)
        if delete:
            self.assertEqual(response.resourcecount,
                         0,
                         "Resource count for %s should be 0" %
                                        get_resource_type(rtype))
        else:
            self.assertNotEqual(response.resourcecount,
                         0,
                         "Resource count for %s should not be 0" %
                                        get_resource_type(rtype))
        return

    def setupAccounts(self):

        self.debug("Creating a domain under: %s" % self.domain.name)
        self.parent_domain = Domain.create(self.apiclient,
                                        services=self.services["domain"],
                                        parentdomainid=self.domain.id)
        self.parentd_admin = Account.create(
                            self.apiclient,
                            self.services["account"],
                            admin=True,
                            domainid=self.domain.id
                            )
         
        self.debug("Updating the Memory resource count for domain: %s" %
                                                            self.domain.name)
        Resources.updateLimit(self.apiclient,
                              resourcetype=10,
                              max=10240,
                              account=self.parentd_admin.account.name,
                              domainid=self.parentd_admin.account.domainid)
        self.debug("Creating a sub-domain under: %s" % self.parent_domain.name)
        self.cdomain_1 = Domain.create(self.apiclient,
                                        services=self.services["domain"],
                                        parentdomainid=self.parent_domain.id)

        self.debug("Creating a sub-domain under: %s" % self.parent_domain.name)
        self.cdomain_2 = Domain.create(self.apiclient,
                                        services=self.services["domain"],
                                        parentdomainid=self.parent_domain.id)

        self.cadmin_1 = Account.create(
                                        self.apiclient,
                                        self.services["account"],
                                        admin=True,
                                        domainid=self.cdomain_1.id
                                        )
                
        self.debug("Updating the Memory resource count for domain: %s" %
                                                        self.cdomain_1.name)
        Resources.updateLimit(self.apiclient,
                              resourcetype=10,
                              max=5120,
                              account=self.cadmin_1.account.name,
                              domainid=self.cadmin_1.account.domainid)

        self.cadmin_2 = Account.create(
                                        self.apiclient,
                                        self.services["account"],
                                        admin=True,
                                        domainid=self.cdomain_2.id
                                        )

	# Cleanup the resources created at end of test
        self.cleanup.append(self.cadmin_1)
        self.cleanup.append(self.cadmin_2)
        self.cleanup.append(self.cdomain_1)
	self.cleanup.append(self.cdomain_2)
	self.cleanup.append(self.parentd_admin)
        self.cleanup.append(self.parent_domain)
	
        self.debug("Updating the Memory resource count for domain: %s" %
                                                        self.cdomain_2.name)
        Resources.updateLimit(self.apiclient,
                              resourcetype=10,
                              max=5120,
                              account=self.cadmin_2.account.name,
                              domainid=self.cadmin_2.account.domainid)
        users = {
                 self.parent_domain: self.parentd_admin,
                 self.cdomain_1: self.cadmin_1,
                 self.cdomain_2: self.cadmin_2
                 }
        return users

    @unittest.skip("Skip")
    @attr(tags=["advanced", "advancedns","simulator"])
    def test_01_multiple_child_domains(self):
        """Test memory limits with multiple child domains"""

        # Validate the following
        # 1. Create Domain1 with 10 GB RAM and 2 child domains with 5 GB
        #    each.Assign 2 GB for Domain1 admin1 & Domain1 User1 .Assign 2
        #    GB for Domain2 admin1 & Domain2 User1
        # 2. Deploy VM's by Domain1 admin1/user1/ Domain2 user1/Admin1 account
        #    and verify the resource updates
        # 3. Deploy VM by admin account after reaching max parent domain limit
        # 4. Deploy VM with child account after reaching max child domain limit
        # 5. Delete user account and verify the resource updates
        # 6. Destroy user/admin account VM's and verify the child & Parent
        #    domain resource updates

        self.debug("Creating service offering with 2 GB RAM")
        self.services["service_offering"]["memory"] = 2048
        self.service_offering = ServiceOffering.create(
                                            self.apiclient,
                                            self.services["service_offering"]
                                            )
        # Adding to cleanup list after execution
        self.cleanup.append(self.service_offering)

        self.debug("Setting up account and domain hierarchy")
        self.setupAccounts()

        self.debug("Creating an instance with service offering: %s" %
                                                self.service_offering.name)
        vm_1 = self.createInstance(account=self.cadmin_1,
                                  service_off=self.service_offering)

        vm_2 = self.createInstance(account=self.cadmin_2,
                                  service_off=self.service_offering)

        self.checkResourceCount(account=self.cadmin_1, rtype=9)
        self.checkResourceCount(account=self.cadmin_2, rtype=9)

        self.debug(
            "Creating instance when Memory limit is fully used in parent domain")
        with self.assertRaises(Exception):
            self.createInstance(account=self.cadmin_1,
                                  service_off=self.service_offering)

        self.debug(
            "Creating instance when Memory limit is fully used in child domain")
        with self.assertRaises(Exception):
            self.createInstance(account=self.cadmin_1,
                                  service_off=self.service_offering)
        self.debug("Destroying instances: %s, %s" % (vm_1.name, vm_2.name))
        try:
            vm_1.delete(self.apiclient)
            vm_2.delete(self.apiclient)
        except Exception as e:
            self.fail("Failed to delete instance: %s" % e)
        self.checkResourceCount(account=self.cadmin_1, rtype=9, delete=True)
        self.checkResourceCount(account=self.cadmin_2, rtype=9, delete=True)
        return


class TestProjectsMemoryLimits(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_client = super(TestProjectsMemoryLimits,
                               cls).getClsTestClient().getApiClient()
        cls.services = Services().services
        # Get Zone, Domain and templates
        cls.domain = get_domain(cls.api_client, cls.services)
        cls.zone = get_zone(cls.api_client, cls.services)
	cls.services["mode"] = cls.zone.networktype

        cls.template = get_template(
                            cls.api_client,
                            cls.zone.id,
                            cls.services["ostype"]
                            )

        cls.services["virtual_machine"]["zoneid"] = cls.zone.id

        cls._cleanup = []
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
             admin=True
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

    def createInstance(self, project, service_off, networks=None):
        """Creates an instance in account"""
        self.debug("Deploying an instance in account: %s" %
                                                self.account.account.name)
        try:
            vm = VirtualMachine.create(
                                self.apiclient,
                                self.services["virtual_machine"],
                                templateid=self.template.id,
                                projectid=project.id,
                                networkids=networks,
                                serviceofferingid=service_off.id)
            vms = VirtualMachine.list(self.apiclient, id=vm.id, listall=True)
            self.assertIsInstance(vms,
                                  list,
                                  "List VMs should return a valid response")
            self.assertEqual(vms[0].state, "Running",
                             "Vm state should be running after deployment")
            return vm
        except Exception as e:
            self.fail("Failed to deploy an instance: %s" % e)

    def getNetwork(self, account):
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

    def checkResourceCount(self, project, rtype, delete=False):
        """Validates the resource count
            8     - CPUs
            9     - RAM
            10    - Primary (shared) storage (Volumes)
            11    - Secondary storage (Snapshots, Templates & ISOs)
            12    - Network bandwidth rate (in bps)
            13    - Number of times a OS template can be deployed"""

        allowedResourceTypes = [8,9,10,11,12,13]
	self.assertTrue(rtype in allowedResourceTypes,"Invalid resource type")

	self.debug("Updating the Memory resource count for project: %s" %
                                                                project.name)
        responses = Resources.updateCount(self.apiclient,
			      domainid = self.account.account.domainid,
                              projectid=self.project.id,
                              resourcetype=rtype)

        self.assertIsInstance(responses, list,
                        "Update resource count should return valid response")
        response = responses[0]
        self.debug(response.resourcecount) 
        return

    def findSuitableHost(self, vm):
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

    def setupProjectAccounts(self):

        self.debug("Creating a domain under: %s" % self.domain.name)
        self.domain = Domain.create(self.apiclient,
                                        services=self.services["domain"],
                                        parentdomainid=self.domain.id)
        self.admin = Account.create(
                            self.apiclient,
                            self.services["account"],
                            admin=True,
                            domainid=self.domain.id
                            )

        # Create project as a domain admin
        self.project = Project.create(self.apiclient,
                                 self.services["project"],
                                 account=self.admin.account.name,
                                 domainid=self.admin.account.domainid)
        # Cleanup created project at end of test
        self.cleanup.append(self.project)
        self.cleanup.append(self.admin)
        self.cleanup.append(self.domain)
        self.debug("Created project with domain admin with name: %s" %
                                                        self.project.name)

        projects = Project.list(self.apiclient, id=self.project.id,
                                listall=True)

        self.assertEqual(isinstance(projects, list), True,
                        "Check for a valid list projects response")
        project = projects[0]
        self.assertEqual(project.name, self.project.name,
                        "Check project name from list response")
        return

    @unittest.skip("Skip")
    @attr(tags=["advanced", "advancedns","simulator"])
    @unittest.skip("Skip")
    @attr(configuration='max.projects.memory')
    def test_01_project_limits_global_config(self):
        """Test max.projects.memory global configuration"""

        # Validate the following
        # 1. Set (max.project.cpus=10) as the max limit to
        #    Domain1 (max.account.cpus=10)
        # 2. Assign account to projects and verify the resource updates
        # 3. Deploy VM with the accounts added to the project
        # 4. Stop VM of an accounts added to the project to a new host
        # 5. Assign VM of an accounts added to the project to a new host
        # 6. Migrate VM of an accounts added to the project to a new host
        # 7. Destroy VM of an accounts added to the project to a new host
        # 8. Restore VM of an accounts added to the project to a new host
        # 9. Recover VM of an accounts added to the project to a new host

        self.service_offering = ServiceOffering.create(
                                            self.apiclient,
                                            self.services["service_offering"]
                                            )
        # Adding to cleanup list after execution
        self.cleanup.append(self.service_offering)

        self.debug("Setting up account and domain hierarchy")
        self.setupProjectAccounts()
        self.debug("Creating an instance with service offering: %s" %
                                                    self.service_offering.name)
        vm = self.createInstance(project=self.project,
                                  service_off=self.service_offering)

        self.checkResourceCount(project=self.project, rtype=9)
        self.debug("Stopping instance: %s" % vm.name)
        try:
            vm.stop(self.apiclient)
        except Exception as e:
            self.fail("Failed to stop instance: %s" % e)
        self.checkResourceCount(project=self.project, rtype=9)

        self.debug("Starting instance: %s" % vm.name)
        try:
            vm.start(self.apiclient)
        except Exception as e:
            self.fail("Failed to start instance: %s" % e)
        self.checkResourceCount(project=self.project, rtype=9)

        host = self.findSuitableHost(vm)
        self.debug("Migrating instance: %s to host: %s" %
                                                    (vm.name, host.name))
        try:
            vm.migrate(self.apiclient, host.id)
        except Exception as e:
            self.fail("Failed to migrate instance: %s" % e)
        self.checkResourceCount(project=self.project, rtype=9)

        self.debug("Destroying instance: %s" % vm.name)
        try:
            vm.delete(self.apiclient)
        except Exception as e:
            self.fail("Failed to delete instance: %s" % e)

	# Wait for expunge interval to cleanup Memory
	wait_for_cleanup(self.apiclient, ["expunge.delay", "expunge.interval"])

        self.checkResourceCount(project=self.project, rtype=9, delete=True)
        return


class TestMaxMemoryLimits(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_client = super(TestMaxMemoryLimits,
                               cls).getClsTestClient().getApiClient()
        cls.services = Services().services
        # Get Zone, Domain and templates
        cls.domain = get_domain(cls.api_client, cls.services)
        cls.zone = get_zone(cls.api_client, cls.services)
	cls.services["mode"] = cls.zone.networktype

        cls.template = get_template(
                            cls.api_client,
                            cls.zone.id,
                            cls.services["ostype"]
                            )

        cls.services["virtual_machine"]["zoneid"] = cls.zone.id

        cls._cleanup = []
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
                     admin=True
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

    def createInstance(self, service_off, account=None,
                        project=None, networks=None):
        """Creates an instance in account"""
        self.debug("Deploying an instance in account: %s" %
                                                self.account.account.name)
        try:
            if account:
                vm = VirtualMachine.create(
                                self.apiclient,
                                self.services["virtual_machine"],
                                templateid=self.template.id,
                                accountid=account.account.name,
                                domainid=account.account.domainid,
                                networkids=networks,
                                serviceofferingid=service_off.id)
            elif project:
                vm = VirtualMachine.create(
                                self.apiclient,
                                self.services["virtual_machine"],
                                templateid=self.template.id,
                                projectid=project.id,
                                networkids=networks,
                                serviceofferingid=service_off.id)
            vms = VirtualMachine.list(self.apiclient, id=vm.id, listall=True)
            self.assertIsInstance(vms,
                                  list,
                                  "List VMs should return a valid response")
            self.assertEqual(vms[0].state, "Running",
                             "Vm state should be running after deployment")
            return vm
        except Exception as e:
            self.fail("Failed to deploy an instance: %s" % e)

    def getNetwork(self, account):
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

    def checkResourceCount(self, rtype, account=None, project=None,
                             delete=False):
        """Validates the resource count
            9     - CPUs
            10    - RAM
            11    - Primary (shared) storage (Volumes)
            12    - Secondary storage (Snapshots, Templates & ISOs)
            13    - Network bandwidth rate (in bps)
            14    - Number of times a OS template can be deployed"""

        allowedResourceTypes = [9,10,11,12,13,14]
	self.assertTrue(rtype in allowedResourceTypes,"Invalid resource type")

	if account:
            self.debug("Updating the Memory resource count for account: %s" %
                                                    account.account.name)
            responses = Resources.updateCount(self.apiclient,
                              domainid=self.account.account.domainid,
                              account=account.account.name,
                              resourcetype=rtype)
        elif project:
            self.debug("Updating the Memory resource count for project: %s" %
                                                                project.name)
            responses = Resources.updateCount(self.apiclient,
					      domainid = self.account.account.domainid,			
                                              projectid=project.id,
                                              resourcetype=rtype)

        self.assertIsInstance(responses, list,
                        "Update resource count should return valid response")
        response = responses[0]
        self.debug(response.resourcecount)
        if delete:
            self.assertEqual(response.resourcecount,
                         0,
                         "Resource count for %s should be 0" %
                                        get_resource_type(rtype))
        else:
            self.assertNotEqual(response.resourcecount,
                         0,
                         "Resource count for %s should not be 0" %
                                        get_resource_type(rtype))
        return

    def findSuitableHost(self, vm):
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

    def setupAccounts(self, account_limit=2, domain_limit=2, project_limit=2):

        self.debug("Creating a domain under: %s" % self.domain.name)
    	self.child_domain = Domain.create(self.apiclient,
                                    services=self.services["domain"],
                                    parentdomainid=self.domain.id)


    	self.debug("domain crated with domain id %s" % self.child_domain.id)

    	self.child_do_admin = Account.create(
                        self.apiclient,
                        self.services["account"],
                        admin=True,
                        domainid=self.child_domain.id
                        )

    	self.debug("domain admin created for domain id %s" % 
			self.child_do_admin.account.domainid)

    	# Create project as a domain admin
    	self.project = Project.create(self.apiclient,
                             self.services["project"],
                             account=self.child_do_admin.account.name,
                             domainid=self.child_do_admin.account.domainid)
   	# Cleanup created project at end of test
    	self.cleanup.append(self.project)


    	# Cleanup accounts created
    	self.cleanup.append(self.child_do_admin)
    	self.cleanup.append(self.child_domain)

    	self.debug("Updating the Memory resource count for domain: %s" %
                                                        self.child_domain.name)
    	# Update resource limits for account 1
    	responses = Resources.updateLimit(self.apiclient,
                          resourcetype=9,
                          max=(account_limit * 1024),
                          account=self.child_do_admin.account.name,
                          domainid=self.child_do_admin.account.domainid
                          )

    	self.debug("Memory Resource count for child domain admin account is now: %s" %
									 responses.max)

    	# Update resource limits for project
    	responses = Resources.updateLimit(self.apiclient,
                          resourcetype=9,
                          max=(project_limit * 1024),
                          projectid=self.project.id)

    	self.debug("Memory Resource count for project is now")
    	self.debug(responses.max)

    	# TODO: Update the Memory limit for domain only
    	responses = Resources.updateLimit(self.apiclient,
                           resourcetype=9,
                       max=(domain_limit * 1024),
                       domainid=self.child_domain.id)

     	self.debug("Memory Resource count for domain %s with id %s is now %s" % 
			    (responses.domain, responses.domainid, responses.max))
     	return	
 
    @unittest.skip("Skip")
    @attr(tags=["advanced", "advancedns","simulator"])
    def test_01_deploy_vm_domain_limit_reached(self):
    	"""Test Try to deploy VM with admin account where account has not used
           the resources but @ domain they are not available"""

    	# Validate the following
    	# 1. Try to deploy VM with admin account where account has not used the
    	#    resources but @ domain they are not available
    	# 2. Deploy VM should error out saying  ResourceAllocationException
    	#    with "resource limit exceeds"

    	self.debug("Creating service offering with 5 GB RAM")
    	self.service_offering = ServiceOffering.create(
                                        self.apiclient,
                                        self.services["service_offering"]
                                        )
    	# Adding to cleanup list after execution
    	self.cleanup.append(self.service_offering)

    	self.debug("Setting up account and domain hierarchy")
    	self.setupAccounts(account_limit=8, domain_limit=4)

    	self.debug("Creating instance with domain %s and admin account %s" % 
		  			(self.child_do_admin.account.domainid,
					     self.child_do_admin.account.name))

    	with self.assertRaises(Exception):
        	self.createInstance(account=self.child_do_admin,
                              service_off=self.service_offering)
    	return 

    @unittest.skip("Skip")
    @attr(tags=["advanced", "advancedns","simulator"])
    def test_02_deploy_vm_account_limit_reached(self):
    	"""Test Try to deploy VM with admin account where account has used
           the resources but @ domain they are available"""

    	# Validate the following
    	# 1. Try to deploy VM with admin account where account has used the
    	#    resources but @ domain they are available
    	# 2. Deploy VM should error out saying  ResourceAllocationException
    	#    with "resource limit exceeds"

    	self.debug("Creating service offering with 5 GB RAM")
    	self.service_offering = ServiceOffering.create(
                                        self.apiclient,
                                        self.services["service_offering"]
                                        )
    	# Adding to cleanup list after execution
    	self.cleanup.append(self.service_offering)

    	self.debug("Setting up account and domain hierarchy")
    	self.setupAccounts(account_limit=7, domain_limit=14)

    	self.debug("Deploying instance with account: %s" %
                                                self.child_do_admin.account.name)
    	self.createInstance(account=self.child_do_admin,
                              service_off=self.service_offering)

    	#self.checkResourceCount(account=self.admin_1, rtype=10)

    	self.debug("Deploying instance in account 1 when Memory limit is reached")

    	with self.assertRaises(Exception):
        	self.createInstance(account=self.child_do_admin,
                              service_off=self.service_offering)
    	return 

    @unittest.skip("Skip")
    @attr(tags=["advanced", "advancedns","simulator"])
    def test_03_deploy_vm_project_limit_reached(self):
    	"""Test TTry to deploy VM with admin account where account has not used
   	   the resources but @ project they are not available"""

    	# Validate the following
    	# 1. Try to deploy VM with admin account where account has not used the
    	#    resources but @ project they are not available
    	# 2. Deploy VM should error out saying  ResourceAllocationException
    	#    with "resource limit exceeds"

    	self.debug("Creating service offering with 5 GB RAM")
    	self.service_offering = ServiceOffering.create(
                                        self.apiclient,
                                        self.services["service_offering"]
                                        )
    	# Adding to cleanup list after execution
    	self.cleanup.append(self.service_offering)

    	self.debug("Setting up account and domain hierarchy")
    	self.setupAccounts(account_limit=8,domain_limit=8, project_limit=4)

    	self.debug("Deploying instance with project: %s" % self.project.name)
    	with self.assertRaises(Exception):
        	self.createInstance(project = self.project,
                            service_off=self.service_offering)
    	return 

    @unittest.skip("Skip")
    @attr(tags=["advanced", "advancedns"])
    def test_04_deployVm__account_limit_reached(self):
    	"""Test Try to deploy VM with admin account where account has used
           the resources but @ project they are available"""

    	# Validate the following
    	# 1. Try to deploy VM with admin account where account has used the
    	#    resources but @ project they are available
    	# 2. Deploy VM should error out saying  ResourceAllocationException
    	#    with "resource limit exceeds"

    	self.debug("Creating service offering with 5 GB RAM")
    	self.service_offering = ServiceOffering.create(
                                        self.apiclient,
                                        self.services["service_offering"]
                                        )
    	# Adding to cleanup list after execution
    	self.cleanup.append(self.service_offering)

    	self.debug("Setting up account and domain hierarchy")
    	self.setupAccounts(account_limit=6, project_limit=12, domain_limit=12)

    	self.debug("Deploying instance with account: %s" %
                                                self.child_do_admin.account.name)
    	self.createInstance(account=self.child_do_admin,
                              service_off=self.service_offering)

    	#self.checkResourceCount(account=self.admin_1, rtype=9)

    	self.debug("Deploying instance in account: %s when memory limit is reached" %
                                                self.child_do_admin.account.name)

    	with self.assertRaises(Exception):
        	self.createInstance( project=self.project,
                             service_off=self.service_offering )
    	return 
