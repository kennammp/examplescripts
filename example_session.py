#!/usr/bin/env python3
import sys

from google.protobuf.json_format import MessageToJson

# Session utils
# RPCs and protobuf files
from volta.v4 import (
    api_device_pb2_grpc,
    api_device_vrouter_interface_pb2,
    api_device_vrouter_pb2,
    api_routing_pb2_grpc,
    api_service_pb2_grpc,
    api_vcluster_common_pb2,
    resources_device_vrouter_pb2,
)
from volta.v4.routing import api_static_pb2

# Utils included in python protobuf bindings to setup RBAC and TLS
from volta.v4.utils.client_channel_creator import create_channel


class ExampleSession:
    """
    Session object to use in example use cases for the public documentation.
    Contains a small client to prepare the scenarios and can be used to store any data
    needed during an example.
    Should be a singleton.
    initialize must be called before any other called. terminate must be called at the end.
    """

    def __init__(self):
        self.is_set_up = False
        # Values utilized in the create_channel() method
        # these include grpc client RBAC and TLS setup
        self.grpc_endpoint = "127.0.0.1:7878"
        self.tls = False
        self.tls_mutual = False
        self.device_id = 1
        # For lab testing purposes you can override the CN integrity check
        self.ssl_name_server_override = "volta-node"

        self.vrouter_ids = None  # Stores vrouter ids set in create_vrouters

        # These attributes are set by initialize and can be used in the examples as a shortcut
        self.grpc_channel = None
        self.session_id = None
        self.session_api = None
        self.vrouter_api = None
        self.static_api = None

    def initialize(self, request=None):
        """
        Initialize session. Request is optional and should come from pytest.
        """
        if request:
            grpc_endpoint = request.config.getoption("--endpoint")
            if grpc_endpoint:
                self.grpc_endpoint = grpc_endpoint
            tls = request.config.getoption("--tls")
            if tls:
                self.tls = tls
            tls_mutual = request.config.getoption("--tls-mutual")
            if tls_mutual:
                self.tls_mutual = tls_mutual
            device = request.config.getoption("--device")
            if device:
                self.device_id = device
            ssl_override = request.config.getoption("--ssl-name-server-override")
            if ssl_override:
                self.ssl_name_server_override = ssl_override

        # RBAC credentials
        USERNAME = "admin"
        PASSWORD = "volta"
        DOMAIN = "root"
        try:
            # - Setup gRPC channel
            # - Setup client gRPC API stubs
            # - Open session
            # Create the object that your client stub will invoke to bring up the connection
            grpc_channel = create_channel(
                self.grpc_endpoint,
                USERNAME,
                PASSWORD,
                DOMAIN,
                tls=self.tls,
                tls_mutual_auth=self.tls_mutual,
                grpc_ssl_target_name_override=self.ssl_name_server_override,
            )
            self.grpc_channel = grpc_channel

            # Create the client stub that will be used to bring up the session:
            self.session_api = api_service_pb2_grpc.ApiSessionStub(grpc_channel)
            msg = api_vcluster_common_pb2.SessionRequest()
            msg.init.parameters.timeout = 600
            # make the call to start the session and create the session ID:
            response = self.session_api.Request(msg)
            self.session_id = response.session_id

            # Create the client stub that will be used to send the function call:
            self.vrouter_api = api_device_pb2_grpc.ApiDeviceVRouterStub(grpc_channel)
            self.static_api = api_routing_pb2_grpc.ApiStaticProtocolInstanceStub(
                grpc_channel
            )
            self._destroy_all_vrouters()
        except Exception:
            raise
        else:
            self.is_set_up = True

    def terminate(self):
        self._destroy_all_vrouters()
        msg = api_vcluster_common_pb2.SessionRequest()
        msg.close.session_id = self.session_id
        _ = self.session_api.Request(msg)
        self.is_set_up = False

    def create_vrouters(self, num, device_id=1):
        """
        Create num vrouters in the specified device.
        Store and return a list of created vrouter_ids.
        Should be called only once.
        """
        if self.vrouter_ids:
            raise RuntimeError("create_vrouters can be called only once")
        else:
            self.vrouter_ids = []
        for i in range(1, num + 1):
            msg = api_device_vrouter_pb2.DeviceVRouterCreateReq()
            msg.hdr.session_id = self.session_id
            msg.name = f"vRouter {i}"
            msg.device_id = device_id
            msg.vrouter_type = 1
            response = self.vrouter_api.Create(msg)
            assert not response.hdr.error
            self.vrouter_ids.append(response.vrouter.id)
        return self.vrouter_ids

    def create_interfaces(self, num, vrouter_id, vlan_id=0):
        """
        Create num interfaces in the specified vrouter and vlan.
        Should be called only once.
        """
        interface_ids = []
        for i in range(1, num + 1):
            msg = api_device_vrouter_interface_pb2.DeviceVRouterInterfaceCreateReq()
            msg.hdr.session_id = self.session_id
            msg.hdr.vrouter_id = vrouter_id
            msg.interface_params.name = f"LIF{i}"
            msg.interface_params.vlan_interface.port_id = i
            msg.interface_params.vlan_interface.vlan_id = vlan_id
            response = self.vrouter_api.InterfaceCreate(msg)
            assert not response.hdr.error
            interface_ids.append(response.interface_id)
        return interface_ids

    def create_vrfs(self, num, vrouter_id):
        """
        Create num VRFs in the specified vrouter.
        Should be called only once.
        """
        for i in range(1, num + 1):
            msg = api_device_vrouter_pb2.DeviceVRouterVrfCreateReq()
            msg.hdr.session_id = self.session_id
            msg.hdr.vrouter_id = vrouter_id
            msg.vrf_id = i
            msg.name = f"vrf{i}"
            response = self.vrouter_api.VrfCreate(msg)
            assert not response.hdr.error

    def create_interface_ips(self, vrouter_id, interface_id, addresses, vrf_id=0):
        """
        Set addresses in the specified interface and attach to VRF.
        """
        msg = api_device_vrouter_pb2.DeviceVRouterVrfInterfaceAttachReq()
        msg.hdr.session_id = self.session_id
        msg.hdr.vrouter_id = vrouter_id
        msg.interface_id = interface_id
        msg.vrf_id = vrf_id
        for address in addresses:
            msg.addresses.append(address)
        response = self.vrouter_api.VrfInterfaceAttach(msg)
        assert not response.hdr.error
        return response

    def get_interface(self, interface_id):
        msg = api_device_vrouter_interface_pb2.DeviceVRouterInterfaceGetReq()
        msg.hdr.session_id = self.session_id
        msg.hdr.vrouter_id = self.vrouter_ids[0]
        msg.interface_id = interface_id
        response = self.vrouter_api.InterfaceGet(msg)
        assert not response.hdr.error
        return response

    def _destroy_vrouters(self):
        """
        Destroy all stored vrouters
        """
        for vr_id in self.vrouter_ids:
            msg = api_device_vrouter_pb2.DeviceVRouterDestroyReq()
            msg.hdr.session_id = self.session_id
            msg.hdr.vrouter_id = vr_id
            _ = self.vrouter_api.Destroy(msg)

    def _destroy_all_vrouters(self):
        msg = api_device_vrouter_pb2.DeviceVRouterListReq()
        msg.hdr.session_id = self.session_id
        response = self.vrouter_api.List(msg)
        for vrouter in response.vrouter:
            msg = api_device_vrouter_pb2.DeviceVRouterDestroyReq()
            msg.hdr.session_id = self.session_id
            msg.hdr.vrouter_id = vrouter.id
            _ = self.vrouter_api.Destroy(msg)

    def list_routes(self, vrouter_id, vrf_id=0):
        msg = api_static_pb2.StaticProtocolInstanceRouteListReq()
        msg.hdr.session_id = self.session_id
        msg.hdr.vrouter_id = vrouter_id
        msg.hdr.vrf_id = vrf_id
        response = self.static_api.RouteList(msg)
        for route in response.static_route:
            print(route)
        assert not response.hdr.error


session = ExampleSession()


def printresp(response):
    print(MessageToJson(response, preserving_proto_field_name=True), file=sys.stdout)
