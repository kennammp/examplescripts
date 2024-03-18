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
    from volta.v4.policies import resources_community_list_pb2
    from volta.v4.policies import resources_policy_common_pb2
    from volta.v4.routing import resources_common_pb2
    # imports.end

    # stub.begin
    vrouter_api = api_device_pb2_grpc.ApiDeviceVRouterStub(grpc_channel)
    # stub.end

    vrouter_id = 1

    # create.begin
    msg = api_device_vrouter_pb2.DeviceVRouterCommunityListCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.community_list.name = "community_list-1"
    e1 = msg.community_list.entry.add()
    e1.seq_num = 10
    e1.communities.extend(["64322:23", "64328:24"])
    e2 = msg.community_list.entry.add()
    e2.seq_num = 20
    e2.communities.extend(["64635:55"])
    response = vrouter_api.CommunityListCreate(msg)
    # create.end
    assert not response.hdr.error

    # list.begin
    msg = api_device_vrouter_pb2.DeviceVRouterCommunityListListReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    response = vrouter_api.CommunityListList(msg)
    print(response)
    # list.end
    assert not response.hdr.error

    # add_entry.begin
    msg = api_device_vrouter_pb2.DeviceVRouterCommunityListEntryAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.community_list_id = 1
    msg.entry.seq_num = 30
    msg.entry.communities.extend(["64635:23"])
    response = vrouter_api.CommunityListEntryAdd(msg)
    # add_entry.end
    assert not response.hdr.error

    # del_entry.begin
    msg = api_device_vrouter_pb2.DeviceVRouterCommunityListEntryDelReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.community_list_id = 1
    msg.entry_id = 10
    response = vrouter_api.CommunityListEntryDel(msg)
    # del_entry.end
    assert not response.hdr.error

    # destroy.begin
    msg = api_device_vrouter_pb2.DeviceVRouterCommunityListDestroyReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.community_list_id = 1
    response = vrouter_api.CommunityListDestroy(msg)
    # destroy.end
    assert not response.hdr.error


