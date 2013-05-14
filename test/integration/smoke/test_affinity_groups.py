#!/usr/bin/env python
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

from marvin.cloudstackTestCase import *
from marvin.cloudstackAPI import *
from marvin.integration.lib.utils import *
from marvin.integration.lib.base import *
from marvin.integration.lib.common import *
from marvin import remoteSSHClient
from nose.plugins.attrib import attr

class Services:
    """Test Account Services
    """

    def __init__(self):
        self.services = {
            "domain": {
                "name": "Domain",
            },
            "account": {
                "email": "newtest@test.com",
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
                # in MHz
                "memory": 64,
                # In MBs
            },
            "ostype": 'CentOS 5.3 (64-bit)',
            "host_anti_affinity_0": {
                    "name": "TestAffGrp_HA_0",
                    "type": "host anti-affinity",
                },
            "host_anti_affinity_1": {
                    "name": "TestAffGrp_HA_1",
                    "type": "host anti-affinity",
                },
            "virtual_machine" : {
                "hypervisor" : "KVM",
            },
            "new_domain": {
                "name": "New Domain",
            },
            "new_account": {
                "email": "domain@test.com",
                "firstname": "Domain",
                "lastname": "Admin",
                "username": "do_admin",
                # Random characters are appended for unique
                # username
                "password": "password",
            },
        }

