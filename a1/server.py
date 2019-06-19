import sys
from socket import *

# get req_code from command line argument
req_code = sys.argv[1]

# create TCP welcoming socket
tcp_socket = socket(AF_INET, SOCK_STREAM)
# bind to random port
tcp_socket.bind(('', 0))
address, n_port = tcp_socket.getsockname()

print("SERVER_PORT=" + str(n_port))

tcp_socket.listen(1)

while True:
    # waits for incoming requests
    connection_socket, addr = tcp_socket.accept()

    # read bytes from socket
    code = connection_socket.recv(1024).decode()

    # close TCP connection if req_code doesn't match
    if code != req_code:
        print("req_code does not match, exiting...")
        connection_socket.close()
        sys.exit()

    # create UDP socket and bind to random port
    udp_socket = socket(AF_INET, SOCK_DGRAM)
    udp_socket.bind(('', 0))
    address, r_port = udp_socket.getsockname()

    # send r_port to client
    connection_socket.send(str(r_port).encode())
    connection_socket.close()

    message, client_address = udp_socket.recvfrom(1024)
    # reverse the message
    modified_message = message.decode()[::-1]
    
    # send encoded message back to client
    udp_socket.sendto(modified_message.encode(), client_address)
