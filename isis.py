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
        addresses=["10.13.0.10/24", "fd01:13::10/64"],
    )
    session.create_interface_ips(
        session.vrouter_ids[0],
        session.vrouter_interfaces[1],
        addresses=["10.12.0.10/24"],
    )
    yield
    session.terminate()


def test_isis_features():
    session_id = session.session_id
    grpc_channel = session.grpc_channel
    vrouter_id = session.vrouter_ids[0]

    # example_imports.begin
    from volta.v1 import api_routing_pb2_grpc
    from volta.v1.routing import api_isis_pb2
    from volta.v1.routing import resources_isis_pb2
    from volta.v1.routing import resources_sr_pb2
    # example_imports.end

    # stub.begin
    isis_api = api_routing_pb2_grpc.ApiIsisProtocolInstanceStub(grpc_channel)
    # stub.end

    # create_isis_instance.begin
    msg = api_isis_pb2.IsisProtocolInstanceCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.settings.area = "0001"
    msg.isis_instance.network.network1.value = "49.0001.1921.6801.0001.00"
    msg.isis_instance.metric_style.metric_style = resources_isis_pb2.ISIS_METRIC_STYLE_WIDE
    msg.isis_instance.level.level = resources_isis_pb2.ISIS_LEVEL_1_2
    msg.isis_instance.level1.auth.md5 = "volta"
    msg.isis_instance.level1.ipv4_afi.default_originate.always.value = True
    msg.isis_instance.level1.ipv4_afi.redistribute.redistribute = resources_common_pb2.ROUTING_REDISTRIBUTE_BGP
    msg.isis_instance.attached_bit.value = True
    msg.isis_instance.overload_bit.value = True
    response = isis_api.Create(msg)
    # create_isis_instance.end
    assert not response.hdr.error

    interface_id = session.vrouter_interfaces[0]
    # add_interface_l2.begin
    msg = api_isis_pb2.IsisProtocolInstanceInterfaceAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.interface_id = interface_id
    msg.interface.ipv4_enabled.value = True
    msg.interface.ipv6_enabled.value = True
    msg.interface.passive.value = False
    msg.interface.level.level = resources_isis_pb2.ISIS_LEVEL_2
    msg.interface.level2.metric.value = 10
    msg.interface.level2.priority.value = "15"
    msg.interface.level2.timers.hello_interval = "50"
    response = isis_api.InterfaceAdd(msg)
    # add_interface_l2.end
    assert not response.hdr.error

    interface_id = session.vrouter_interfaces[1]
    # add_interface_l1.begin
    msg = api_isis_pb2.IsisProtocolInstanceInterfaceAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.interface_id = interface_id
    msg.interface.ipv4_enabled.value = True
    msg.interface.passive.value = False
    msg.interface.level.level = resources_isis_pb2.ISIS_LEVEL_1
    msg.interface.level1.metric.value = 5
    response = isis_api.InterfaceAdd(msg)
    # add_interface_l1.end
    assert not response.hdr.error

    # create_sr.begin
    msg = api_isis_pb2.IsisProtocolInstanceSegmentRoutingCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.segment_routing.enable.value = True
    msg.segment_routing.max_stack_depth.value = 2
    msg.segment_routing.global_block.start.value = 16000
    msg.segment_routing.global_block.end.value = 23999
    response = isis_api.SegmentRoutingCreate(msg)
    # create_sr.end
    assert not response.hdr.error

    # add_sr_prefix.begin
    msg = api_isis_pb2.IsisProtocolInstanceSegmentRoutingPrefixAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.prefix.prefix.value = "192.168.10.1/32"
    msg.prefix.index.value = 101
    msg.prefix.phb.phb = resources_sr_pb2.SR_PHB_PHP
    response = isis_api.SegmentRoutingPrefixAdd(msg)
    # add_sr_prefix.end
    assert not response.hdr.error

    # get_config.begin
    msg = api_isis_pb2.IsisProtocolInstanceFullGetReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    response = isis_api.FullGet(msg)
    for isis_interface in response.isis_instance.interface:
        print(isis_interface)
    print(response.isis_instance.level1)
    print(response.isis_instance.level2)
    print(response.isis_instance.segment_routing)
    # get_config.end
    assert not response.hdr.error

