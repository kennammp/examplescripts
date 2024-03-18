
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
    from volta.v4.policies import resources_access_list_pb2
    from volta.v4.policies import resources_policy_common_pb2
    from volta.v4.routing import resources_common_pb2
    # imports.end


    # create_stub.begin
    vrouter_api = api_device_pb2_grpc.ApiDeviceVRouterStub(grpc_channel)
    # create_stub.end

    # create_acl.begin
    msg = api_device_vrouter_pb2.DeviceVRouterAccessListCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.access_list.name = "access-list-1"
    e1 = msg.access_list.entry.add()
    e1.seq_num = 10
    e1.description = "Subnet-A"
    e1.network = "10.10.10.0/24"
    e2 = msg.access_list.entry.add()
    e2.seq_num = 20
    e2.description = "Subnet-B"
    e2.network = "10.10.30.0/24"
    response = vrouter_api.AccessListCreate(msg)
    # create_acl.end
    #print(response)

    # add_entry.begin
    msg = api_device_vrouter_pb2.DeviceVRouterAccessListEntryAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.access_list_id = 1
    msg.entry.seq_num = 30
    msg.entry.network = "10.70.10.0/24"
    response = vrouter_api.AccessListEntryAdd(msg)
    # add_entry.end
    print(response)

    # listacl.begin
    msg = api_device_vrouter_pb2.DeviceVRouterAccessListListReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    response = vrouter_api.AccessListList(msg)
    print(response)
    # listacl.end

    # del_entry.begin
    msg = api_device_vrouter_pb2.DeviceVRouterAccessListEntryDelReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.access_list_id = 1
    msg.entry_id = 10
    response = vrouter_api.AccessListEntryDel(msg)
    # del_entry.end

    # destroyacl.begin
    msg = api_device_vrouter_pb2.DeviceVRouterAccessListDestroyReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.access_list_id = 1
    response = vrouter_api.AccessListDestroy(msg)
    # destroyacl.end

    # listacl.begin
    msg = api_device_vrouter_pb2.DeviceVRouterAccessListListReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    response = vrouter_api.AccessListList(msg)
    print(response)
    # listacl2.end


