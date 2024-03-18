"""
2020-03-18
(c) Volta Networks Inc.
__author__: Josep Lluis Ferrer  <jl@voltanet.io>

Simple example of how to setup egress Qos in a VRouter using the calls available in the
gRPC API (via a client).

This script is a demonstration of a workflow to setup QoS in a VRouter in the egress
stage.


Volta QoS VRouter resources:

- QosBundle. Set of virtual queues
    * QosServiceQueue. Virtual Queue in a bundle.
        * Shaper. A Queue has a Shaper. Supported rates:
            - kbps
            - %total_bandwidth
        * DropPolicy. A Queue has an associated Drop Policy
    * Logical Interfaces (LIFs). One or more (output) LIFs enqueue in the QosBundles.
      The LIFs can only be attached to the QoSBundle once the entire hierarchy is complete.
- QosMap. Set of traffic Mappings to classify / mark traffic
    * QoSMapping: Rule used in Classification (ingress) and Marking/remarking (egress)
        * Classification: List of headers to parse (VLAN, MPLS, LL, DCSP) with mapping of Cos value TO priority / color.
        * Marking/Remarking: List of headers to parse (VLAN, MPLS, LL, DCSP) with mapping of Cos value FROM priority / color.
- QosScheduler. Scheduler. Supported: Round Robin (RR), Weighted Fair Queue (WFQ), Strict Priority (SP)
    * Shaper. Each scheduler has a Shaper
- QosDropPolicy. Vrouter drop policies, can be configured as the drop policy on queues of the QueueBundle
    * TailDrop
    * WRED. Supported 3 colors. Configuration:
        * Parameters (per color): low Threshold, high Thres., Drop probability high threshold
- DefaultDropPolicy (id=0). Default DropPolicy available in VRouter
    * type: WRED
        * GREEN. high 250kB, low (green_high*7/10) , drop prob = 100
        * YELLOW. high 125kb, low (yellow_high*7/10) , drop prob = 100
        * RED. high 0kb, low (red_high*7/10) , drop prob = 100
- Creation of hierarchies: Use QoSConnect / QoSDisconnect APIs to connect queues with schedulers.
    * Connection parameters: weight / priority, based on the scheduler where the connection is created
    * Connections:
        * queue -> scheduler (queue_id, sched_id)
        * scheduler -> scheduler (sched_id, sched_id)
        * scheduler --> port scheduler (sched_id, port_id, egress_queue_id)

- Classification/Marking: Use QosCosMapLifAttach / QosCosMapLifDetach APIs to apply classification/re/marking

When connecting to the non-programmable part of the port users must specify port_id
and the queue_id. Priority of the queues is shown in the diagram below:

     QUEUE N
    +------------------+
    |                  +---------------+    +--------+
    +------------------+               |    |        |
                                       +---->   SP   +--+
                                            |        |  |
    QUEUE N-1                           +-->+        |  |
    +------------------+                |   +--------+  |
    |                  +-+ +-------+    |               |   +--------+
    +------------------+ | |       |    |               |   |        |
                         +>+   FQ  +----+               +-->+        |     +----------------------+
     ...                   |       |                        |  SP    +---->+ PHY PORT             |
    +------------------+ +>+       |        +-------------->+        |     +----------------------+
    |                  +-+ +-------+        |               |        |
    +------------------+                    |               +--------+
                                            |
                                            |
     0                                      |
    +------------------+                    |
    |                  +--------------------+
    +------------------+



"""
import grpc

from volta.v4.utils.client_auth_interceptor import header_adder_interceptor
# grpc vrouter qos resources
from volta.v4 import api_device_pb2_grpc
from volta.v4 import api_device_vrouter_qos_pb2
from volta.v4 import resources_device_vrouter_qos_pb2

# Session utils
from volta.v4 import api_service_pb2_grpc
from volta.v4 import api_vcluster_common_pb2

client_auth = header_adder_interceptor("admin", "volta", "root")
channel = grpc.insecure_channel('127.0.0.1:7878')
intercept = grpc.intercept_channel(channel, client_auth)


session_api = api_service_pb2_grpc.ApiSessionStub(intercept)
vrouter_api = api_device_pb2_grpc.ApiDeviceVRouterStub(intercept)

# Create the session_id value
msg = api_vcluster_common_pb2.SessionRequest()
msg.init.parameters.timeout = 600
res = session_api.Request(msg)
session_id = res.session_id

# The VRouter Id that already exists
vrouter_id = 1

# CREATE common header
vrouter_hdr = api_vcluster_common_pb2.VclusterVRouterRequestHeader()
vrouter_hdr.vrouter_id = vrouter_id
vrouter_hdr.session_id = session_id

