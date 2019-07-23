import sys
from socket import *
from struct import *

# return a little-endian ordered byte array
def to_bytearray(i):
    return (i).to_bytes(4, byteorder="little", signed=False)

def init_adjacent(r):
    for link, cost in r:
        for l, c in neighbours:
            # if adjacent
            if link == l and cost == c:
                return cost
    return float("inf")

# return nodes that are adjacent to w and not in N
def adjacent(w, N):
    links = []
    adj = []
    for link, cost in LSDB[w-1]:
        links.append(link)
    #print(links)
    for r in range(5):
        if r+1 == w or r+1 in N:
            continue
        for link, cost in LSDB[r]:
            #print("link: " + str(link) + " cost: " + str(cost))
            if link in links:
                adj.append((r+1, cost))
    #print(adj)
    return adj

# print Topology Database
def print_topology(t):
    print("# Topology database")
    for r in range(5):
        nbr_link = len(t[r])
        if nbr_link != 0:
            print("R" + str(router_id) + " -> R" + str(r+1) + " nbr link " + str(nbr_link))
            for link, cost in t[r]:
                print("R" + str(router_id) + " -> R" + str(r+1) + " link " + str(link) + " cost " + str(cost))
    print()

# print Routing Information Base
def print_RIB(dist, prev):
    print("# RIB")
    for i in range(5):
        next_hop = "Local"
        if dist[i] == float("inf"):
            next_hop = "inf"
        elif i+1 != router_id:
            p = i
            while prev[p] != router_id:
                p = prev[p]-1
            next_hop = "R" + str(p+1)
        print("R" + str(router_id) + " -> R" + str(i+1) + " -> " + next_hop + ", " + str(dist[i]))
    print()

# Error check command line arguments
if len(sys.argv) != 5:
    print("Incorrect number of arguments")
    sys.exit()

# get required variables from command line arguments 
router_id = int(sys.argv[1])
nse_host = sys.argv[2]
nse_port = int(sys.argv[3])
router_port = int(sys.argv[4])

# Send INIT packet to nse
pkt_INIT = to_bytearray(router_id)
socket = socket(AF_INET, SOCK_DGRAM)
socket.bind(("", router_port))
socket.sendto(pkt_INIT, (nse_host, nse_port))
print("R" + str(router_id) + " sends an INIT: router_id " + str(router_id))

# Receive circuit database from nse
message, server = socket.recvfrom(1024)
circuit_DB = unpack("<IIIIIIIIIII", message)
nbr_link = circuit_DB[0]
print("R" + str(router_id) + " receives a CIRCUIT_DB: nbr_link " + str(nbr_link))
neighbours = []
# Link State Database (router, link id, cost)
LSDB = [[], [], [], [], []]
for i in range(1, 2*nbr_link+1, 2):
    link = circuit_DB[i]
    cost = circuit_DB[i+1]
    neighbours.append((link, cost))
    LSDB[router_id-1].append((link, cost))

# Send HELLO PDU to each of its neighbours
for link, cost in neighbours:
    pkt_HELLO = pkt_INIT + to_bytearray(link)
    socket.sendto(pkt_HELLO, (nse_host, nse_port))
    print("R" + str(router_id) + " sends a HELLO: router_id " + str(router_id) + " link_id " + str(link))

while True:
    message, server = socket.recvfrom(1024)
    if len(message) == 8: # Receiving HELLO packet from neighbour
        pkt_HELLO = unpack("<II", message)
        sender_id = pkt_HELLO[0]
        via = pkt_HELLO[1]
        print("R" + str(router_id) + " receives a HELLO: router_id " + str(sender_id) + " link_id " + str(via))
        # Send a set of LSPDU packets to that neighbour
        for link, cost in neighbours:
            pkt_LSPDU = pkt_INIT + pkt_INIT + to_bytearray(link) + to_bytearray(cost) + to_bytearray(via)
            socket.sendto(pkt_LSPDU, (nse_host, nse_port))
            print("R" + str(router_id) + " sends an LS PDU: sender " + str(router_id) + " router_id " + str(router_id) + " link_id " + str(link) + " cost " + str(cost) + " via " + str(via))
    elif len(message) == 20: # Receiving LSPDU pakcet from neighbour
        pkt_LSPDU = unpack("<IIIII", message)
        sender = pkt_LSPDU[0]
        r_id = pkt_LSPDU[1]
        link_id = pkt_LSPDU[2]
        cost = pkt_LSPDU[3]
        via = pkt_LSPDU[4]
        print("R" + str(router_id) + " receives an LS PDU: sender " + str(sender) + " router_id " + str(r_id) + " link_id " + str(link_id) + " cost " + str(cost) + " via " + str(via))
        # Add LSPDU information to LSDB
        unique = True
        for r in range(5):
            for l, c in LSDB[r]:
                if r+1 == r_id and l == link_id and c == cost:
                    unique = False
                    break
        if unique:
            LSDB[r_id-1].append((link_id, cost))
            # Print Topology
            print_topology(LSDB)
            # Forward to rest of neighbours
            for l, c in neighbours:
                if l != via:
                    pkt_LSPDU = pkt_INIT + to_bytearray(r_id) + to_bytearray(link_id) + to_bytearray(cost) + to_bytearray(l)
                    socket.sendto(pkt_LSPDU, (nse_host, nse_port))
                    print("R" + str(router_id) + " sends an LS PDU: sender " + str(router_id) + " router_id " + str(r_id) + " link_id " + str(link_id) + " cost " + str(cost) + " via " + str(l))
            # Run Dijsktra's algorithm on LSDB
            N = [router_id]
            # Routing Information Base
            D = [None] * 5 # Minimum Distance
            P = [None] * 5 # Previous Router
            for r in range(5):
                if r+1 == router_id:
                    D[r] = 0
                else:
                    D[r] = init_adjacent(LSDB[r])
                    P[r] = router_id
            while len(N) < 5:
                # find w not in N such that D(w) is a minimum
                w = -1
                min_dist = float("inf")
                for router in range(5):
                    if router+1 not in N and D[router] <= min_dist:
                        w = router+1
                        min_dist = D[router]
                N.append(w)
                for v, c in adjacent(w, N):
                    alt = D[w-1] + c
                    if alt < D[v-1]:
                        D[v-1] = alt
                        P[v-1] = w
            print_RIB(D, P)
