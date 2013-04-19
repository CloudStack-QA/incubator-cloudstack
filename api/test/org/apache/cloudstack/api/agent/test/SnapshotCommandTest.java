// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.
package org.apache.cloudstack.api.agent.test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;

import org.junit.Before;
import org.junit.Test;

import com.cloud.agent.api.SnapshotCommand;
import com.cloud.storage.Storage.StoragePoolType;
import com.cloud.storage.StoragePool;
import com.cloud.storage.StoragePoolStatus;

public class SnapshotCommandTest {

    public StoragePool pool = new StoragePool() {
        public long getId() {
            return 1L;
        };

        public String getName() {
            return "name";
        };

        public String getUuid() {
            return "bed9f83e-cac3-11e1-ac8a-0050568b007e";
        };

        public StoragePoolType getPoolType() {
            return StoragePoolType.Filesystem;
        };

        public Date getCreated() {
            Date date = null;
            try {
                date = new SimpleDateFormat("MM/dd/yyyy HH:mm:ss")
                        .parse("01/01/1970 12:12:12");
            } catch (ParseException e) {
                e.printStackTrace();
            }
            return date;
        }

        public Date getUpdateTime() {
            return new Date();
        };

        public long getDataCenterId() {
            return 0L;
        };

        public long getCapacityBytes() {
            return 0L;
        };

        public long getAvailableBytes() {
            return 0L;
        };

        public Long getClusterId() {
            return 0L;
        };

        public String getHostAddress() {
            return "hostAddress";
        };

        public String getPath() {
            return "path";
        };

        public String getUserInfo() {
            return "userInfo";
        };

        public boolean isShared() {
            return false;
        };

        public boolean isLocal() {
            return false;
        };

        public StoragePoolStatus getStatus() {
            return StoragePoolStatus.Up;
        };

        public int getPort() {
            return 25;
        };

        public Long getPodId() {
            return 0L;
        }

		@Override
		public String getStorageProviderName() {
			// TODO Auto-generated method stub
			return null;
		}

        @Override
        public boolean isInMaintenance() {
            // TODO Auto-generated method stub
            return false;
        };
    };

    SnapshotCommand ssc = new SnapshotCommand(pool,
            "http://secondary.Storage.Url",
            "420fa39c-4ef1-a83c-fd93-46dc1ff515ae", "snapshotName", 101L, 102L,
            103L);

    SnapshotCommand ssc1;


    @Before
    public void setUp() {
        ssc1 = new SnapshotCommand(pool,
                "secondaryStorageUrl", "snapshotUuid", "snapshotName", 101L,
                102L, 103L);
    }

    @Test
    public void testGetPrimaryStoragePoolNameLabel() {
        String label = ssc.getPrimaryStoragePoolNameLabel();
        assertTrue(label.equals("bed9f83e-cac3-11e1-ac8a-0050568b007e"));
    }

    @Test
    public void testGetSecondaryStorageUrl() {
        String url = ssc.getSecondaryStorageUrl();
        assertTrue(url.equals("http://secondary.Storage.Url"));
    }

    @Test
    public void testGetSnapshotUuid() {
        String uuid = ssc.getSnapshotUuid();
        assertTrue(uuid.equals("420fa39c-4ef1-a83c-fd93-46dc1ff515ae"));
    }

    @Test
    public void testGetSnapshotName() {
        String name = ssc.getSnapshotName();
        assertTrue(name.equals("snapshotName"));
    }

    @Test
    public void testGetVolumePath() {
        ssc.setVolumePath("vPath");
        String path = ssc.getVolumePath();
        assertTrue(path.equals("vPath"));

        ssc1.setVolumePath("vPath1");
        path = ssc1.getVolumePath();
        assertTrue(path.equals("vPath1"));
    }

    @Test
    public void testExecuteInSequence() {
        boolean b = ssc.executeInSequence();
        assertFalse(b);

        b = ssc1.executeInSequence();
        assertFalse(b);
    }

    @Test
    public void testGetDataCenterId() {
        Long dcId = ssc.getDataCenterId();
        Long expected = 101L;
        assertEquals(expected, dcId);
    }

    @Test
    public void testGetAccountId() {
        Long aId = ssc.getAccountId();
        Long expected = 102L;
        assertEquals(expected, aId);
    }

    @Test
    public void testGetVolumeId() {
        Long vId = ssc.getVolumeId();
        Long expected = 103L;
        assertEquals(expected, vId);
    }
}