# We have existing VRouter, with 3 LIFs
lif_id_1 = 10  # LIF (interface_id=10) Logical port 1 vlan 100
lif_id_2 = 20  # LIF (interface_id=20) Logical port 1 vlan 200
lif_id_3 = 30  # LIF (interface_id=30) Logical port 2 vlan 300
lif_id_4 = 40  # LIF (interface_id=40) Logical port 2 vlan 400

# Bundle Creation, currently, only 8 queues bundles are supported
msg = api_device_vrouter_qos_pb2.DeviceVRouterQosBundleCreateReq(
    hdr=vrouter_hdr,
    number_of_queues=8)

rpc_rsp = vrouter_api.QosBundleCreate(msg)
bundle = rpc_rsp.bundle

"""
Bundle Attributes:

- bundle.id
- bundle.queues[]. Map of queues (i.e. priorities), the key is the queue index (i.e. priority)
"""

queue0 = bundle.queue[0]  # Queue with priority 0
queue1 = bundle.queue[1]
queue2 = bundle.queue[2]
queue3 = bundle.queue[3]

"""
Queue Attributes:

- queue.id (the index in the bundle, from 0 to num_queues-1)
- queue.size. Szie of the queue in KBytes
- queue.drop_policy --> Reference to Drop policy (Default, drop_policy_id=0 )
- queue.shaper. Queue shaper parameters
- queue.output_scheduler --> Scheduler where it is connected
- queue.output_scheduler.id. Id of scheduler in VRouter
- queue.output_scheduler.weight. When scheduler is WFQ, the weight value
- queue.output_scheduler.priority. When scheduler is SP, the priority of the connection.
"""
# Queues parameters can be updated via QosServiceQueueUpdate RPC calls
# Parameter: drop_policy_id, size, shaper,
# Example modification of shaper parameters. Using .value to detect that the
# field has been set by the user.
msg = api_device_vrouter_qos_pb2.DeviceVRouterQosServiceQueueUpdateReq(
    hdr=vrouter_hdr,
    bundle_id=bundle.id,
    queue_id=0)
msg.shaper.kbps.value = 10000  # kbps
msg.shaper.burst_size.value = 200000  # kB
_ = vrouter_api.QosServiceQueueUpdate(msg)


# Example modification queue size
msg = api_device_vrouter_qos_pb2.DeviceVRouterQosServiceQueueUpdateReq(
    hdr=vrouter_hdr,
    bundle_id=bundle.id,
    queue_id=1)
msg.size.value = 10000  # kB
_ = vrouter_api.QosServiceQueueUpdate(msg)


# Classification mappings
# In this example use case, we are going to have 3 priorities defined
# And each of the priority will be mapped to EXP bits in MPLS header
# The resource will require to create a single CosMap with a set CosMappings
priority_high = 0
priority_med = 1
priority_low = 2

# For the rest of the protocol that do not match, apply following defaults:
default_priority = 7
default_color = resources_device_vrouter_qos_pb2.QOS_COLOR_GREEN

# EXP 0x01 or 0x02 priority HIGH --> mapped to colour GREEN
# EXP 0x03 priority MED --> mapped to colour YELLOW
# EXP 0x04 priority LOW --> mapped to colour RED

cos_map_classification = resources_device_vrouter_qos_pb2.QosCosMap()
cos_map_classification.classification.default_color = default_color
cos_map_classification.classification.default_priority.value = default_priority

cos_mapping_1 = cos_map_classification.classification.mpls.add()
cos_mapping_1.protocol_bits.add().mpls.exp = 0x01
cos_mapping_1.protocol_bits.add().mpls.exp = 0x02
cos_mapping_1.internal_priority = priority_high
cos_mapping_1.color = resources_device_vrouter_qos_pb2.QOS_COLOR_GREEN

cos_mapping_3 = cos_map_classification.classification.mpls.add()
cos_mapping_3.protocol_bits.add().mpls.exp = 0x03
cos_mapping_3.internal_priority = priority_med
cos_mapping_3.color = resources_device_vrouter_qos_pb2.QOS_COLOR_YELLOW

cos_mapping_4 = cos_map_classification.classification.mpls.add()
cos_mapping_4.cos_value = 0x04
cos_mapping_4.internal_priority = priority_low
cos_mapping_4.color = resources_device_vrouter_qos_pb2.QOS_COLOR_RED

# RPC method
msg = api_device_vrouter_qos_pb2.DeviceVRouterQosCosMapCreateReq(
    hdr=vrouter_hdr,
    cos_map=cos_map_classification)

rpc_rsp_map = vrouter_api.QosCosMapCreate(msg)
cos_map = rpc_rsp_map.map

