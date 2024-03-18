
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
    from volta.v4.routing import api_ldp_pb2
    from volta.v4.routing import resources_ldp_pb2
    from volta.v4.routing import resources_common_pb2
    # imports.end

    # create_stub.begin
    vrouter_api = api_device_pb2_grpc.ApiDeviceVRouterStub(grpc_channel)
    ldp_api = api_routing_pb2_grpc.ApiLdpProtocolInstanceStub(grpc_channel)
    # create_stub.end

    # create_ldpinstance.begin
    msg = api_ldp_pb2.LdpProtocolInstanceCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.ldp_instance.transport_preferred_connection = resources_ldp_pb2.LDP_TRANSPORT_PREFERRED_CONNECTION_IPV4
    msg.ldp_instance.router_id = "5.5.5.5"
    msg.ldp_instance.ordered_control = True
    response = ldp_api.Create(msg)
    # create_ldpinstance.end
    assert not response.hdr.error

    # create_ldpafi.begin
    msg = api_ldp_pb2.LdpProtocolInstanceAddressFamilyCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.address_family_type = resources_common_pb2.ADDRESS_FAMILY_IPV4
    msg.address_family.targeted_sessions_information.accept_hellos = True
    msg.address_family.transport_address = "5.5.5.5"
    msg.address_family.targeted_sessions_information.access_list_from = "access-list-1"
    msg.address_family.label_accept_policy.neighbor_access_list = "access-list-2"
    response = ldp_api.AddressFamilyCreate(msg)
    # create_ldpafi.end
    assert not response.hdr.error

    interface_id = session.vrouter_interfaces[0]
    # interfaceadd.begin
    msg = api_ldp_pb2.LdpProtocolInstanceInterfaceAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.interface.interface_id = interface_id
    msg.interface.address_family_ipv4_enabled = True
    response = ldp_api.InterfaceAdd(msg)
    # interfaceadd.end
    assert not response.hdr.error

    # get_instance.begin
    msg = api_ldp_pb2.LdpProtocolInstanceGetReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    response = ldp_api.Get(msg)
    print(response)
    # get_instance.end
    assert not response.hdr.error

    # get_afi.begin
    msg = api_ldp_pb2.LdpProtocolInstanceAddressFamilyGetReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.address_family_type = resources_common_pb2.ADDRESS_FAMILY_IPV4
    response = ldp_api.AddressFamilyGet(msg)
    print(response)
    # get_afi.end
    assert not response.hdr.error


