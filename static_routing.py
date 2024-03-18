import pytest
from example_session import session

# Scenario:
#               10.13.0.0/24 +---------+
#               fd01:13::/64 |         |
#                     +------+    R3   +----------+
#                     |   .30|         |          |
#                     |      +---------+          |
#                     |                           |
# +---+--------+ .10  |                           |
# |   |        +------+                           |
# |   |   VRF0 |            10.12.0.0/24          |
# |   |        +----------------------+      +----+----+
# |   +--------+                      +------+         |            192.168.0.0/16
# |   |        |                          .20|   R2    +----------+ fd01:abcd::/64
# |   |   VRF3 +---------+                   |         |
# |   |        |         |                   +----+----+
# |   +--------+         |                        |
# |  R1        |         |10.14.0.0/24            |
# +------------+         |                        |
#                        |                        |
#                        |                        |
#                        |   +---------+          |
#                        |.40|         |          |
#                        +---+   R4    +----------+
#                            |         |
#                            +---------+


@pytest.fixture(autouse=True)
def prepare_session_for_example(request):
    session.initialize(request)
    session.create_vrouters(1)
    session.vrouter_interfaces = session.create_interfaces(3, session.vrouter_ids[0])
    session.create_vrfs(3, session.vrouter_ids[0])
    session.create_interface_ips(
        session.vrouter_ids[0],
        session.vrouter_interfaces[0],
        addresses=["10.13.0.10/24", "fd01:13::10/64"],
    )

    session.create_interface_ips(
        session.vrouter_ids[0],
        session.vrouter_interfaces[1],
        addresses=["10.12.0.10/24"],
    )

    session.create_interface_ips(
        session.vrouter_ids[0],
        session.vrouter_interfaces[2],
        addresses=["10.14.0.10/24"],
        vrf_id=3,
    )
    yield
    session.terminate()


def test_static_routing_features():
    session_id = session.session_id
    grpc_channel = session.grpc_channel
    vrouter_id = session.vrouter_ids[0]

    # example_imports.begin
    from volta.v4 import api_routing_pb2_grpc
    from volta.v4.routing import api_static_pb2

    # example_imports.end
    
    # stub.begin
    static_api = api_routing_pb2_grpc.ApiStaticProtocolInstanceStub(grpc_channel)
    # stub.end

    # set_route.begin
    msg = api_static_pb2.StaticProtocolInstanceRouteSetReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    route = msg.static_route.add()
    route.prefix = "192.168.55.0/24"
    route.next_hop.address = "10.13.0.30"
    route_ipv6 = msg.static_route.add()
    route_ipv6.prefix = "fd01:abcd::/64"
    route_ipv6.next_hop.address = "fd01:13::30"
    response = static_api.RouteSet(msg)
    # set_route.end
    assert not response.hdr.error

    interface_id = session.vrouter_interfaces[0]
    # set_static_route_interface.begin
    msg = api_static_pb2.StaticProtocolInstanceRouteAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.static_route.prefix = "192.168.77.0/24"
    msg.static_route.next_hop.interface_id = interface_id
    msg.static_route.next_hop.address = "10.13.0.30"
    response = static_api.RouteAdd(msg)
    # set_static_route_interface.end
    assert not response.hdr.error

    # set_route_ecmp.begin
    msg = api_static_pb2.StaticProtocolInstanceRouteAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.static_route.prefix = "192.168.111.0/24"
    msg.static_route.distance = 100
    msg.static_route.next_hop.address = "10.13.0.30"
    response = static_api.RouteAdd(msg)

    msg = api_static_pb2.StaticProtocolInstanceRouteAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.static_route.prefix = "192.168.111.0/24"
    msg.static_route.distance = 100
    msg.static_route.next_hop.address = "10.12.0.20"
    response = static_api.RouteAdd(msg)
    # set_route_ecmp.end
    assert not response.hdr.error

    # set_route_vrf.begin
    msg = api_static_pb2.StaticProtocolInstanceRouteAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.static_route.prefix = "192.168.22.0/24"
    msg.static_route.vrf_id = 3
    msg.static_route.label.label.extend([456, 88])
    msg.static_route.next_hop.address = "10.14.0.40"
    response = static_api.RouteAdd(msg)
    # set_route_vrf.end
    assert not response.hdr.error

    # set_static_route_blackhole.begin
    msg = api_static_pb2.StaticProtocolInstanceRouteAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.static_route.prefix = "192.168.99.0/24"
    msg.static_route.blackhole.Clear()
    response = static_api.RouteAdd(msg)
    # set_static_route_blackhole.end
    assert not response.hdr.error

    # list_routes.begin
    msg = api_static_pb2.StaticProtocolInstanceRouteListReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    response = static_api.RouteList(msg)
    print(response)
    # list_routes.end
    assert not response.hdr.error

    # set_static_route_mpls.begin
    msg = api_static_pb2.StaticProtocolInstanceMplsBindingSetReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    binding = msg.mpls_binding.add()
    binding.prefix.ipv4_net.address.ip = "192.168.66.0"
    binding.prefix.ipv4_net.mask = 24
    binding.label = 66
    response = static_api.MplsBindingSet(msg)
    # set_static_route_mpls.end
    assert not response.hdr.error

    # add_mpls_binding.begin
    msg = api_static_pb2.StaticProtocolInstanceMplsBindingAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.mpls_binding.prefix.ipv4_net.address.ip = "192.168.88.0"
    msg.mpls_binding.prefix.ipv4_net.mask = 24
    msg.mpls_binding.label = 688
    response = static_api.MplsBindingAdd(msg)
    # add_mpls_binding.end

    # list_static_route_mpls.begin
    msg = api_static_pb2.StaticProtocolInstanceMplsBindingListReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    response = static_api.MplsBindingList(msg)
    print(response)
    # list_static_route_mpls.end
    assert not response.hdr.error