class TestCreateAffinityGroup(cloudstackTestCase):
    """
    Test various scenarios for Create Affinity Group API
    """

    @classmethod
    def setUpClass(cls):    

        cls.api_client = super(TestCreateAffinityGroup, cls).getClsTestClient().getApiClient()
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

        cls.services["template"] = cls.template.id
        cls.services["zoneid"] = cls.zone.id

        cls.account = Account.create(
            cls.api_client,
            cls.services["account"],
            domainid=cls.domain.id
        )

        cls.services["account"] = cls.account.name

        cls.service_offering = ServiceOffering.create(
            cls.api_client,
            cls.services["service_offering"]
        )

        cls._cleanup = [
            cls.service_offering,
            cls.account,
        ]
        return
   
    def setUp(self):
        self.apiclient = self.testClient.getApiClient()
        self.dbclient = self.testClient.getDbConnection()
        self.cleanup = []

    def tearDown(self):
        try:
            # Clean up, terminate the created instance, volumes and snapshots
            cleanup_resources(self.apiclient, self.cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return
 
    @classmethod
    def tearDown(cls):
        try:
            cls.api_client = super(TestCreateAffinityGroup, cls).getClsTestClient().getApiClient()
            #Clean up, terminate the created templates
            cleanup_resources(cls.api_client, cls._cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
   
    def create_aff_grp(self, api_client=None, aff_grp=None, 
                  acc=None, domainid=None):
        
        if api_client == None:
            api_client = self.api_client
        if aff_grp == None:
            self.services["host_anti_affinity_0"]
        if acc == None:
            acc = self.account.name
        if domainid == None:
            domainid = self.domain.id

        try:
            self.aff_grp = AffinityGroup.create(api_client, aff_grp, acc, domainid)
        except Exception as e:
            raise Exception("Error: Creation of Affinity Group failed : %s" %e)
       
    @attr(tags=["simulator", "basic", "advanced"])
    def test_01_admin_create_aff_grp(self):
  
        self.create_aff_grp(aff_grp=self.services["host_anti_affinity_0"])
        self.debug("Created Affinity Group: %s" %self.aff_grp.name) 
        
        list_aff_grps = AffinityGroup.list(self.api_client)
        AffinityGroup.delete(self.api_client, list_aff_grps[0].name)
        self.debug("Deleted Affinity Group: %s" %list_aff_grps[0].name)
    

    @attr(tags=["simulator", "basic", "advanced"])
    def test_02_doadmin_create_aff_grp(self):

        self.new_domain = Domain.create(self.api_client, self.services["new_domain"])
        self.do_admin = Account.create(self.api_client, self.services["new_account"],
                                      admin=True, domainid=self.new_domain.id)
        self.cleanup.append(self.do_admin)
        self.cleanup.append(self.new_domain)

        self.create_aff_grp(aff_grp=self.services["host_anti_affinity_0"],
                            acc=self.do_admin.name, domainid=self.new_domain.id)

        list_aff_grps = AffinityGroup.list(self.api_client, 
                            acc=self.do_admin.name, domainid=self.new_domain.id)
        
        AffinityGroup.delete(self.api_client, list_aff_grps[0].name)
        self.debug("Deleted Affinity Group: %s" %list_aff_grps[0].name)
 

    @attr(tags=["simulator", "basic", "advanced"])
    def test_03_user_create_aff_grp(self):

        self.user = Account.create(self.api_client, self.services["new_account"],
                                  domainid=self.domain.id)

        self.cleanup.append(self.user)
        self.create_aff_grp(aff_grp=self.services["host_anti_affinity_0"],
                            acc=self.user.name, domainid=self.domain.id)
        
        list_aff_grps = AffinityGroup.list(self.api_client, 
                            acc=self.user.name, domainid=self.domain.id)
        
        AffinityGroup.delete(self.api_client, list_aff_grps[0].name)
        self.debug("Deleted Affinity Group: %s" %list_aff_grps[0].name)
 

    @attr(tags=["simulator", "basic", "advanced"])
    def test_04_user_create_aff_grp_existing_name(self):

        self.user = Account.create(self.api_client, self.services["new_account"],
                                  domainid=self.domain.id)
        
        self.cleanup.append(self.user)
        self.create_aff_grp(aff_grp=self.services["host_anti_affinity_0"],
                            acc=self.user.name, domainid=self.domain.id)
        with self.assertRaises(Exception):
            self.create_aff_grp(aff_grp=self.services["host_anti_affinity_0"],
                            acc=self.user.name, domainid=self.domain.id)

        AffinityGroup.delete(self.api_client, list_aff_grps[0].name)
        self.debug("Deleted Affinity Group: %s" %list_aff_grps[0].name)
    
    @attr(tags=["simulator", "basic", "advanced"])
    def test_05_create_aff_grp_same_name_diff_acc(self):
        
        self.user = Account.create(self.api_client, self.services["new_account"],
                                  domainid=self.domain.id)
        
        self.cleanup.append(self.user)
        self.create_aff_grp(aff_grp=self.services["host_anti_affinity_0"],
                            acc=self.user.name, domainid=self.domain.id)

        try:
            self.create_aff_grp(aff_grp=self.services["host_anti_affinity_0"])
        except Exception:
            self.debug("Error: Creating affinity group with same name from different account failed.")    
    

    @attr(tags=["simulator", "basic", "advanced"])
    def test_06_create_aff_grp_nonexisting_type(self):
        
        self.non_existing_aff_grp = {
                    "name": "TestAffGrp_HA",
                    "type": "Incorrect type",
                }
        with self.assertRaises(Exception):
            self.create_aff_grp(aff_grp=self.non_existing_aff_grp)

class TestListAffinityGroups(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):    

        cls.api_client = super(TestListAffinityGroups, cls).getClsTestClient().getApiClient()
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

        cls.services["template"] = cls.template.id
        cls.services["zoneid"] = cls.zone.id

        cls.account = Account.create(
            cls.api_client,
            cls.services["account"],
            domainid=cls.domain.id
        )

        cls.services["account"] = cls.account.name

        cls.service_offering = ServiceOffering.create(
            cls.api_client,
            cls.services["service_offering"]
        )

        cls.aff_grp = []
        cls.__cleanup = [
            cls.service_offering,
            cls.account,
        ]
        return
   
    def setUp(self):
        self.apiclient = self.testClient.getApiClient()
        self.dbclient = self.testClient.getDbConnection()
        self.cleanup = []

    def tearDown(self):
        try:
            cls.api_client = super(TestListAffinityGroups, cls).getClsTestClient().getApiClient()
            #Clean up, terminate the created templates
            cleanup_resources(cls.api_client, cls.cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)

 
    @classmethod
    def tearDown(cls):
        try:
            cls.api_client = super(TestListAffinityGroups, cls).getClsTestClient().getApiClient()
            #Clean up, terminate the created templates
            cleanup_resources(cls.api_client, cls.__cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
   
    def create_aff_grp(self, api_client=None, aff_grp=None, 
                  acc=None, domainid=None):
        
        if api_client == None:
            api_client = self.api_client
        if aff_grp == None:
            self.services["host_anti_affinity_0"]
        if acc == None:
            acc = self.account.name
        if domainid == None:
            domainid = self.domain.id

        try:
            self.aff_grp.append(AffinityGroup.create(api_client, 
                                                     aff_grp, acc, domainid))
        except Exception as e:
            raise Exception("Error: Creation of Affinity Group failed : %s" %e)
 
    def create_vm_in_aff_grps(self, ag_list):
	#try:
	self.debug('Creating VM in AffinityGroup=%s' % ag_list[0])
	vm = VirtualMachine.create(
            	self.api_client,
            	self.services["virtual_machine"],
            	templateid=self.template.id,
            	#accountid=self.account.name,
            	#domainid=self.account.domainid,
            	serviceofferingid=self.service_offering.id,
            	affinitygroupnames=ag_list
            )
	self.debug('Created VM=%s in Affinity Group=%s' % 
		    (vm.id, ag_list[0]))
	#except Exception:
	    #self.debug('Unable to create VM in a Affinity Group=%s'
       #                 % ag_list[0])
	
	list_vm = list_virtual_machines(self.api_client, id=vm.id)

        self.assertEqual(isinstance(list_vm, list), True,
                         "Check list response returns a valid list")
        self.assertNotEqual(len(list_vm),0,
                            "Check VM available in List Virtual Machines")
        
        vm_response = list_vm[0]
        self.assertEqual(vm_response.state, 'Running',
                         msg="VM is not in Running state")
   
        return vm, vm_response.hostid
    
    def test_01_list_aff_grps_for_vm(self):
        """
           List affinity group for a vm 
        """
        self.create_aff_grp(aff_grp=self.services["host_anti_affinity_0"])
        self.debug("Created Affinity Group: %s" %self.aff_grp[0].name) 
        
        vm, hostid = self.create_vm_in_aff_grps([self.aff_grp[0].name])
        list_aff_grps = AffinityGroup.list(self.api_client, 
                                           virtualmachineid=vm.id)
       
        self.assertEqual(list_aff_grps[0].name, self.aff_grp[0].name,
                         "Listing Affinity Group by VM id failed") 
        
        vm.delete(self.api_client)
        #Wait for expunge interval to cleanup VM
        wait_for_cleanup(self.apiclient, ["expunge.delay", "expunge.interval"])
        AffinityGroup.delete(self.api_client, list_aff_grps[0].name)
        self.debug("Deleted Affinity Group: %s" %list_aff_grps[0].name)
     
    def test_02_list_multiple_aff_grps_for_vm(self):
        """
           List multiple affinity groups associated with a vm 
        """

        #AffinityGroup.delete(self.api_client, "TestAffGrp_HA_0")
        #AffinityGroup.delete(self.api_client, "TestAffGrp_HA_1")
        #return        
 
        self.create_aff_grp(aff_grp=self.services["host_anti_affinity_0"])
        self.debug("Created Affinity Group: %s" %self.aff_grp[0].name) 

        self.create_aff_grp(aff_grp=self.services["host_anti_affinity_1"])
        self.debug("Created Affinity Group: %s" %self.aff_grp[1].name) 
   
        aff_grps_names = [self.aff_grp[0].name, self.aff_grp[1].name] 
        vm, hostid = self.create_vm_in_aff_grps(aff_grps_names)
        list_aff_grps = AffinityGroup.list(self.api_client, 
                                           virtualmachineid=vm.id)
        
        list_aff_grps_names = [list_aff_grps[0].name, list_aff_grps[1].name]
        
        aff_grps_names.sort()
        list_aff_grps_names.sort() 
        self.assertEqual(aff_grps_names, list_aff_grps_names,
                         "One of the Affinity Groups is missing %s" 
                         %list_aff_grps_names) 
 
 
        vm.delete(self.api_client)
        #Wait for expunge interval to cleanup VM
        wait_for_cleanup(self.apiclient, ["expunge.delay", "expunge.interval"])
        
        for i in aff_grps_names:
            AffinityGroup.delete(self.api_client, i)
            self.debug("Deleted Affinity Group: %s" %i)
       
    def test_03_list_aff_grps_by_id(self):
        """
           List affinity groups by id 
        """
        self.create_aff_grp(aff_grp=self.services["host_anti_affinity_0"])
        self.debug("Created Affinity Group: %s" %self.aff_grp[0].name) 
        
        vm, hostid = self.create_vm_in_aff_grps([self.aff_grp[0].name])
        list_aff_grps = AffinityGroup.list(self.api_client, 
                                           id=self.aff_grp[0].id)
       
        self.assertEqual(list_aff_grps[0].name, self.aff_grp[0].name,
                         "Listing Affinity Group by VM id failed") 
        
        vm.delete(self.api_client)
        #Wait for expunge interval to cleanup VM
        wait_for_cleanup(self.apiclient, ["expunge.delay", "expunge.interval"])
        AffinityGroup.delete(self.api_client, list_aff_grps[0].name)
        self.debug("Deleted Affinity Group: %s" %list_aff_grps[0].name)
      

    
@unittest.skip("WIP")
class TestDeployVmWithAffinityGroup(cloudstackTestCase):
    """
    Deploys a virtual machine into a user account
    using the small service offering and builtin template
    """

    @classmethod
    def setUpClass(cls):
        cls.api_client = super(TestDeployVmWithAffinityGroup, cls).getClsTestClient().getApiClient()
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

        cls.services["template"] = cls.template.id
        cls.services["zoneid"] = cls.zone.id

        cls.account = Account.create(
            cls.api_client,
            cls.services["account"],
            domainid=cls.domain.id
        )

        cls.services["account"] = cls.account.name

        cls.service_offering = ServiceOffering.create(
            cls.api_client,
            cls.services["service_offering"]
        )

        cls.ag = AffinityGroup.create(cls.api_client, cls.services["virtual_machine"]["affinity"],
            account=cls.services["account"], domainid=cls.domain.id)

        cls._cleanup = [
            cls.service_offering,
            cls.account,
        ]
        return
    
    @classmethod
    def tearDown(cls):
        try:
            cls.api_client = super(TestDeployVmWithAffinityGroup, cls).getClsTestClient().getApiClient()
            #Clean up, terminate the created templates
            cleanup_resources(cls.api_client, cls.cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
    
    def create_vm_in_ag(self, ag_list):
	try:
	    self.debug('Creating VM in AffinityGroup=%s' % ag_list[0])
	    vm = VirtualMachine.create(
            	self.api_client,
            	self.services["virtual_machine"],
            	templateid=self.template.id,
            	accountid=self.account.name,
            	domainid=self.account.domainid,
            	serviceofferingid=self.service_offering.id,
            	affinitygroupnames=ag_list
            )
	    self.debug('Created VM=%s in Affinity Group=%s' % 
		    (vm.id, ag_list[0]))
	except Exception:
	    self.debug('Unable to create VM in a Affinity Group=%s'
                        % ag_list[0])
	
	list_vm = list_virtual_machines(self.api_client, id=vm.id)

        self.assertEqual(isinstance(list_vm, list), True,
                         "Check list response returns a valid list")
        self.assertNotEqual(len(list_vm),0,
                            "Check VM available in List Virtual Machines")
        
        vm_response = list_vm[0]
        self.assertEqual(vm_response.state, 'Running',
                         msg="VM is not in Running state")
   
        return vm, vm_response.hostid
 
    @attr(tags=["simulator", "basic", "advanced", "multihost"])
    def test_01_deploy_vm_anti_affinity_group(self):
        """
        test DeployVM in anti-affinity groups

        deploy VM1 and VM2 in the same host-anti-affinity groups
        Verify that the vms are deployed on separate hosts
        """
        #deploy VM1 in affinity group created in setUp
        vm1, host_vm1 = self.create_vm_in_ag([self.ag.name])

        #deploy VM2 in affinity group created in setUp
        vm2, host_vm2 = self.create_vm_in_ag([self.ag.name])

        self.assertNotEqual(host_vm1, host_vm2,
            msg="Both VMs of affinity group %s are on the same host" % self.ag.name)

        
