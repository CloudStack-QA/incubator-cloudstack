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

""" P1 tests for Upload Volumes
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
#Import System modules
import os
import urllib
import time
import tempfile


class Services:
    """Test Volume Services
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
                                    "cpuspeed": 100,    # in MHz
                                    "memory": 128,       # In MBs
                        },
                        "disk_offering": {
                                    "displaytext": "Small",
                                    "name": "Small",
                                    "disksize": 1
                        },
                        "volume": {
                                "diskname": "UploadedVolume",
                                "url": "http://10.147.28.7/templates/centos5.5hvm.vhd.gz",
                                "format": 'VHD',
                        },
                        "volumes": {
                            # If you are testing for other hypervisor than XenServer,
                            # Please change this dict according to following
                            # "HYPERVISOR" : {
                            #    0: {
                            #        """Configs for volume type 1
                            #            supported by HYPERVISOR"""
                            # Xenserver specific settings for volumes
                            "xenserver": {
                                0: {
                                     "diskname": "Volume_VHD_Format",
                                     "url": "http://10.147.28.7/templates/centos5.5hvm.vhd.gz",
                                     "format": 'VHD',
                                     },
                                },
                        },
                        "virtual_machine": {
                                    "displayname": "testVM",
                                    "hypervisor": 'XenServer',
                                    "protocol": 'TCP',
                                    "ssh_port": 22,
                                    "username": "root",
                                    "password": "password",
                                    "privateport": 22,
                                    "publicport": 22,
                         },
                        "sleep": 50,
                        "ostype": 'CentOS 5.3 (64-bit)',
                        "mode": 'advanced',
                    }


