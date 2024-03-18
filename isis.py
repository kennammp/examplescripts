from example_session import session, printresp
import pytest


# Scenario:
#         AREA 1                          AREA 2
#    +---------------+              +----------------+

#       +---------+     10.13.0.0/24   +---------+
#       |   R1    |     fd01:13::10/64 |   R3    |
#       |   L1L2  +--------------------+   L2    |
#       |         |.10              .30|         |
#       +---------+                    +---------+
#            |
#            |
#            |
#            | 10.12.0.0/24
#            |
#            |
#            |
#       +---------+
#       |   R2    |
#       |   L1    |
#       |         |
#       +---------+



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
    from volta.v4 import api_routing_pb2_grpc
    from volta.v4.routing import api_isis_pb2
    from volta.v4.routing import resources_isis_pb2
    from volta.v4.routing import resources_sr_pb2
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
    msg.isis_instance.level1.auth.md5.value = "volta"
    msg.isis_instance.level1.ipv4_afi.default_originate.always.value = True
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
    msg.interface.level2.priority.value = 15
    msg.interface.level2.timers.hello_interval.value = 50
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
    print(response.isis_instance.interface)
    print(response.isis_instance.network)
    print(response.isis_instance.instance_settings)
    print(response.isis_instance.level1)
    print(response.isis_instance.level2)
    print(response.isis_instance.segment_routing)
    # get_config.end
    assert not response.hdr.error
    
    """ Segment routing output only
    # get_config_output.begin
enable {
  value: true
}
max_stack_depth {
  value: 2
}
global_block {
  start {
    value: 16000
  }
  end {
    value: 23999
  }
}
prefix {
  prefix {
    value: "192.168.10.1/32"
  }
  index {
    value: 101
  }
  phb {
    phb: SR_PHB_PHP
  }
}
    # get_config_output.end
    """

    # Extra examples, more complex and not needed

    # # update_isis_instance.begin
    # msg = api_isis_pb2.IsisProtocolInstanceUpdateReq()
    # msg.hdr.session_id = session_id
    # msg.hdr.vrouter_id = vrouter_id
    # msg.isis_instance.purge_origin.value = True
    # msg.isis_instance.isis_timers.max_lsp_lifetime.value = 2500
    # msg.isis_instance.isis_timers.lsp_refresh_interval.value = 2200
    # msg.isis_instance.topology.ipv6_unicast_active.value = True
    # msg.isis_instance.level2.auth.md5.value = "286755fad04869ca523320acce0dc6a4"
    # msg.isis_instance.level2.auth.snp.snp_auth = resources_isis_pb2.ISIS_AUTH_SNP_VALIDATE
    # response = isis_api.Update(msg)
    # # update_isis_instance.end
    # assert not response.hdr.error

    # interface_id = session.vrouter_interfaces[2]
    # # add_interface_l1.begin
    # msg = api_isis_pb2.IsisProtocolInstanceInterfaceAddReq()
    # msg.hdr.session_id = session_id
    # msg.hdr.vrouter_id = vrouter_id
    # msg.interface_id = interface_id
    # msg.interface.ipv4_enabled.value = True
    # msg.interface.passive.value = False
    # msg.interface.level1.metric.value = 10
    # response = isis_api.InterfaceAdd(msg)
    # # add_interface_l1.end
    # assert not response.hdr.error

    # # del_interface_l1.begin
    # msg = api_isis_pb2.IsisProtocolInstanceInterfaceDelReq()
    # msg.hdr.session_id = session_id
    # msg.hdr.vrouter_id = vrouter_id
    # msg.interface_id = interface_id
    # response = isis_api.InterfaceDel(msg)
    # # del_interface_l1.end
    # assert not response.hdr.error

    # interface_id = session.vrouter_interfaces[0]
    # # update_interface.begin
    # msg = api_isis_pb2.IsisProtocolInstanceInterfaceUpdateReq()
    # msg.hdr.session_id = session_id
    # msg.hdr.vrouter_id = vrouter_id
    # msg.interface_id = interface_id
    # msg.interface.ipv6_enabled.value = False
    # # msg.interface.hello_padding.value = True
    # # msg.interface.point_to_point.value = True
    # # msg.interface.threeway_handshake.value = True
    # response = isis_api.InterfaceUpdate(msg)
    # # update_interface.end
    # assert not response.hdr.error

    # # del_sr_prefix.begin
    # msg = api_isis_pb2.IsisProtocolInstanceSegmentRoutingPrefixDelReq()
    # msg.hdr.session_id = session_id
    # msg.hdr.vrouter_id = vrouter_id
    # msg.prefix.prefix.value = "10.45.0.0/24"
    # response = isis_api.SegmentRoutingPrefixDel(msg)
    # # del_sr_prefix.end
    # assert not response.hdr.error