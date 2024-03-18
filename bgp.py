from example_session import session, printresp
import pytest


@pytest.fixture(autouse=True)
def prepare_session_for_example(request):
    session.initialize(request)
    session.create_vrouters(1)
    session.vrouter_interfaces = session.create_interfaces(3, session.vrouter_ids[0])
    session.create_interface_ips(
        session.vrouter_ids[0],
        session.vrouter_interfaces[0],
        addresses=["10.13.0.10/24", "fd01:13::10/64"],
    )
    session.create_interface_ips(
        session.vrouter_ids[0],
        session.vrouter_interfaces[1],
        addresses=["10.14.0.10/24", "fd01:14::10/64"],
    )
    session.create_interface_ips(
        session.vrouter_ids[0],
        session.vrouter_interfaces[2],
        addresses=["10.12.0.10/24"],
    )
    yield
    session.terminate()


def test_bgp_features():
    session_id = session.session_id
    grpc_channel = session.grpc_channel
    vrouter_id = session.vrouter_ids[0]

    # imports.begin
    from volta.v4 import api_routing_pb2_grpc
    from volta.v4.routing import api_bgp_pb2
    from volta.v4.routing import resources_bgp_pb2
    from volta.v4.routing import resources_common_pb2
    from volta.v4 import api_device_vrouter_pb2
    # imports.end
    from google.protobuf.json_format import MessageToJson


    # stub.begin
    bgp_api = api_routing_pb2_grpc.ApiBgpProtocolInstanceStub(grpc_channel)
    # stub.end

    # create_bgp_instance.begin
    msg = api_bgp_pb2.BgpProtocolInstanceCreateReq()
    msg.hdr.vrouter_id = vrouter_id
    msg.hdr.session_id = session_id
    msg.settings.autonomous_system = 65001
    msg.settings.vrf_id = 0
    msg.bgp_instance.router_id.ip = "10.13.0.10"
    msg.bgp_instance.route_selection.bestpath_aspath_ignore = True
    response = bgp_api.Create(msg)
    # create_bgp_instance.end
    printresp(response)
    assert not response.hdr.error
    
    # fullget_bgp_instance.begin
    msg = api_bgp_pb2.BgpProtocolInstanceFullGetReq()
    msg.hdr.vrouter_id = vrouter_id
    msg.hdr.session_id = session_id
    msg.hdr.vrf_id = 0
    response = bgp_api.FullGet(msg)
    bgp_instance = response.full_instance
    print(bgp_instance)
    # fullget_bgp_instance.end
    assert not response.hdr.error

    interface_id = session.vrouter_interfaces[0]
    # add_peer.begin
    msg = api_bgp_pb2.BgpProtocolInstancePeerAddReq()
    msg.hdr.vrouter_id = vrouter_id
    msg.hdr.session_id = session_id
    msg.hdr.vrf_id = 0
    msg.peer_address.ipv4.ip = "10.13.0.40"
    msg.peer.remote_as = 65002
    msg.peer.is_ipv4_afi_enabled = True
    msg.peer.is_ipv6_afi_enabled = True
    msg.peer.ipv4_in_rmap = "route-map-1"
    response = bgp_api.PeerAdd(msg)
    # add_peer.end
    assert not response.hdr.error

    # get_peer.begin
    msg = api_bgp_pb2.BgpProtocolInstancePeerGetReq()
    msg.hdr.vrouter_id = vrouter_id
    msg.hdr.session_id = session_id
    msg.hdr.vrf_id = 0
    msg.peer_address.ipv4.ip = "10.13.0.40"
    response = bgp_api.PeerGet(msg)
    # get_peer.end
    assert not response.hdr.error

    # afiv4.begin
    msg = api_bgp_pb2.BgpProtocolInstanceIPv4AfiCreateReq()
    msg.hdr.vrouter_id = vrouter_id
    msg.hdr.session_id = session_id
    msg.hdr.vrf_id = 0
    msg.ipv4_afi.export_route_distinguisher.rd = "65001:1"
    response = bgp_api.IPv4AfiCreate(msg)
    # afiv4.end
    assert not response.hdr.error

    # redistribute.begin
    msg = api_bgp_pb2.BgpProtocolInstanceRedistributeAddReq()
    msg.hdr.vrouter_id = vrouter_id
    msg.hdr.session_id = session_id
    msg.hdr.vrf_id = 0
    msg.address_family = resources_bgp_pb2.BGP_AFI_IPV4
    msg.redistribute.route_map = "route-map-2"
    msg.redistribute.redistribute = resources_common_pb2.ROUTING_REDISTRIBUTE_ISIS
    response = bgp_api.RedistributeAdd(msg)
    # redistribute.end
    assert not response.hdr.error

    # ipv4_network.begin
    msg = api_bgp_pb2.BgpProtocolInstanceIPv4NetworkAddReq()
    msg.hdr.vrouter_id = vrouter_id
    msg.hdr.session_id = session_id
    msg.hdr.vrf_id = 0
    msg.ipv4_network.address.ip = "10.10.10.0"
    msg.ipv4_network.mask = 24
    response = bgp_api.Ipv4NetworkAdd(msg)
    # ipv4_network.end
    assert not response.hdr.error

    # export_rt.begin
    msg = api_bgp_pb2.BgpProtocolInstanceExportRouteTargetAddReq()
    msg.hdr.vrouter_id = vrouter_id
    msg.hdr.session_id = session_id
    msg.hdr.vrf_id = 0
    msg.address_family = resources_bgp_pb2.BGP_AFI_IPV4
    msg.route_target.rt = "65000:10"
    response = bgp_api.ExportRouteTargetAdd(msg)
    # export_rt.end
    assert not response.hdr.error
    
    # import_rt.begin
    msg = api_bgp_pb2.BgpProtocolInstanceImportRouteTargetAddReq()
    msg.hdr.vrouter_id = vrouter_id
    msg.hdr.session_id = session_id
    msg.hdr.vrf_id = 0
    msg.address_family = resources_bgp_pb2.BGP_AFI_IPV4
    msg.route_target.rt = "65000:10"
    response = bgp_api.ImportRouteTargetAdd(msg)
    # import_rt.end
    assert not response.hdr.error

    # del_peer.begin
    msg = api_bgp_pb2.BgpProtocolInstancePeerDelReq()
    msg.hdr.vrouter_id = vrouter_id
    msg.hdr.session_id = session_id
    msg.hdr.vrf_id = 0
    msg.peer_address.ipv4.ip = "10.13.0.40"
    response = bgp_api.PeerDel(msg)
    # del_peer.end
    assert not response.hdr.error

    # destroy_bgp_instance.begin
    msg = api_bgp_pb2.BgpProtocolInstanceDestroyReq()
    msg.hdr.vrouter_id = vrouter_id
    msg.hdr.session_id = session_id
    msg.hdr.vrf_id = 0
    response = bgp_api.Destroy(msg)
    # destroy_bgp_instance.end
    assert not response.hdr.error
    

