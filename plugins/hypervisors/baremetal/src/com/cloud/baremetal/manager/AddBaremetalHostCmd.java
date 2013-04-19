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
//
// Automatically generated by addcopyright.py at 01/29/2013
package com.cloud.baremetal.manager;

import org.apache.cloudstack.api.APICommand;
import org.apache.cloudstack.api.ApiConstants;
import org.apache.cloudstack.api.Parameter;
import org.apache.cloudstack.api.command.admin.host.AddHostCmd;
import org.apache.cloudstack.api.response.HostResponse;
@APICommand(name="addBaremetalHost", description="add a baremetal host", responseObject = HostResponse.class)
public class AddBaremetalHostCmd extends AddHostCmd {

    @Parameter(name=ApiConstants.IP_ADDRESS, type=CommandType.STRING, description="ip address intentionally allocated to this host after provisioning")
    private String vmIpAddress;

    public AddBaremetalHostCmd() {
    }

    @Override
    public void execute(){
        this.getFullUrlParams().put(ApiConstants.BAREMETAL_DISCOVER_NAME, BareMetalDiscoverer.class.getName());
        super.execute();
    }

    public String getVmIpAddress() {
        return vmIpAddress;
    }

    public void setVmIpAddress(String vmIpAddress) {
        this.vmIpAddress = vmIpAddress;
    }
}
