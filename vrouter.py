from example_session import session, printresp
from google.protobuf.json_format import MessageToJson
import pytest

@pytest.fixture(autouse=True)
def prepare_session_for_example(request):
    session.initialize(request)
    yield
    session.terminate()

def test_vrouter_features():
    session_id = session.session_id
    device_id = session.device_id
    grpc_channel = session.grpc_channel

    # example_imports.begin
    from volta.v4 import api_device_pb2_grpc
    from volta.v4 import api_device_vrouter_pb2
    from volta.v4 import api_device_vrouter_interface_pb2
    # example_imports.end

    # create_vrouter.begin
    vrouter_api = api_device_pb2_grpc.ApiDeviceVRouterStub(grpc_channel)
    msg = api_device_vrouter_pb2.DeviceVRouterCreateReq()
    msg.hdr.session_id = session_id
    msg.name = "R1"
    msg.device_id = device_id
    response = vrouter_api.Create(msg)
    vrouter_id = response.vrouter.id
    # create_vrouter.end
    assert not response.hdr.error 

    # create_lif.begin
    # Create an interface 
    msg = api_device_vrouter_interface_pb2.DeviceVRouterInterfaceCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.interface_params.name = "LIF_1"
    msg.interface_params.vlan_interface.port_id = 1
    msg.interface_params.vlan_interface.vlan_id = 10
    response = vrouter_api.InterfaceCreate(msg)
    interface_id = response.interface_id
    # create_lif.end
    assert not response.hdr.error 

    # create_vrf.begin
    # Create a VRF
    msg = api_device_vrouter_pb2.DeviceVRouterVrfCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.vrf_id = 3
    msg.name = "VRF_3"
    response = vrouter_api.VrfCreate(msg)
    # create_vrf.end
    assert not response.hdr.error 

    # set_vrf.begin
    # Attach the interface to the default VRF
    msg = api_device_vrouter_pb2.DeviceVRouterVrfInterfaceAttachReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.interface_id = interface_id
    msg.vrf_id = 0
    msg.addresses.append("10.14.0.10/24")
    msg.addresses.append("fd01:14::10/64")
    response = vrouter_api.VrfInterfaceAttach(msg)
    # set_vrf.end
    assert not response.hdr.error

    # add_ip.begin
    msg = api_device_vrouter_pb2.DeviceVRouterInterfaceAddressAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.interface_id = interface_id
    msg.address = "10.14.0.11/24"
    response = vrouter_api.InterfaceAddressAdd(msg)
    # add_ip.end
    assert not response.hdr.error 

    # get_interface.begin
    # Display interface configuration
    msg = api_device_vrouter_interface_pb2.DeviceVRouterInterfaceGetReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.interface_id = interface_id
    response = vrouter_api.InterfaceGet(msg)
    print(response)
    # get_interface.end
    assert not response.hdr.error

    # list_vrs.begin
    # Display vRouter summary
    msg = api_device_vrouter_pb2.DeviceVRouterListReq()
    msg.hdr.session_id = session_id
    response = vrouter_api.List(msg)
    print(response)
    # list_vrs.end
    assert not response.hdr.error
