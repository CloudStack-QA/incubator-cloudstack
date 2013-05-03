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
    """
    """

    def __init__(self):
        self.services = {
            "domain": {
                "name": "Domain",
            },
            "account": {
                "email": "test@test.com",
                "firstname": "Test",
                "lastname": "User",
                "username": "test",
                # Random characters are appended for unique
                # username
                "password": "password",
		"accountUUID": "account1",
		"userUUID": "user1"
            },
            "user": {
                "email": "test@test.com",
                "firstname": "Test",
                "lastname": "User",
                "username": "test",
                # Random characters are appended for unique
                # username
                "password": "password",
		"userUUID": "user2"
            },
	    "domain": {
		"name": "test",
		"domainUUID": "domain1"
	    },
            "ostype": 'CentOS 5.3 (64-bit)',
	    "region": {
		"regionid": "2",
		"regionname": "Region2",
		"regionendpoint": "http://region2:8080/client"
	    }
        }


class TestRegions(cloudstackTestCase):
    """
	Testing Regions related Apis 
    """
    @classmethod
    def setUpClass(cls):
        cls.api_client = super(TestRegions, cls).getClsTestClient().getApiClient()
        cls.services = Services().services
	cls.domain = get_domain(cls.api_client, cls.services)

        return

    @unittest.skip("skipped - more validation needs to be done")
    def test_createAccountWithUUID(self):
	"""
	    Test to create an account by passing id parameter
	"""
        account = Account.create(
            self.api_client,
            self.services["account"],
            domainid=self.domain.id
	)
	return

    @unittest.skip("skipped - more validation needs to be done")
    def test_createUserWithUUID(self):
	"""
	    Test to create a user by passing id parameter
	"""
        user = User.create(
            self.api_client,
            self.services["user"],
	    account="Admin",
            domainid=self.domain.id
	)
	return
	
    @unittest.skip("skipped - more validation needs to be done")
    def test_createdomainWithUUID(self):
	"""
	    Test to create a domain by passing id parameter
	"""
        domain = Domain.create(
            self.api_client,
            self.services["domain"]
	)
	return

    @attr(tags=["basic", "advanced"])
    def test_createRegion(self):
	"""
	    Test for add Region
	"""
	
	region = Region.create(self.api_client,
		     self.services["region"]
	)

	list_region = Region.list(self.api_client,
		     id=self.services["region"]["regionid"]
	)
	
	self.assertEqual(
                         isinstance(list_region, list),
                         True,
                         "Check for list Region response"
                         )
        region_response = list_region[0]

	print (region_response)
	print (self.services["region"])
	
        self.assertEqual(
                            str(region_response.id),
                            self.services["region"]["regionid"],
                            "listRegion response does not match with region Id created" 
                        )

        self.assertEqual(
                            region_response.name,
                            self.services["region"]["regionname"],
                            "listRegion response does not match with region name created"
                        )
        self.assertEqual(
                            region_response.endpoint,
                            self.services["region"]["regionendpoint"],
                            "listRegion response does not match with region endpoint created"
                        )

	region = region.delete(self.api_client)

	return

    @attr(tags=["basic", "advanced"])
    def test_createDupRegion(self):
	"""
	    Test for duplicate checks on id and name parameters when adding regions
	"""

	self.services["region"]["regionid"]="5"
        self.services["region"]["regionname"]="Region5"
        self.services["region"]["regionendpoint"]="http://region5:8080/client"

	
	region = Region.create(self.api_client,
		     self.services["region"]
	)

	list_region = Region.list(self.api_client,
		     id=self.services["region"]["regionid"]
	)
	
	self.assertEqual(
                         isinstance(list_region, list),
                         True
			)
	"""
        Creating regions with duplicate id should not be allowed
        """

	self.services["region"]["regionid"]="5"
        self.services["region"]["regionname"]="Region51"
        self.services["region"]["regionendpoint"]="http://region51:8080/client"

	try:
	    region = Region.create(self.api_client,
		     self.services["region"]
	    )
	    self.assertIsNone(region,
                         "Creating regions with duplicate id is allowed"
			)
	except:
	    print " Creating Region with duplicate Id is not allowed"
	    pass

	"""
	Creating regions with duplicate name should not be allowed
	"""

	self.services["region"]["regionid"]="51"
        self.services["region"]["regionname"]="Region5"
        self.services["region"]["regionendpoint"]="http://region51:8080/client"

	try:
	    region = Region.create(self.api_client,
		     self.services["region"]
	    )
	except:
	    print " Creating Region with duplicate Name is not allowed"
	    pass

	region.delete(self.api_client)

	return

    @attr(tags=["basic", "advanced"])
    def test_updateRegion(self):
	"""
		Test for update Region
	"""

	self.services["region"]["regionid"]="3"	
	self.services["region"]["regionname"]="Region3"
	self.services["region"]["regionendpoint"]="http://region3:8080/client"
	region = Region.create(self.api_client,
		     self.services["region"]
	)

	self.services["region"]["regionname"]="Region3upd"
	self.services["region"]["regionendpoint"]="http://region3upd:8080/client"
	
	updated_region = region.update(self.api_client,
                          self.services["region"]
	)

	list_region = Region.list(self.api_client,
				id=self.services["region"]["regionid"]
	)
	
	self.assertEqual(
                         isinstance(list_region, list),
                         True,
                         "Check for list Region response"
                         )
        region_response = list_region[0]
	
        self.assertEqual(
                            str(region_response.id),
                            self.services["region"]["regionid"],
                            "listRegion response does not match with region Id created" 
                        )

        self.assertEqual(
                            region_response.name,
                            self.services["region"]["regionname"],
                            "listRegion response does not match with region name created"
                        )
        self.assertEqual(
                            region_response.endpoint,
                            self.services["region"]["regionendpoint"],
                            "listRegion response does not match with region endpoint created"
                        )

	region.delete(self.api_client)

	return

    @attr(tags=["basic", "advanced"])
    def test_deleteRegion(self):
	"""
		Test for delete Region
	"""
	
	self.services["region"]["regionid"]="4"	
	self.services["region"]["regionname"]="Region4"
	self.services["region"]["regionendpoint"]="http://region4:8080/client"

	region = Region.create(self.api_client,
		     self.services["region"]
	)

	list_region = Region.list(self.api_client,
		     id=self.services["region"]["regionid"]
	)

	print (list_region);
	
	self.assertEqual(
                         len(list_region),
                         1,
			 "Check for Region response"
			)

	region = region.delete(self.api_client)

	list_region = Region.list(self.api_client,
		     id=self.services["region"]["regionid"]
	)

	print (list_region);
	
	self.assertIsNone(list_region,
                         "Check for empty Region response"
                         )

	return



        @classmethod
        def tearDown(cls):

            try:
                cls.api_client = super(TestRegions, cls).getClsTestClient().getApiClient()
                #Clean up
                cleanup_resources(cls.api_client, cls.cleanup)
            except Exception as e:
                raise Exception("Warning: Exception during cleanup : %s" % e)