class TestUploadDataDisk(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_client = super(
                               TestUploadDataDisk,
                               cls
                               ).getClsTestClient().getApiClient()
        cls.services = Services().services

        # Get Zone, Domain and templates
        cls.domain = get_domain(cls.api_client, cls.services)
        cls.zone = get_zone(cls.api_client, cls.services)
        template = get_template(
                            cls.api_client,
                            cls.zone.id,
                            cls.services["ostype"]
                            )
        # Create account, service offerings etc
        cls.account = Account.create(
                            cls.api_client,
                            cls.services["account"],
                            domainid=cls.domain.id
                            )

        cls.services["account"] = cls.account.account.name
        cls.services["zoneid"] = cls.zone.id
        cls.service_offering = ServiceOffering.create(
                                            cls.api_client,
                                            cls.services["service_offering"]
                                            )
        cls.disk_offering = DiskOffering.create(
                                    cls.api_client,
                                    cls.services["disk_offering"]
                                    )
        cls._cleanup = [
                        cls.service_offering,
                        cls.disk_offering,
                        cls.account
                        ]

    def setUp(self):

        self.apiclient = self.testClient.getApiClient()
        self.dbclient = self.testClient.getDbConnection()
        self.cleanup = []

    def tearDown(self):
        try:
            #Clean up, terminate the created volumes
            self.debug("Cleanup the resources..")
            cleanup_resources(self.apiclient, self.cleanup)
            self.debug("Cleanup succeeded")
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    @classmethod
    def tearDownClass(cls):
        try:
            cleanup_resources(cls.api_client, cls._cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)

    @attr(speed = "slow")
    @attr(tags = ["advanced", "basic", "eip", "advancedns", "sg"])
    def test_01_upload_data_disk(self):
        """Test Upload a data disk
        """


        # Validate the following
        # 1. call upload volume API with following parameters HTTP URL of the
        #    data disk, Zone ID, Name, Description, Hyper visor
        # 2. Upload volume is successful

        self.debug("Uploading the volume to account: %s" %
                                                self.account.account.name)
        # Upload the volume
        volume = Volume.upload(
                                self.apiclient,
                                self.services["volume"],
                                zoneid=self.zone.id,
                                account=self.account.account.name,
                                domainid=self.account.account.domainid,
                                url=self.services["volume"]["url"]
                                )
        self.debug("Registered volume: %s for account: %s" % (
                                                volume.name,
                                                self.account.account.name
                                                ))
        self.debug("Waiting for upload of volume: %s" % volume.name)
        try:
            volume.wait_for_upload(self.apiclient)
            self.debug("Volume: %s uploaded to CS successfully" % volume.name)
        except Exception as e:
            self.fail("Upload volume failed: %s" % e)

        # Check List Volume response for newly created volume
        list_volume_response = Volume.list(
                                                self.apiclient,
                                                id=volume.id,
                                                zoneid=self.zone.id,
                                                listall=True
                                                )
        self.assertNotEqual(
                                list_volume_response,
                                None,
                                "Check if volume exists in ListVolumes"
                            )
        volume_response = list_volume_response[0]
        self.assertEqual(
                    volume_response.state,
                    "Uploaded",
                    "Volume state should be 'Uploaded' after importing to CS"
                    )
        return

    @attr(speed = "slow")
    @attr(tags = ["advanced", "basic", "eip", "advancedns", "sg"])
    def test_02_upload_volume_limit(self):
        """Test upload volume limits
        """


        # Validate the following
        # 1. Update the volume resource limit for account to 1
        # 2. Upload volume in that account
        # 3. Upload volume should fail with appropriate error

        self.debug(
            "Updating volume resource limit for account: %s" %
                                                self.account.account.name)
        # Set usage_vm=1 for Account 1
        update_resource_limit(
                              self.apiclient,
                              2,    # Volume
                              account=self.account.account.name,
                              domainid=self.account.account.domainid,
                              max=1
                              )

        self.debug("Uploading the volume to account: %s" %
                                                self.account.account.name)
        with self.assertRaises(Exception):
            # Upload the volume
            volume = Volume.upload(
                                self.apiclient,
                                self.services["volume"],
                                zoneid=self.zone.id,
                                account=self.account.account.name,
                                domainid=self.account.account.domainid,
                                url=self.services["volume"]["url"]
                                )
            self.debug("Registered volume: %s for account: %s" % (
                                                volume.name,
                                                self.account.account.name
                                                ))
        self.debug("Upload volume failed! Test succeeded..")
        return


class TestUploadDiskDiffFormat(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_client = super(
                               TestUploadDiskDiffFormat,
                               cls
                               ).getClsTestClient().getApiClient()
        cls.services = Services().services

        # Get Zone, Domain and templates
        cls.domain = get_domain(cls.api_client, cls.services)
        cls.zone = get_zone(cls.api_client, cls.services)
        template = get_template(
                            cls.api_client,
                            cls.zone.id,
                            cls.services["ostype"]
                            )
        # Create account, service offerings etc
        cls.account = Account.create(
                            cls.api_client,
                            cls.services["account"],
                            domainid=cls.domain.id
                            )
        cls.services["zoneid"] = cls.zone.id
        cls.service_offering = ServiceOffering.create(
                                            cls.api_client,
                                            cls.services["service_offering"]
                                            )
        cls.disk_offering = DiskOffering.create(
                                    cls.api_client,
                                    cls.services["disk_offering"]
                                    )
        cls._cleanup = [
                        cls.service_offering,
                        cls.disk_offering,
                        cls.account
                        ]

    def setUp(self):

        self.apiclient = self.testClient.getApiClient()
        self.dbclient = self.testClient.getDbConnection()
        self.cleanup = []

    def tearDown(self):
        try:
            #Clean up, terminate the created volumes
            self.debug("Cleanup the resources..")
            cleanup_resources(self.apiclient, self.cleanup)
            self.debug("Cleanup succeeded")
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    @classmethod
    def tearDownClass(cls):
        try:
            cleanup_resources(cls.api_client, cls._cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)

    @attr(tags = ["advanced", "basic", "eip", "advancedns", "sg"])
    def test_upload_disk_diff_format(self):
        """Test Upload a data disk in different format
        """


        # Validate the following
        # 1. call upload volume API with following parameters HTTP URL of the
        #    data disk, Zone ID, Name, Description, Hyper visor
        #    disk types are: zip file format,tar format,tar gzip format
        #    tar bzip format
        # 2. Upload volume is successful

        for hypervisor, settings in self.services["volumes"].items():
            for k, v in settings.items():
                self.debug(
                    "Uploading the volume (type: %s) for Hypervisor: %s to account: %s" % (
                                                v["format"],
                                                hypervisor,
                                                self.account.account.name
                                                ))
                # Upload the volume
                volume = Volume.upload(
                                self.apiclient,
                                v,
                                zoneid=self.zone.id,
                                account=self.account.account.name,
                                domainid=self.account.account.domainid,
                                )
                self.debug("Registered volume: %s for account: %s" % (
                                                volume.name,
                                                self.account.account.name
                                                ))
                self.debug("Waiting for upload of volume: %s" % volume.name)
                try:
                    volume.wait_for_upload(self.apiclient)
                    self.debug("Volume: %s uploaded to CS successfully" %
                                                                volume.name)
                except Exception as e:
                    self.fail("Upload volume failed: %s" % e)

                # Check List Volume response for newly created volume
                list_volume_response = list_volumes(
                                                self.apiclient,
                                                id=volume.id
                                                )
                self.assertNotEqual(
                                list_volume_response,
                                None,
                                "Check if volume exists in ListVolumes"
                            )
                volume_response = list_volume_response[0]
                self.assertEqual(
                    volume_response.state,
                    "Uploaded",
                    "Volume state should be 'Uploaded' after importing to CS"
                    )
        return


class TestUploadAttachDisk(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_client = super(
                               TestUploadAttachDisk,
                               cls
                               ).getClsTestClient().getApiClient()
        cls.services = Services().services

        # Get Zone, Domain and templates
        cls.domain = get_domain(cls.api_client, cls.services)
        cls.zone = get_zone(cls.api_client, cls.services)
        template = get_template(
                            cls.api_client,
                            cls.zone.id,
                            cls.services["ostype"]
                            )
        # Create account, service offerings etc
        cls.account = Account.create(
                            cls.api_client,
                            cls.services["account"],
                            domainid=cls.domain.id
                            )

        cls.services["account"] = cls.account.account.name
        cls.services["virtual_machine"]["zoneid"] = cls.zone.id
        cls.services["zoneid"] = cls.zone.id
        cls.service_offering = ServiceOffering.create(
                                            cls.api_client,
                                            cls.services["service_offering"]
                                            )
        cls.disk_offering = DiskOffering.create(
                                    cls.api_client,
                                    cls.services["disk_offering"]
                                    )
        cls.virtual_machine = VirtualMachine.create(
                                    cls.api_client,
                                    cls.services["virtual_machine"],
                                    templateid=template.id,
                                    accountid=cls.account.account.name,
                                    domainid=cls.account.account.domainid,
                                    serviceofferingid=cls.service_offering.id,
                                )
        cls._cleanup = [
                        cls.service_offering,
                        cls.disk_offering,
                        cls.account
                        ]

    def setUp(self):

        self.apiclient = self.testClient.getApiClient()
        self.dbclient = self.testClient.getDbConnection()
        self.cleanup = []

    def tearDown(self):
        try:
            #Clean up, terminate the created volumes
            self.debug("Cleanup the resources..")
            cleanup_resources(self.apiclient, self.cleanup)
            self.debug("Cleanup succeeded")
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    @classmethod
    def tearDownClass(cls):
        try:
            cleanup_resources(cls.api_client, cls._cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)

    @attr(tags = ["advanced", "basic", "eip", "advancedns", "sg"])
    def test_upload_attach_data_disk(self):
        """Test Upload and attach a data disk
        """


        # Validate the following
        # 1. call upload volume API with following parameters HTTP URL of the
        #    data disk, Zone ID, Name, Description, Hyper visor
        # 2. Upload volume is successful

        self.debug("Uploading the volume to account: %s" %
                                                self.account.account.name)
        # Upload the volume
        volume = Volume.upload(
                                self.apiclient,
                                self.services["volume"],
                                zoneid=self.zone.id,
                                account=self.account.account.name,
                                domainid=self.account.account.domainid,
                                url=self.services["volume"]["url"]
                                )
        self.debug("Registered volume: %s for account: %s" % (
                                                volume.name,
                                                self.account.account.name
                                                ))
        self.debug("Waiting for upload of volume: %s" % volume.name)
        try:
            volume.wait_for_upload(self.apiclient)
            self.debug("Volume: %s uploaded to CS successfully" % volume.name)
        except Exception as e:
            self.fail("Upload volume failed: %s" % e)

        # Check List Volume response for newly created volume
        list_volume_response = Volume.list(
                                                self.apiclient,
                                                id=volume.id,
                                                zoneid=self.zone.id,
                                                listall=True
                                                )
        self.assertNotEqual(
                                list_volume_response,
                                None,
                                "Check if volume exists in ListVolumes"
                            )
        volume_response = list_volume_response[0]
        self.assertEqual(
                    volume_response.state,
                    "Uploaded",
                    "Volume state should be 'Uploaded' after importing to CS"
                    )
        self.debug(
            "Attaching the disk: %s to VM: %s" % (
                                                  self.virtual_machine.name,
                                                  volume.name
                                                  ))
        self.virtual_machine.attach_volume(self.apiclient, volume)
        self.debug(
                "Volume attached to instance: %s" %
                                            self.virtual_machine.name)
        # Check List Volume response for newly created volume
        list_volume_response = Volume.list(
                                        self.apiclient,
                                        id=volume.id,
                                        virtualmachineid=self.virtual_machine.id,
                                        listall=True
                                    )
        self.assertNotEqual(
                            list_volume_response,
                            None,
                            "Check if volume exists in ListVolumes"
                            )

        volume_response = list_volume_response[0]
        self.assertEqual(
                    volume_response.state,
                    "Ready",
                    "Volume state should be 'Uploaded' after importing to CS"
                    )
        return


class TestUploadAttachDiskDiffFormat(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_client = super(
                               TestUploadAttachDiskDiffFormat,
                               cls
                               ).getClsTestClient().getApiClient()
        cls.services = Services().services

        # Get Zone, Domain and templates
        cls.domain = get_domain(cls.api_client, cls.services)
        cls.zone = get_zone(cls.api_client, cls.services)
        template = get_template(
                            cls.api_client,
                            cls.zone.id,
                            cls.services["ostype"]
                            )
        # Create account, service offerings etc
        cls.account = Account.create(
                            cls.api_client,
                            cls.services["account"],
                            domainid=cls.domain.id
                            )
        cls.services["virtual_machine"]["zoneid"] = cls.zone.id
        cls.services["zoneid"] = cls.zone.id
        cls.service_offering = ServiceOffering.create(
                                            cls.api_client,
                                            cls.services["service_offering"]
                                            )
        cls.disk_offering = DiskOffering.create(
                                    cls.api_client,
                                    cls.services["disk_offering"]
                                    )
        cls.virtual_machine = VirtualMachine.create(
                                    cls.api_client,
                                    cls.services["virtual_machine"],
                                    templateid=template.id,
                                    accountid=cls.account.account.name,
                                    domainid=cls.account.account.domainid,
                                    serviceofferingid=cls.service_offering.id,
                                )
        cls._cleanup = [
                        cls.service_offering,
                        cls.disk_offering,
                        cls.account
                        ]

    def setUp(self):

        self.apiclient = self.testClient.getApiClient()
        self.dbclient = self.testClient.getDbConnection()
        self.cleanup = []

    def tearDown(self):
        try:
            #Clean up, terminate the created volumes
            self.debug("Cleanup the resources..")
            cleanup_resources(self.apiclient, self.cleanup)
            self.debug("Cleanup succeeded")
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    @classmethod
    def tearDownClass(cls):
        try:
            cleanup_resources(cls.api_client, cls._cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)

    @attr(tags = ["advanced", "basic", "eip", "advancedns", "sg"])
    def test_upload_disk_diff_format(self):
        """Test Upload a data disk in different format
        """


        # Validate the following
        # 1. call upload volume API with following parameters HTTP URL of the
        #    data disk, Zone ID, Name, Description, Hyper visor
        #    disk types are: zip file format,tar format,tar gzip format
        #    tar bzip format
        # 2. Upload volume is successful

        for hypervisor, settings in self.services["volumes"].items():
            for k, v in settings.items():
                self.debug(
                    "Uploading the volume (type: %s) for Hypervisor: %s to account: %s" % (
                                                v["format"],
                                                hypervisor,
                                                self.account.account.name
                                                ))
                # Upload the volume
                volume = Volume.upload(
                                self.apiclient,
                                v,
                                zoneid=self.zone.id,
                                account=self.account.account.name,
                                domainid=self.account.account.domainid,
                                )
                self.debug("Registered volume: %s for account: %s" % (
                                                volume.name,
                                                self.account.account.name
                                                ))
                self.debug("Waiting for upload of volume: %s" % volume.name)
                try:
                    volume.wait_for_upload(self.apiclient)
                    self.debug("Volume: %s uploaded to CS successfully" %
                                                                volume.name)
                except Exception as e:
                    self.fail("Upload volume failed: %s" % e)

                # Check List Volume response for newly created volume
                list_volume_response = list_volumes(
                                                self.apiclient,
                                                id=volume.id
                                                )
                self.assertNotEqual(
                                list_volume_response,
                                None,
                                "Check if volume exists in ListVolumes"
                            )
                volume_response = list_volume_response[0]
                self.assertEqual(
                    volume_response.state,
                    "Uploaded",
                    "Volume state should be 'Uploaded' after importing to CS"
                    )

                self.debug(
                    "Attaching the disk: %s to VM: %s" % (
                                                  self.virtual_machine.name,
                                                  volume.name
                                                  ))
                self.virtual_machine.attach_volume(self.apiclient, volume)
                self.debug(
                           "Volume attached to instance: %s" %
                                            self.virtual_machine.name)
                # Check List Volume response for newly created volume
                list_volume_response = Volume.list(
                                        self.apiclient,
                                        id=volume.id,
                                        virtualmachineid=self.virtual_machine.id,
                                        listall=True
                                    )
                self.assertNotEqual(
                            list_volume_response,
                            None,
                            "Check if volume exists in ListVolumes"
                            )

                volume_response = list_volume_response[0]
                self.assertEqual(
                        volume_response.state,
                        "Ready",
                        "Volume state should be 'Uploaded' after importing to CS"
                    )
        return


class TestUploadDiskMultiStorage(cloudstackTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_client = super(
                               TestUploadDiskMultiStorage,
                               cls
                               ).getClsTestClient().getApiClient()
        cls.services = Services().services

        # Get Zone, Domain and templates
        cls.domain = get_domain(cls.api_client, cls.services)
        cls.zone = get_zone(cls.api_client, cls.services)
        cls.pod = get_pod(cls.api_client, zoneid=cls.zone.id)

        template = get_template(
                            cls.api_client,
                            cls.zone.id,
                            cls.services["ostype"]
                            )
        # Create account, service offerings etc
        cls.account = Account.create(
                            cls.api_client,
                            cls.services["account"],
                            domainid=cls.domain.id
                            )

        cls.services["account"] = cls.account.account.name
        cls.services["zoneid"] = cls.zone.id
        cls.service_offering = ServiceOffering.create(
                                            cls.api_client,
                                            cls.services["service_offering"]
                                            )
        cls.disk_offering = DiskOffering.create(
                                    cls.api_client,
                                    cls.services["disk_offering"]
                                    )
        cls._cleanup = [
                        cls.service_offering,
                        cls.disk_offering,
                        cls.account
                        ]

    def setUp(self):

        self.apiclient = self.testClient.getApiClient()
        self.dbclient = self.testClient.getDbConnection()
        self.cleanup = []

    def tearDown(self):
        try:
            #Clean up, terminate the created volumes
            self.debug("Cleanup the resources..")
            cleanup_resources(self.apiclient, self.cleanup)
            self.debug("Cleanup succeeded")
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)
        return

    @classmethod
    def tearDownClass(cls):
        try:
            cleanup_resources(cls.api_client, cls._cleanup)
        except Exception as e:
            raise Exception("Warning: Exception during cleanup : %s" % e)

    @attr(tags = ["advanced", "basic", "eip", "advancedns", "sg", "multistorage"])
    def test_01_upload_volume_multi_sec_storage(self):
        """Test Upload a data disk when multiple sec storages are present
        """


        # Validate the following
        # 1. Assume multiple secondary storages are present in a zone
        # 2. call upload volume API with following parameters HTTP URL of the
        #    data disk, Zone ID, Name, Description, Hyper visor
        # 2. Upload volume is successful

        sec_storages = Host.list(
                                 self.apiclient,
                                 type='SecondaryStorage',
                                 zoneid=self.zone.id
                                 )
        self.assertEqual(
                         isinstance(sec_storages, list),
                         True,
                         "List Secondary storage should return a valid list"
                         )
        self.assertGreaterEqual(
                    len(sec_storages),
                    2,
                    "Test requires atleast 2 secondary storages added to zone"
                    )
        self.debug("Uploading the volume to account: %s" %
                                                self.account.account.name)
        # Upload the volume
        volume = Volume.upload(
                                self.apiclient,
                                self.services["volume"],
                                zoneid=self.zone.id,
                                account=self.account.account.name,
                                domainid=self.account.account.domainid,
                                url=self.services["volume"]["url"]
                                )
        self.debug("Registered volume: %s for account: %s" % (
                                                volume.name,
                                                self.account.account.name
                                                ))
        self.debug("Waiting for upload of volume: %s" % volume.name)
        try:
            volume.wait_for_upload(self.apiclient)
            self.debug("Volume: %s uploaded to CS successfully" % volume.name)
        except Exception as e:
            self.fail("Upload volume failed: %s" % e)

        # Check List Volume response for newly created volume
        list_volume_response = Volume.list(
                                                self.apiclient,
                                                id=volume.id,
                                                zoneid=self.zone.id,
                                                listall=True
                                                )
        self.assertNotEqual(
                                list_volume_response,
                                None,
                                "Check if volume exists in ListVolumes"
                            )
        volume_response = list_volume_response[0]
        self.assertEqual(
                    volume_response.state,
                    "Uploaded",
                    "Volume state should be 'Uploaded' after importing to CS"
                    )
        return

    @attr(tags = ["advanced", "basic", "eip", "advancedns", "sg", "multistorage"])
    def test_02_upload_volume_multi_pri_storage(self):
        """Test Upload a data disk when multiple primary storages are present
        """


        # Validate the following
        # 1. Assume multiple primary storages are present in a pod
        # 2. call upload volume API with following parameters HTTP URL of the
        #    data disk, Zone ID, Name, Description, Hyper visor
        # 2. Upload volume is successful

        storage_pools = StoragePool.list(
                                 self.apiclient,
                                 zoneid=self.zone.id,
                                 podid=self.pod.id
                                 )
        self.assertEqual(
                         isinstance(storage_pools, list),
                         True,
                         "List Primary storage should return a valid list"
                         )
        self.assertGreaterEqual(
                    len(storage_pools),
                    2,
                    "Test requires atleast 2 primary storages added to pod"
                    )
        self.debug("Uploading the volume to account: %s" %
                                                self.account.account.name)
        # Upload the volume
        volume = Volume.upload(
                                self.apiclient,
                                self.services["volume"],
                                zoneid=self.zone.id,
                                account=self.account.account.name,
                                domainid=self.account.account.domainid,
                                url=self.services["volume"]["url"]
                                )
        self.debug("Registered volume: %s for account: %s" % (
                                                volume.name,
                                                self.account.account.name
                                                ))
        self.debug("Waiting for upload of volume: %s" % volume.name)
        try:
            volume.wait_for_upload(self.apiclient)
            self.debug("Volume: %s uploaded to CS successfully" % volume.name)
        except Exception as e:
            self.fail("Upload volume failed: %s" % e)

        # Check List Volume response for newly created volume
        list_volume_response = Volume.list(
                                                self.apiclient,
                                                id=volume.id,
                                                zoneid=self.zone.id,
                                                listall=True
                                                )
        self.assertNotEqual(
                                list_volume_response,
                                None,
                                "Check if volume exists in ListVolumes"
                            )
        volume_response = list_volume_response[0]
        self.assertEqual(
                    volume_response.state,
                    "Uploaded",
                    "Volume state should be 'Uploaded' after importing to CS"
                    )
        return
