
""" P1 tests for resource limits
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
                                        Host
                                        )
from marvin.integration.lib.common import (get_domain,
                                        get_zone,
                                        get_template,
                                        cleanup_resources,
                                        )


class Services:
    """Test resource limit services
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
                                "cpunumber": 2,
                                "cpuspeed": 100,    # in MHz
                                "memory": 128,    # In MBs
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


@unittest.skip("Skipping - Work in progress")
class TestCPULimits(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_client = super(TestCPULimits,
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

    def create_Instance(self, service_off, networks=None):
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

    def get_Resource_Type(self, resource_id):
        """Returns resource type"""

        lookup = {1: "VM", 2: "Public IP", 3: "Volume", 4: "Snapshot",
                     5: "Template", 6: "Projects", 7: "Network", 8: "VPC",
                     9: "CPUs", 10: "RAM",
                     11: "Primary (shared) storage (Volumes)",
                     12: "Secondary storage (Snapshots, Templates & ISOs)",
                     13: "Network bandwidth rate (in bps)",
                     14: "Number of times a OS template can be deployed"}
        return lookup[resource_id]

    def check_Resource_Count(self, account, rtype, delete=False):
        """Validates the resource count
            9     - CPUs
            10    - RAM
            11    - Primary (shared) storage (Volumes)
            12    - Secondary storage (Snapshots, Templates & ISOs)
            13    - Network bandwidth rate (in bps)
            14    - Number of times a OS template can be deployed"""

        self.debug("Updating the CPU resource count for account: %s" %
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
                                        self.get_Resource_Type(rtype))
        else:
            self.assertNotEqual(response.resourcecount,
                         0,
                         "Resource count for %s should not be 0" %
                                        self.get_Resource_Type(rtype))
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

    @attr(tags=["advanced", "advancedns"])
    def test_01_deploy_vm_with_5_cpus(self):
        """Test Deploy VM with 5 core CPU & verify the usage"""

        # Validate the following
        # 1. Deploy VM with 5 core CPU & verify the usage
        # 2. Stop VM & verify the update resource limit of Root Admin Account
        # 3. Start VM & verify the update resource limit of Root Admin Account
        # 4. Migrate VM & verify update resource limit of Root Admin Account
        # 5. Destroy VM & verify update resource limit of Root Admin Account

        self.debug("Creating service offering with 5 CPU cores")
        self.service_offering = ServiceOffering.create(
                                            self.apiclient,
                                            self.services["service_offering"]
                                            )
        # Adding to cleanup list after execution
        self.cleanup.append(self.service_offering)

        self.debug("Creating an instance with service offering: %s" %
                                                    self.service_offering.name)
        vm = self.create_Instance(service_off=self.service_offering)

        self.check_Resource_Count(account=self.account, rtype=9)
        self.debug("Stopping instance: %s" % vm.name)
        try:
            vm.stop(self.apiclient)
        except Exception as e:
            self.fail("Failed to stop instance: %s" % e)
        self.check_Resource_Count(account=self.account, rtype=9)

        self.debug("Starting instance: %s" % vm.name)
        try:
            vm.start(self.apiclient)
        except Exception as e:
            self.fail("Failed to start instance: %s" % e)
        self.check_Resource_Count(account=self.account, rtype=9)

        host = self.find_Suitable_Host(vm)
        self.debug("Migrating instance: %s to host: %s" % (vm.name, host.name))
        try:
            vm.migrate(self.apiclient, host.id)
        except Exception as e:
            self.fail("Failed to migrate instance: %s" % e)
        self.check_Resource_Count(account=self.account, rtype=9)

        self.debug("Destroying instance: %s" % vm.name)
        try:
            vm.delete(self.apiclient)
        except Exception as e:
            self.fail("Failed to delete instance: %s" % e)
        self.check_Resource_Count(account=self.account, rtype=9, delete=True)
        return

    @attr(tags=["advanced", "advancedns"])
    def test_02_deploy_multiple_vm_with_5_cpus(self):
        """Test Deploy multiple VM with 5 core CPU & verify the usage"""

        # Validate the following
        # 1. Create compute offering with 5 core CPU
        # 2. Deploy multiple VMs with this service offering
        # 3. Update Resource count for the root admin CPU usage
        # 4. CPU usage should list properly
        # 5. Destroy one VM among multiple VM's and verify the resource limit
        # 6. Migrate VM from & verify resource updates
        # 7. List resources of Root Admin for CPU
        # 8. Failed to deploy VM and verify the resource usage

        self.debug("Creating service offering with 5 CPU cores")
        self.service_offering = ServiceOffering.create(
                                            self.apiclient,
                                            self.services["service_offering"]
                                            )
        # Adding to cleanup list after execution
        self.cleanup.append(self.service_offering)

        self.debug("Creating an instance with service offering: %s" %
                                                    self.service_offering.name)
        vm_1 = self.create_Instance(service_off=self.service_offering)
        vm_2 = self.create_Instance(service_off=self.service_offering)
        self.create_Instance(service_off=self.service_offering)
        self.create_Instance(service_off=self.service_offering)

        self.check_Resource_Count(account=self.account, rtype=9)
        self.debug("Destroying instance: %s" % vm_1.name)
        try:
            vm_1.delete(self.apiclient)
        except Exception as e:
            self.fail("Failed to delete instance: %s" % e)
        self.check_Resource_Count(account=self.account, rtype=9)

        host = self.find_Suitable_Host(vm_2)
        self.debug("Migrating instance: %s to host: %s" % (vm_2.name,
                                                           host.name))
        try:
            vm_2.migrate(self.apiclient, host.id)
        except Exception as e:
            self.fail("Failed to migrate instance: %s" % e)
        self.check_Resource_Count(account=self.account, rtype=9)
        return
