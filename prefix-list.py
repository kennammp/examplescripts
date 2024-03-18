
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
    from volta.v4.policies import resources_prefix_list_pb2
    from volta.v4.policies import resources_policy_common_pb2
    from volta.v4.routing import resources_common_pb2
    # imports.end

    # create_stub.begin
    vrouter_api = api_device_pb2_grpc.ApiDeviceVRouterStub(grpc_channel)
    # create_stub.end

    vrouter_id = 1

    # create_pl.begin
    msg = api_device_vrouter_pb2.DeviceVRouterPrefixListCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.prefix_list.name = "prefix-list-1"
    e1 = msg.prefix_list.entry.add()
    e1.seq_num = 10
    e1.prefix = "10.10.0.0/16"
    e1.min_prefix_len = 24
    e2 = msg.prefix_list.entry.add()
    e2.seq_num = 20
    e2.prefix = "10.30.0.0/16"
    e2.min_prefix_len = 24
    response = vrouter_api.PrefixListCreate(msg)
    # create_pl.end

    # listpl.begin
    msg = api_device_vrouter_pb2.DeviceVRouterPrefixListListReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    response = vrouter_api.PrefixListList(msg)
    print(response)
    # listpl.end

    # add_entry.begin
    msg = api_device_vrouter_pb2.DeviceVRouterPrefixListEntryAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.prefix_list_id = 1
    msg.entry.seq_num = 30
    msg.entry.prefix = "10.70.0.0/16"
    response = vrouter_api.PrefixListEntryAdd(msg)
    # add_entry.end
    print(response)

    # del_entry.begin
    msg = api_device_vrouter_pb2.DeviceVRouterPrefixListEntryDelReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.prefix_list_id = 1
    msg.entry_id = 10
    response = vrouter_api.PrefixListEntryDel(msg)
    # del_entry.end

    # destroypl.begin
    msg = api_device_vrouter_pb2.DeviceVRouterPrefixListDestroyReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.prefix_list_id = 1
    response = vrouter_api.PrefixListDestroy(msg)
    # destroypl.end