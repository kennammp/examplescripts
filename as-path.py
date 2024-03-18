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
    from volta.v4.policies import resources_as_path_pb2
    from volta.v4.policies import resources_policy_common_pb2
    from volta.v4.routing import resources_common_pb2
    # imports.end

    # create_stub.begin
    vrouter_api = api_device_pb2_grpc.ApiDeviceVRouterStub(grpc_channel)
    # create_stub.end

    vrouter_id = 1

    # create_aspath.begin
    msg = api_device_vrouter_pb2.DeviceVRouterAsPathCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.as_path.name = "as_path-1"
    e1 = msg.as_path.entry.add()
    e1.as_path = "64617"
    e2 = msg.as_path.entry.add()
    e2.as_path = "64655"
    response = vrouter_api.AsPathCreate(msg)
    # create_aspath.end
    assert not response.hdr.error

    # listaspath.begin
    msg = api_device_vrouter_pb2.DeviceVRouterAsPathListReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    response = vrouter_api.AsPathList(msg)
    print(response)
    # listaspath.end
    assert not response.hdr.error
    
    # add_entry.begin
    msg = api_device_vrouter_pb2.DeviceVRouterAsPathEntryAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.as_path_id = 1
    msg.entry.as_path = "64635"
    response = vrouter_api.AsPathEntryAdd(msg)
    # add_entry.end
    assert not response.hdr.error
    
    # del_entry.begin
    msg = api_device_vrouter_pb2.DeviceVRouterAsPathEntryDelReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.as_path_id = 1
    msg.entry_id = 10
    response = vrouter_api.AsPathEntryDel(msg)
    # del_entry.end
    assert not response.hdr.error
    
    # destroy.begin
    msg = api_device_vrouter_pb2.DeviceVRouterAsPathDestroyReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.as_path_id = 1
    response = vrouter_api.AsPathDestroy(msg)
    # destroy.end
    assert not response.hdr.error
    
    



