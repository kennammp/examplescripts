from example_session import session, printresp
import pytest


@pytest.fixture(autouse=True)
def prepare_session_for_example(request):
    session.initialize(request)
    session.create_vrouters(1)
    session.vrouter_interfaces = session.create_interfaces(3, session.vrouter_ids[0])
    yield
    session.terminate()


def test_sr_te_features():
    session_id = session.session_id
    grpc_channel = session.grpc_channel
    vrouter_id = session.vrouter_ids[0]

    # import.begin
    from volta.v4 import api_routing_pb2_grpc
    from volta.v4.routing import api_srte_pb2
    from volta.v4.routing import resources_srte_pb2
    from volta.v4.routing import api_pcep_pb2
    from volta.v4.routing import resources_pcep_pb2
    # import.end

    # stub.begin
    sr_te_api = api_routing_pb2_grpc.ApiSegmentRoutingTEStub(grpc_channel)
    pcep_api = api_routing_pb2_grpc.ApiPcepStub(grpc_channel)
    # stub.end
    
    # policy_create.begin
    msg = api_srte_pb2.SegmentRoutingTEPolicyCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.sr_policy.name = "blue"
    msg.sr_policy.color = 1
    msg.sr_policy.endpoint = "10.2.2.2"
    msg.sr_policy.priority.value = 10
    response = sr_te_api.PolicyCreate(msg)
    blue_policy_id =  response.sr_policy.id
    # policy_create.end
    assert not response.hdr.error

    # What's the correct order of the labels in the list?
    # segment_list_create.begin
    msg = api_srte_pb2.SegmentRoutingTESegmentListCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.segment_list.name = "R1_R2"
    segment1 = resources_srte_pb2.Segment()
    segment1.type1.label = 1000
    segment2 = resources_srte_pb2.Segment()
    segment2.type1.label = 2000
    msg.segment_list.segment.extend([segment1, segment2])
    response = sr_te_api.SegmentListCreate(msg)
    R1R2_segment_list_id = response.segment_list.id
    # segment_list_create.end
    assert not response.hdr.error

    # candidate_add_dynamic.begin
    msg = api_srte_pb2.SegmentRoutingTECandidatePathAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.sr_policy_id = blue_policy_id
    candidate_path = resources_srte_pb2.CandidatePath()
    candidate_path.name = "auto"
    candidate_path.preference.value = 25
    msg.candidate_path.extend([candidate_path])
    response = sr_te_api.CandidatePathAdd(msg)
    # candidate_add_dynamic.end
    assert not response.hdr.error

    # candidate_add.begin
    msg = api_srte_pb2.SegmentRoutingTECandidatePathAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.sr_policy_id = blue_policy_id
    candidate_path = resources_srte_pb2.CandidatePath()
    candidate_path.name = "fall-back"
    path = resources_srte_pb2.ExplicitCandidatePath()
    path.segment_list_id = R1R2_segment_list_id
    path.weight = 10
    candidate_path.type.explicit.explicit_candidate_path.extend([path])
    candidate_path.preference.value = 999
    msg.candidate_path.extend([candidate_path])
    response = sr_te_api.CandidatePathAdd(msg)
    # candidate_add.end
    assert not response.hdr.error

    # entity_create.begin
    msg = api_pcep_pb2.PcepEntityCreateReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id
    msg.pcep_entity.name = "R1_PCEP"
    response = pcep_api.EntityCreate(msg)
    # entity_create.end
    assert not response.hdr.error

    # neighbor_add.begin
    msg = api_pcep_pb2.PcepEntityNeighborAddReq()
    msg.hdr.session_id = session_id
    msg.hdr.vrouter_id = vrouter_id

    neighbor = resources_pcep_pb2.PcepNeighbor()
    neighbor.address = "10.1.1.1"
    neighbor.use_srte_draft07 = True
    neighbor.local_address = "192.168.1.1"
    neighbor.authentication_md5_password.value = "password"
    neighbor.precedence.value = 10
    
    neighbor2 = resources_pcep_pb2.PcepNeighbor()
    neighbor2.address = "10.2.2.2"
    neighbor2.use_srte_draft07 = True
    neighbor2.local_address = "192.168.1.1"
    neighbor2.authentication_md5_password.value = "password"
    neighbor2.precedence.value = 20
    
    msg.pcep_neighbor.extend([neighbor, neighbor2])
    response = pcep_api.EntityNeighborAdd(msg)
    # neighbor_add.end
    assert not response.hdr.error


