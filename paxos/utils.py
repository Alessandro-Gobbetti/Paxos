#!/usr/bin/env python3
import sys
import socket
import struct
import json


class MsgType:
    # message types
    CLIENT_REQUEST = 0
    PHASE_1A = 1
    PHASE_1B = 2
    PHASE_2A = 3
    PHASE_2B = 4
    DECISION = 5
    CATCHUP = 6
    CATCHUP_REQ = 7


# # variables for the paxos algorithm
# c_rnd = 0       # highest-numbered round the proposes has started
# c_val = None    # value the process has picked for round c_rnd
# rnd = 0         # highest-numbered round the acceptor has participated
# v_round = 0     # highest-numbered round the acceptor has cast a vote
# v_val = None    # value voted by the acceptor in round v_round


def mcast_receiver(hostport):
    """create a multicast socket listening to the address"""
    recv_sock = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    recv_sock.bind(hostport)

    mcast_group = struct.pack(
        "4sl", socket.inet_aton(hostport[0]), socket.INADDR_ANY)
    recv_sock.setsockopt(
        socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mcast_group)
    return recv_sock


def mcast_sender():
    """create a udp socket"""
    send_sock = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    return send_sock


def parse_cfg(cfgpath):
    cfg = {}
    with open(cfgpath, "r") as cfgfile:
        for line in cfgfile:
            (role, host, port) = line.split()
            cfg[role] = (host, int(port))
    return cfg
