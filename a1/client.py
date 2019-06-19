import sys
from socket import *

# error check command line arguments
if len(sys.argv) != 5:
    print("Incorrect number of arguments")
    sys.exit()
try:
    temp = str(sys.argv[1])
    temp = int(sys.argv[2])
    temp = int(sys.argv[3])
    temp = str(sys.argv[4])
except:
    print("Incorrect format of arguments")
    sys.exit()


# get required variables from command line arguments 
server_address = sys.argv[1]
n_port = int(sys.argv[2])
req_code = sys.argv[3]
message = sys.argv[4]

# create TCP socket for server, with n_port
client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect((server_address, n_port))

# send req_code to server
client_socket.send(req_code.encode())

# get r_port from server
r_port = int(client_socket.recv(1024).decode())
client_socket.close()

# create UDP socket for server
client_udp_socket = socket(AF_INET, SOCK_DGRAM)

# attach server name and port to message, send into socket
client_udp_socket.sendto(message.encode(), (server_address, r_port))

# get modified message and print
modified_message, server_address = client_udp_socket.recvfrom(1024)
print(modified_message.decode())

client_udp_socket.close()
