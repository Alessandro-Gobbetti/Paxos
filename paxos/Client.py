#!/usr/bin/env python3
import sys
import socket
import struct
import json
from utils import *


class Client:
    def __init__(self, config, id):
        print("-> client ", id)
        self.config = config
        self.id = id
        self.s = mcast_sender()

    def propose(self, value):
        print("client %d proposing %s" % (self.id, value))
        msg = json.dumps((MsgType.CLIENT_REQUEST, value))
        self.s.sendto(msg.encode(), self.config["proposers"])

    def run(self):
        for value in sys.stdin:
            value = int(value.strip())
            self.propose((value, self.id))


if __name__ == "__main__":
    cfgpath = sys.argv[1]
    config = parse_cfg(cfgpath)
    id = int(sys.argv[2])

    client = Client(config, id)
    client.run()