"""
CosMap attributes:

- cos_map.id
- cos_map.classification_interface[]. List of LIFs with the Map applied in ingress (classification)
- cos_map.marking_interface[]. List of LIFs with the Map applied in egress (marking/remarking)

Based on its type: CLASSIFICATION or MARKING, the following structs will be filled

- cos_map.classification
- cos_map.marking

In the case of classification it has the following structure

- cos_map.classification.dscp[]. List of QosCosMappingClassification struct to classify/re/mark based on IPv4/Ipv6 DCSP/TC fields
- cos_map.classification.vlan[]. List of QosCosMappingClassification struct to classify/re/mark based on 802.1Q PCP+DEI fields
- cos_map.classification.mpls[]. List of QosCosMappingClassification struct to classify/re/mark based on MPLS EXP fields
- cos_map.default_priority. Default priority value for the values not set in the previous lists if the list contains > 1 element. Default: 7
- cos_map.default_color. Default priority value for the values not set in the previous lists if the list contains > 1 element. Default: GREEN

Each of the QosCosMappingClassification struct includes:
- priority. Internal priority value (the queue id)
- color. Internal color (GREEN, YELLOW, RED)
- protocol_bits[]. A list of the protocol values to classify the traffic

"""

# Enable the Classification in LIFs
# For simplicity, in the example, we are going to apply the same CosMap to
# all interfaces for both ingress and egress
for lif_id in [lif_id_1, lif_id_2, lif_id_3, lif_id_4]:
    # Classification
    msg = api_device_vrouter_qos_pb2.DeviceVRouterQosCosMapInterfaceAttachReq(
        hdr=vrouter_hdr,
        cos_map_id=cos_map.id,
        interface_id=lif_id)

    _ = vrouter_api.QosCosMapInterfaceAttach(msg)

"""
COSMAP REMARKING

For remarking, the pairs (color, priority) will be transformed in a specific protocol
field value.

In the case of marking, the cosmap has to fill the cos_map.marking structure (QosCosMapMarking),
with the following fields:

- cos_map.marking.dscp. QosCosMapMarkingColorProtocol with 3 colors:
  - cos_map.marking.dscp.green. List of priorities and protocol values for the green, priority pairs.
    Each of the value will have to fill the correct protocol field
  - cos_map.marking.dscp.yellow. Same with yellow color
  - cos_map.marking.dscp.red. Same with red color
- cos_map.marking.vlan. Same but with VLAN
- cos_map.marking.mpls. Same but with MPLS

- cos_map.marking.marking_defaults. Default values to use for combinations of color,priority not
  included in each of protocols lists. Only applicable if there is > 1 protocol marking match information


"""
cos_map_marking = resources_device_vrouter_qos_pb2.QosCosMap()

# Set defaults (example, all to 1)
cos_map_marking.marking.marking_defaults.vlan.pcp = 1
cos_map_marking.marking.marking_defaults.mpls.exp = 1
cos_map_marking.marking.marking_defaults.dscp.dscp = 1

# Green, high prio, remark MPLS EXP bits to 0x02
# Green, low prio, remark MPLS EXP bits to 0x03
cos_map_marking.marking.mpls.green.priority[priority_high].mpls.exp = 0x02
cos_map_marking.marking.mpls.green.priority[priority_low].mpls.exp = 0x03

# RPC method
msg = api_device_vrouter_qos_pb2.DeviceVRouterQosCosMapCreateReq(
    hdr=vrouter_hdr,
    cos_map=cos_map_marking)

rpc_rsp_map = vrouter_api.QosCosMapCreate(msg)
cos_map = rpc_rsp_map.map

for lif_id in [lif_id_1, lif_id_2, lif_id_3, lif_id_4]:
    # Marking
    msg = api_device_vrouter_qos_pb2.DeviceVRouterQosCosMapInterfaceAttachReq(
        hdr=vrouter_hdr,
        cos_map_id=cos_map.id,
        interface_id=lif_id)

    _ = vrouter_api.QosCosMapInterfaceAttach(msg)

# Schedulers creation.
# We are going to create 2 schedulers: one SP and other WFQ
# After creation, parameters can be changed like the Queue case, using the RPC
# QosSchedulerUpdate. Scheduler type can not be updated.

msg = api_device_vrouter_qos_pb2.DeviceVRouterQosSchedulerCreateReq(
    hdr=vrouter_hdr,
    scheduling_algorithm=resources_device_vrouter_qos_pb2.QOS_SCHEDULING_ALGORITHM_WEIGHTED_FAIR_QUEUE)

