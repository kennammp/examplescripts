#!/usr/bin/env python3
import getopt
import sys

# -----––-----------------------------------------––----------------------------
# grpc_imports.begin
# Utils included in python protobuf bindings to setup RBAC and TLS
from volta.v4.utils.client_channel_creator import create_channel

# RPCs and protobuf files
from volta.v4 import api_device_pb2_grpc
from volta.v4 import api_device_vrouter_pb2
from volta.v4 import api_device_vrouter_interface_pb2

# Session utils
from volta.v4 import api_service_pb2_grpc
from volta.v4 import api_vcluster_common_pb2
# grpc_imports.end
# -----––-----------------------------------------––----------------------------

# -----––-----------------------------------------––----------------------------
# grpc_setup.begin
# For a multinode deployment use the IP address of the Coordinator node
# Values utilized in the create_channel() method
# these include grpc client RBAC and TLS setup
grpc_endpoint = '127.0.0.1:7878'
tls = False
tls_mutual = False

# Default values for TLS certificates
# only used if TLS and client authentication is enabled on the server side
tls_client_cert = "/etc/volta/certs/client.pem"
tls_client_key = "/etc/volta/certs/client.key"
# CA file required when TLS is enabled in order to authenticate the server
tls_ca_file = "/etc/ssl/certs/ca.crt"

# For lab testing purposes you can override the CN integrity check
ssl_name_server_override = "volta-node"

# RBAC credentials
username = "admin"
password = "volta"
domain = "root"
# grpc_setup.end
# -----––-----------------------------------------––----------------------------

# -----––-----------------------------------------––----------------------------
# device_setup.begin
# Define the device where the vRouter will be presented
device_id = 5432369721234
# device_setup.end
device_id = 1
# -----––-----------------------------------------––----------------------------

# Get input arguments to launch the script
try:
    opts, args = getopt.getopt(sys.argv[1:], "h",
                               ["help",
                                "tls",
                                "tls-mutual",
                                "endpoint=",
                                "device=",
                                "ssl-name-server-override="])
except getopt.GetoptError as err:
    print(err)
    sys.exit(2)

for o, a in opts:
    if o == "--endpoint":
        grpc_endpoint = a
    elif o in ("-h", "--help"):
        print("Usage: {} --endpoint=127.0.0.1:7878 --device=1 [--tls] [--tls-mutual] "
              "[--ssl_name_server_override=volta-node]".format(__file__))
        sys.exit()
    elif o == "--device":
        device_id = int(a)
    elif o == '--tls':
        tls = True
    elif o == '--tls-mutual':
        tls_mutual = True
    elif o == '--ssl_name_server_override':
        ssl_name_server_override = str(a)

# INIT
# - Setup gRPC channel
# - Setup client gRPC API stubs
# - Open session
# -----––-----------------------------------------––----------------------------
# grpc_channel_stubs.begin
# Create the object that your client stub will invoke to bring up the connection
grpc_channel = create_channel(grpc_endpoint, username, password, domain,
                              tls=tls, tls_mutual_auth=tls_mutual,
                              grpc_ssl_target_name_override=ssl_name_server_override)
# grpc_channel_stubs.end
# -----––-----------------------------------------––----------------------------

# -----––-----------------------------------------––----------------------------
# create_session_id.begin
# Create the client stub that will be used to bring up the session:
session_api = api_service_pb2_grpc.ApiSessionStub(grpc_channel)

# create the message that will begin the session with the server:
msg = api_vcluster_common_pb2.SessionRequest()
msg.init.parameters.timeout = 600

# make the call to start the session and create the session ID:
response = session_api.Request(msg)
session_id = response.session_id
# create_session_id.end
# -----––-----------------------------------------––----------------------------

# -----––-----------------------------------------––----------------------------
# stubs_api.begin
# Create the client stub that will be used to send the function call:
vrouter_api = api_device_pb2_grpc.ApiDeviceVRouterStub(grpc_channel)
# stubs_api.end
# -----––-----------------------------------------––----------------------------

# VROUTER SETUP
# - Create VRouter

# -----––-----------------------------------------––----------------------------
# vrouter_create.begin

# Create the message for the function call. 
msg = api_device_vrouter_pb2.DeviceVRouterCreateReq()
msg.hdr.session_id = session_id
msg.name = "vrouter_example"
msg.device_id = device_id

# make the call to create the vrouter, and display the new vRouter's details:
response = vrouter_api.Create(msg)
vrouter_id = response.vrouter.id
print(response)
# vrouter_create.end
# -----––-----------------------------------------––----------------------------

# -----––-----------------------------------------––----------------------------
# show_vrouter_json.begin
from google.protobuf.json_format import MessageToJson
print(MessageToJson(response.vrouter, preserving_proto_field_name=True))
# {
#   "id": 2,
#   "name": "vrouter_example",
#   "vrfs": [
#     0
#   ],
#   "default_vrf": {
#     "vrouter_id": 2,
#     "protocols": {
#       "static": [
#         0
#       ]
#     },
#     "interfaces": [
#       1
#     ],
#     "settings": {
#       "ipv4": true,
#       "ipv6": true,
#       "mpls": true
#     },
#     "name": "default",
#     "loopback_interface_id": 1
#   },
#   "settings": {
#     "ipv4": true,
#     "ipv6": true,
#     "mpls": true
#   },
#   "interfaces": [
#     1
#   ],
#   "device_id": "1"
# }
# show_vrouter_json.end
# -----––-----------------------------------------––----------------------------

# CLEANUP
# - Destroy VRouter
# - Close session

# -----––-----------------------------------------––----------------------------
# vrouter_destroy.begin
msg = api_device_vrouter_pb2.DeviceVRouterDestroyReq()
msg.hdr.session_id = session_id
msg.hdr.vrouter_id = vrouter_id

response = vrouter_api.Destroy(msg)
# vrouter_destroy.end
# -----––-----------------------------------------––----------------------------

# -----––-----------------------------------------––----------------------------
# session_close.begin
# Create the message for the function call
msg = api_vcluster_common_pb2.SessionRequest()
msg.close.session_id = session_id

# make the call to close the session
response = session_api.Request(msg)
# session_close.end
# -----––-----------------------------------------––----------------------------
