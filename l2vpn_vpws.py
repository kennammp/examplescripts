from example_session import session, printresp
import pytest

@pytest.fixture(autouse=True)
def prepare_session_for_example(request):
    session.initialize(request)
    session.create_vrouters(1)
    yield
    session.terminate()


def test_l2vpn_vpws_features():
    session_id = session.session_id
    grpc_channel = session.grpc_channel
    vrouter_id = session.vrouter_ids[0]

    # import.begin
    from volta.v4 import api_device_pb2_grpc
    from volta.v4 import api_device_vrouter_interface_pb2
    from volta.v4 import api_device_vrouter_l2vpn_pb2
    from volta.v4 import resources_device_l2vpn_pb2
    # import.end

    # stub.begin
    vrouter_api = api_device_pb2_grpc.ApiDeviceVRouterStub(grpc_channel)
    l2vpn_api = api_device_pb2_grpc.ApiDeviceVRouterL2vpnStub(grpc_channel)
    # stub.end
    
    # vrouter_create_lif.begin
    msg = api_device_vrouter_interface_pb2.DeviceVRouterInterfaceCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.interface_params.name = "lif-2-1000"
    msg.interface_params.vlan_interface.port_id = 2
    msg.interface_params.vlan_interface.vlan_id = 1000
    response = vrouter_api.InterfaceCreate(msg)
    interface_id = response.interface_id
    # vrouter_create_lif.end
    assert not response.hdr.error

    # This assumes that MPLS is enabled in VRouter with LDP
    # l2vpn_create.begin
    msg = api_device_vrouter_l2vpn_pb2.DeviceVRouterL2vpnCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.l2vpn.type = resources_device_l2vpn_pb2.L2VPN_TYPE_VPWS
    msg.l2vpn.name = "vpws-l2vpn"
    response = vrouter_api.L2vpnCreate(msg)
    l2vpn_id = response.l2vpn.id
    # l2vpn_create.end
    assert not response.hdr.error

    # cross_connect.begin
    msg = api_device_vrouter_l2vpn_pb2.DeviceVRouterL2vpnInterfaceCrossConnectSetReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.l2vpn_id = l2vpn_id
    msg.interface_id = interface_id
    response = l2vpn_api.InterfaceCrossConnectSet(msg)
    # cross_connect.end

    # Create pseudowire for L2VPN
    # add_pw.begin
    msg = api_device_vrouter_l2vpn_pb2.DeviceVRouterL2vpnPseudoWireCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.l2vpn_id = l2vpn_id
    msg.lif_pseudowire.name = "vpws-pw"
    msg.lif_pseudowire.pw_interface.pw_id = 8
    msg.lif_pseudowire.pw_interface.control_word = False
    msg.lif_pseudowire.pw_interface.pw_type = resources_device_l2vpn_pb2.PWTYPE_ETHERNET_TAGGED
    msg.lif_pseudowire.pw_interface.remote_id = "10.6.20.2"
    msg.lif_pseudowire.pw_interface.service_vlan = 2500
    response = l2vpn_api.PseudoWireCreate(msg)
    # add_pw.end
    assert not response.hdr.error

    # get_crossconnect.begin
    msg = api_device_vrouter_l2vpn_pb2.DeviceVRouterL2vpnInterfaceCrossConnectGetReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.l2vpn_id = l2vpn_id
    response = l2vpn_api.InterfaceCrossConnectGet(msg)
    print(response)
    # get_crossconnect.end

    # get_pw.begin
    msg = api_device_vrouter_l2vpn_pb2.DeviceVRouterL2vpnPseudoWireListReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.l2vpn_id = l2vpn_id
    response = l2vpn_api.PseudoWireList(msg)
    print(response)
    # get_pw.end

    # l2vpn_destroy.begin
    msg = api_device_vrouter_l2vpn_pb2.DeviceVRouterL2vpnDestroyReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.l2vpn_id = l2vpn_id
    response = vrouter_api.L2vpnDestroy(msg)
    # l2vpn_destroy.end


