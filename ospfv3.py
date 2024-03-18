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
        addresses=["2001:db8:10:100::1/64"],
    )
    session.create_interface_ips(
        session.vrouter_ids[0],
        session.vrouter_interfaces[1],
        addresses=["2001:db8:10:500::1/64"],
    )

    yield
    session.terminate()

def test_ospf_features():
    session_id = session.session_id
    grpc_channel = session.grpc_channel
    vrouter_id = session.vrouter_ids[0]

    # imports.begin
    from volta.v4 import api_routing_pb2_grpc
    from volta.v4.routing import api_ospfv3_pb2
    from volta.v4.routing import resources_ospfv3_pb2
    # imports.end

    # create_stub.begin
    ospfv3_api = api_routing_pb2_grpc.ApiOspfv3ProtocolInstanceStub(grpc_channel)
    # create_stub.end

    # create_ospfinstance.begin
    msg = api_ospfv3_pb2.Ospfv3ProtocolInstanceCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.ospfv3_instance.router_id = "1.1.1.1"
    msg.ospfv3_instance.auto_cost_reference_bandwidth.value = 10000
    msg.ospfv3_instance.timers.lsa_min_arrival.value = 750
    msg.ospfv3_instance.timers.throttle_spf_delay.value = 4000
    response = ospfv3_api.Create(msg)
    # create_ospfinstance.end

    # create_area0.begin
    msg = api_ospfv3_pb2.Ospfv3ProtocolInstanceAreaAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.area.area_id = "0.0.0.0"
    response = ospfv3_api.AreaAdd(msg)
    # create_area0.end

    # create_area5.begin
    msg = api_ospfv3_pb2.Ospfv3ProtocolInstanceAreaAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.area.area_id = "5.5.5.5"
    msg.area.stub = True
    msg.area.no_summary = True
    response = ospfv3_api.AreaAdd(msg)
    # create_area5.end

    interface_id = 2

    # lif1_ospf.begin
    msg = api_ospfv3_pb2.Ospfv3ProtocolInstanceInterfaceAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.interface.interface_id = interface_id
    msg.interface.area_id = "0.0.0.0"
    msg.interface.link_type = resources_ospfv3_pb2.OSPFV3_LINK_TYPE_BROADCAST
    msg.interface.cost = 100
    msg.interface.priority.value = 10
    response = ospfv3_api.InterfaceAdd(msg)
    # lif1_ospf.end

    interface_id = 3

    # lif2_ospf.begin
    msg = api_ospfv3_pb2.Ospfv3ProtocolInstanceInterfaceAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.interface.interface_id = interface_id
    msg.interface.area_id = "5.5.5.5"
    msg.interface.link_type = resources_ospfv3_pb2.OSPFV3_LINK_TYPE_P2P
    response = ospfv3_api.InterfaceAdd(msg)
    # lif2_ospf.end


    # network_range.begin
    msg = api_ospfv3_pb2.Ospfv3ProtocolInstanceRangeAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.range.area_id = "5.5.5.5"
    msg.range.range_id = "2001:db8:10:500::/56"
    msg.range.not_advertise = False
    response = ospfv3_api.RangeAdd(msg)
    # network_range.end

    # get.begin
    msg = api_ospfv3_pb2.Ospfv3ProtocolInstanceGetReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    response = ospfv3_api.Get(msg)
    ospfv3_instance = response.ospfv3_instance
    print(ospfv3_instance)
    # get.end

