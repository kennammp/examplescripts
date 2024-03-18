
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
    from volta.v4.policies import resources_acl_pb2
    from volta.v4.policies import resources_policy_common_pb2
    from volta.v4.routing import resources_common_pb2
    # imports.end

    # create_stub.begin
    vrouter_api = api_device_pb2_grpc.ApiDeviceVRouterStub(grpc_channel)
    # create_stub.end

    vrouter_id = 1

    # aclcreate.begin
    msg = api_device_vrouter_pb2.DeviceVRouterAclCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.name = "acl1"
    response = vrouter_api.AclCreate(msg)
    # aclcreate.end

    # entry.begin
    acl = response.acl
    
    msg = api_device_vrouter_pb2.DeviceVRouterAclEntryAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.acl_id = acl.id
    ace_msg = msg.ace
    ace_msg.acl_id = acl.id
    ace_msg.sequence_number = 10
    action = ace_msg.action.add()
    action.type = resources_acl_pb2.MATCH_ACTION_PERMIT
    match = ace_msg.match.add()
    match.ipv4_dst_addr.dst_addr = "10.10.30.0/24"
    match = ace_msg.match.add()
    match.ipv4_src_addr.src_addr = "192.168.10.0/24"
    response = vrouter_api.AclEntryAdd(msg)

    msg = api_device_vrouter_pb2.DeviceVRouterAclEntryAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.acl_id = acl.id
    ace_msg = msg.ace
    ace_msg.acl_id = acl.id
    ace_msg.sequence_number = 20
    action = ace_msg.action.add()
    action.type = resources_acl_pb2.MATCH_ACTION_PERMIT
    match = ace_msg.match.add()
    match.ipv4_dst_addr.dst_addr = "10.10.50.0/24"
    match = ace_msg.match.add()
    match.ipv4_src_addr.src_addr = "192.168.50.0/24"
    response = vrouter_api.AclEntryAdd(msg)
    # entry.end

    interface_id = 2

    # intadd.begin
    msg = api_device_vrouter_pb2.DeviceVRouterInterfaceAclAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.acl_id = acl.id
    msg.interface_id = interface_id
    response = vrouter_api.InterfaceAclAdd(msg)
    # intadd.end

    # view.begin
    msg = api_device_vrouter_pb2.DeviceVRouterInterfaceAclListReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.interface_id = interface_id
    response = vrouter_api.InterfaceAclList(msg)
    print(response)

    msg = api_device_vrouter_pb2.DeviceVRouterAclListReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    response = vrouter_api.AclList(msg)
    print(response)
    # view.end

    # entrydel.begin
    msg = api_device_vrouter_pb2.DeviceVRouterAclEntryDelReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.acl_id = 1
    msg.ace_sequence_number = 10
    response = vrouter_api.AclEntryDel(msg)
    # entrydel.end


    msg = api_device_vrouter_pb2.DeviceVRouterAclListReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    response = vrouter_api.AclList(msg)
    print(response)


    # intdel.begin
    msg = api_device_vrouter_pb2.DeviceVRouterInterfaceAclDelReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.acl_id = 1
    msg.interface_id = 2
    response = vrouter_api.InterfaceAclDel(msg)
    # intdel.end

    msg = api_device_vrouter_pb2.DeviceVRouterInterfaceAclListReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.interface_id = 2
    response = vrouter_api.InterfaceAclList(msg)
    print(response)

    # acldel.begin
    msg = api_device_vrouter_pb2.DeviceVRouterAclDestroyReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.acl_id = 1
    response = vrouter_api.AclDestroy(msg)
    # acldel.end

    msg = api_device_vrouter_pb2.DeviceVRouterAclListReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    response = vrouter_api.AclList(msg)
    print(response)
