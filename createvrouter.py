# Utils included in python protobuf bindings to setup RBAC and TLS
from volta.v1.utils.client_channel_creator import create_channel

# RPCs and protobuf files
from volta.v1 import api_device_pb2_grpc
from volta.v1 import api_device_vrouter_pb2

# Session utils
from volta.v1 import api_service_pb2_grpc
from volta.v1 import api_vcluster_common_pb2

# Values utilized in the create_channel() method
# these include grpc client RBAC and TLS setup
grpc_endpoint = '192.168.253.2:7878'
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

# Create the object that your client stub will invoke to bring up the connection
grpc_channel = create_channel(grpc_endpoint, username, password, domain,
                              tls=tls, tls_mutual_auth=tls_mutual,
                              grpc_ssl_target_name_override=ssl_name_server_override)

# Create the client stub that will be used to bring up the session:
session_api = api_service_pb2_grpc.ApiSessionStub(grpc_channel)

# create the message that will begin the session with the server:
msg = api_vcluster_common_pb2.SessionRequest()
msg.init.parameters.timeout = 600

# make the call to start the session and create the session ID:
response = session_api.Request(msg)
session_id = response.session_id

# Create the client stub that will be used to send the function call:
vrouter_api = api_device_pb2_grpc.ApiDeviceVRouterStub(grpc_channel)

# Define the device where the vRouter will be presented
device_id = 1

# Create the message for the function call. This message defines the new vRouter's name and device_ID:
msg = api_device_vrouter_pb2.DeviceVRouterCreateReq()
msg.hdr.session_id = session_id
msg.name = "vrouter_example"
msg.device_id = device_id

# make the call to create the vrouter:
response = vrouter_api.Create(msg)
vrouter_id = response.vrouter.id

# Create the message for the function call
msg = api_vcluster_common_pb2.SessionRequest()
msg.close.session_id = session_id

# make the call to close the session
response = session_api.Request(msg)
