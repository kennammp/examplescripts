from example_session import session, printresp
import pytest

@pytest.fixture(autouse=True)
def prepare_session_for_example(request):
    session.initialize(request)
    session.create_vrouters(1)
    session.vrouter_interfaces = session.create_interfaces(2, session.vrouter_ids[0])
    session.create_interface_ips(
        session.vrouter_ids[0],
        session.vrouter_interfaces[0],
        addresses=["10.100.10.15/24"],
    )
    session.create_interface_ips(
        session.vrouter_ids[0],
        session.vrouter_interfaces[1],
        addresses=["192.168.10.1/30"],
    )

    yield
    session.terminate()

def test_features():
    session_id = session.session_id
    grpc_channel = session.grpc_channel
    vrouter_id = session.vrouter_ids[0]

    # imports.begin
    from volta.v4 import api_device_pb2_grpc
    from volta.v4 import api_device_vrouter_pb2
    from volta.v4 import api_routing_pb2_grpc
    from volta.v4.policies import resources_rmap_pb2
    from volta.v4.policies import resources_policy_common_pb2
    from volta.v4.routing import resources_common_pb2
    # imports.end

    # create_stub.begin
    vrouter_api = api_device_pb2_grpc.ApiDeviceVRouterStub(grpc_channel)
    # create_stub.end

    vrouter_id = 1

    # create_rmap.begin
    msg = api_device_vrouter_pb2.DeviceVRouterRouteMapCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.route_map.name = "route-map-1"
    e1 = msg.route_map.entry.add()
    e1.seq_num = 10
    e1_match = e1.match.add()
    e1_match.peer_ipv4 = "2.2.2.2"
    e1_action = e1.action.add()
    e1_action.set_ipv4_next_hop = "1.2.3.4"
    e2 = msg.route_map.entry.add()
    e2.seq_num = 20
    e2_match = e2.match.add()
    e2_match.ipv4_address_prefix_list = "prefix-list-1"
    e2_action = e2.action.add()
    e2_action.set_metric = 200
    response = vrouter_api.RouteMapCreate(msg)
    # create_rmap.end

    # add_entry.begin
    msg = api_device_vrouter_pb2.DeviceVRouterRouteMapEntryAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.route_map_id = 1
    msg.entry.seq_num = 30
    e1_match = msg.entry.match.add()
    e1_match.ipv4_address_access_list_name = "access-list-1"
    msg.entry.type = resources_policy_common_pb2.POLICY_ENTRY_TYPE_PERMIT
    response = vrouter_api.RouteMapEntryAdd(msg)
    # add_entry.end

    # del_entry.begin
    msg = api_device_vrouter_pb2.DeviceVRouterRouteMapEntryDelReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.route_map_id = 1
    msg.entry_id = 10
    response = vrouter_api.RouteMapEntryDel(msg)
    # del_entry.end

    # listrmap.begin
    msg = api_device_vrouter_pb2.DeviceVRouterRouteMapListReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    response = vrouter_api.RouteMapList(msg)
    print(response)
    # listrmap.end

    # destroyrmap.begin
    msg = api_device_vrouter_pb2.DeviceVRouterRouteMapDestroyReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.route_map_id = 1
    response = vrouter_api.RouteMapDestroy(msg)
    # destroyrmap.end