rpc_rsp_wfq = vrouter_api.QosSchedulerCreate(msg)
sched_wfq = rpc_rsp_wfq.scheduler


msg = api_device_vrouter_qos_pb2.DeviceVRouterQosSchedulerCreateReq(
    hdr=vrouter_hdr,
    scheduling_algorithm=resources_device_vrouter_qos_pb2.QOS_SCHEDULING_ALGORITHM_STRICT_PRIORITY)

rpc_rsp_sp = vrouter_api.QosSchedulerCreate(msg)
sched_sp = rpc_rsp_sp.scheduler

"""
Scheduler Attributes:

- scheduler.id
- scheduler.scheduling_algorithm
- scheduler.shaper. Scheduler shaper parameters

The shaper parameters can be updated using the QosSchedulerUpdate API
"""
msg = api_device_vrouter_qos_pb2.DeviceVRouterQosSchedulerUpdateReq(
    hdr=vrouter_hdr,
    scheduler_id=sched_wfq.id)

msg.shaper.kbps.value = 10000  # kbps
msg.shaper.burst_size.value = 200000  # kB

_ = vrouter_api.QosSchedulerUpdate(msg)


# List schedulers
msg = api_device_vrouter_qos_pb2.DeviceVRouterQosSchedulerListReq(hdr=vrouter_hdr)
rpc_rsp = vrouter_api.QosSchedulerList()
scheduler_list = rpc_rsp.scheduler  # This is an Array

"""
PortScheduler Attributes:

- scheduler.id
- scheduler.port_id. Index of the physical interface
- scheduler.scheduling_algorithm
- scheduler.shaper. Scheduler shaper parameters
"""

#
# Connections:
# queues 0 (weight=60%), 1 (weight=40%) --> sched_wfq
# queues 2 (priority_high) , 3 (priority_low) --> sched_sp
# sched_wfq (weight=50%) --> port_scheduler_1
# sched_sp (weight=50%) --> port_scheduler_1

# QUEUES CONNECTIONS
msg = api_device_vrouter_qos_pb2.DeviceVRouterQosConnectReq(hdr=vrouter_hdr)
msg.queue_to_scheduler.bundle_id = bundle.id
msg.queue_to_scheduler.queue_id = 0
msg.queue_to_scheduler.scheduler_id = sched_wfq.id
msg.weight = 60
_ = vrouter_api.QosConnect(msg)

msg = api_device_vrouter_qos_pb2.DeviceVRouterQosConnectReq(hdr=vrouter_hdr)
msg.queue_to_scheduler.bundle_id = bundle.id
msg.queue_to_scheduler.queue_id = 1
msg.queue_to_scheduler.scheduler_id = sched_wfq.id
msg.weight = 40
_ = vrouter_api.QosConnect(msg)

msg = api_device_vrouter_qos_pb2.DeviceVRouterQosConnectReq(hdr=vrouter_hdr)
msg.queue_to_scheduler.bundle_id = bundle.id
msg.queue_to_scheduler.queue_id = 2
msg.queue_to_scheduler.scheduler_id = sched_sp.id
msg.priority = priority_high
_ = vrouter_api.QosConnect(msg)

msg = api_device_vrouter_qos_pb2.DeviceVRouterQosConnectReq(hdr=vrouter_hdr)
msg.queue_to_scheduler.bundle_id = bundle.id
msg.queue_to_scheduler.queue_id = 3
msg.queue_to_scheduler.scheduler_id = sched_sp.id
msg.priority = priority_low
_ = vrouter_api.QosConnect(msg)

# SCHEDULERS CONNECTIONS
msg = api_device_vrouter_qos_pb2.DeviceVRouterQosConnectReq(hdr=vrouter_hdr)
msg.scheduler_to_port_scheduler.port_id = 1
msg.scheduler_to_port_scheduler.scheduler_id = sched_wfq.id
msg.weight = 60
_ = vrouter_api.QosConnect(msg)

msg = api_device_vrouter_qos_pb2.DeviceVRouterQosConnectReq(hdr=vrouter_hdr)
msg.scheduler_to_port_scheduler.port_id = 1
msg.scheduler_to_port_scheduler.scheduler_id = sched_sp.id
msg.weight = 40
_ = vrouter_api.QosConnect(msg)


# After the connections are ready, LIFs can be attached to the bundle,
# otherwise operation will fail
# In that example we attach LIF_1 to the QoSBundle
msg = api_device_vrouter_qos_pb2.DeviceVRouterQosBundleInterfaceAttachReq(
    hdr=vrouter_hdr,
    bundle_id=bundle.id,
    interface_id=lif_id_1
)

_ = vrouter_api.QosBundleInterfaceAttach(msg)
