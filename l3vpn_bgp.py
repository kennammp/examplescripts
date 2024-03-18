from example_session import session
import pytest


@pytest.fixture(autouse=True)
def prepare_session_for_example(request):
    session.initialize(request)
    session.create_vrouters(1)
    interfaces = session.create_interfaces(2, session.vrouter_ids[0])
    session.create_interface_ips(session.vrouter_ids[0], interfaces[0], ["192.168.10.1"])
    yield
    session.terminate()


def test_l3vpn_features():
    session_id = session.session_id
    grpc_channel = session.grpc_channel
    vrouter_id = session.vrouter_ids[0]

    # import.begin
    from volta.v4 import api_routing_pb2_grpc
    from volta.v4 import api_device_pb2_grpc
    from volta.v4 import api_device_vrouter_pb2
    from volta.v4 import api_device_vrouter_l3vpn_pb2
    from volta.v4 import api_device_vrouter_interface_pb2
    from volta.v4.routing import api_bgp_pb2
    from volta.v4.routing import resources_bgp_pb2
    # import.end

    # stub.begin
    vrouter_api = api_device_pb2_grpc.ApiDeviceVRouterStub(grpc_channel)
    bgp_api = api_routing_pb2_grpc.ApiBgpProtocolInstanceStub(grpc_channel)
    # stub.end

    # bgp_pe_pe.begin
    msg = api_bgp_pb2.BgpProtocolInstanceCreateReq()
    msg.hdr.vrouter_id = vrouter_id
    msg.hdr.session_id = session_id
    msg.settings.autonomous_system = 65001
    msg.settings.vrf_id = 0
    msg.bgp_instance.router_id.ip = "192.168.10.1"
    response = bgp_api.Create(msg)

    msg = api_bgp_pb2.BgpProtocolInstanceIPv4AfiCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    response = bgp_api.IPv4AfiCreate(msg)
    # bgp_pe_pe.end
    assert not response.hdr.error

    # Create VRF for L3VPN and attach a LIF
    # vrf_l3vpn.begin
    msg = api_device_vrouter_pb2.DeviceVRouterVrfCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.name = 'l3vpn-vrf'
    response_vrf = vrouter_api.VrfCreate(msg)
    vrf_l3vpn_id = response_vrf.vrf.id

    msg = api_device_vrouter_interface_pb2.DeviceVRouterInterfaceCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.interface_params.name = "LIF_PE_CE"
    msg.interface_params.vlan_interface.port_id = 2
    msg.interface_params.vlan_interface.vlan_id = 2000
    response_iface = vrouter_api.InterfaceCreate(msg)
    interface_id = response_iface.interface_id

    msg = api_device_vrouter_pb2.DeviceVRouterVrfInterfaceAttachReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.vrf_id = vrf_l3vpn_id
    msg.interface_id = interface_id
    msg.addresses.append("10.1.1.1")
    response = vrouter_api.VrfInterfaceAttach(msg)
    # vrf_l3vpn_lif.end
    assert not response_vrf.hdr.error
    assert not response_iface.hdr.error
    assert not response.hdr.error

    # l3vpn_create.begin
    msg = api_device_vrouter_l3vpn_pb2.DeviceVRouterL3vpnCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.vrf_id = vrf_l3vpn_id
    msg.name = "example-l3vpn"
    response = vrouter_api.L3vpnCreate(msg)
    l3vpn_id = response.l3vpn.id
    # l3vpn_create.end
    assert not response.hdr.error

    # bgp_pe_ce.begin
    msg = api_bgp_pb2.BgpProtocolInstanceCreateReq()
    msg.hdr.vrouter_id = vrouter_id
    msg.hdr.session_id = session_id
    msg.settings.autonomous_system = 56000
    msg.settings.vrf_id = vrf_l3vpn_id
    msg.bgp_instance.router_id.ip = "10.1.1.1"
    response = bgp_api.Create(msg)

    msg = api_bgp_pb2.BgpProtocolInstanceIPv4AfiCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.hdr.vrf_id = vrf_l3vpn_id
    msg.ipv4_afi.export_auto_label = True
    msg.ipv4_afi.export_route_distinguisher.rd = "192.168.10.1:1"
    msg.ipv4_afi.vpn_import = True
    msg.ipv4_afi.vpn_export = True
    response = bgp_api.IPv4AfiCreate(msg)
    # bgp_vrf.end
    assert not response.hdr.error

    # bgp_vrf_rt.begin
    msg = api_bgp_pb2.BgpProtocolInstanceExportRouteTargetAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.hdr.vrf_id = vrf_l3vpn_id
    msg.address_family = resources_bgp_pb2.BGP_AFI_IPV4
    msg.route_target.rt = "65001:1"
    response = bgp_api.ExportRouteTargetAdd(msg)

    msg = api_bgp_pb2.BgpProtocolInstanceImportRouteTargetAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.hdr.vrf_id = vrf_l3vpn_id
    msg.address_family = resources_bgp_pb2.BGP_AFI_IPV4
    msg.route_target.rt = "65001:1"
    response = bgp_api.ImportRouteTargetAdd(msg)
    # bgp_vrf_rt.end
    assert not response.hdr.error

    # l3vpn_destroy.begin
    msg = api_device_vrouter_l3vpn_pb2.DeviceVRouterL3vpnDestroyReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.l3vpn_id = l3vpn_id
    response = vrouter_api.L3vpnDestroy(msg)
     # l3vpn_destroy.end
    assert not response.hdr.error
