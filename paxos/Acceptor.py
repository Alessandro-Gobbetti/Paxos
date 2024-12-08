#!/usr/bin/env python3
import sys
import json
from utils import *


class Acceptor:
    def __init__(self, config, id):
        print("-> acceptor", id)
        self.config = config
        self.id = id
        self.r = mcast_receiver(config["acceptors"])
        self.s = mcast_sender()

        self.rnd = 0
        self.v_rnd = 0
        self.v_val = None

    def send_phase_1b(self):
        msg = json.dumps((MsgType.PHASE_1B, self.rnd, self.v_rnd, self.v_val))
        self.s.sendto(msg.encode(), self.config["proposers"])

    def send_phase_2b(self):
        msg = json.dumps((MsgType.PHASE_2B, self.v_rnd, self.v_val))
        self.s.sendto(msg.encode(), self.config["proposers"])

    def run(self):

        while True:
            msg = self.r.recv(2**16)
            msg = json.loads(msg.decode())
            match msg[0]:
                case MsgType.PHASE_1A:
                    _, c_rnd = msg
                    if c_rnd > self.rnd:
                        print("   A%d PHASE_1A: %d %d %s" %
                              (self.id, c_rnd, self.rnd, c_rnd > self.rnd))
                        self.rnd = c_rnd
                        self.send_phase_1b()

                case MsgType.PHASE_2A:
                    print("\tA%d PHASE_2A: %s" % (self.id, msg))
                    _, c_rnd, c_val = msg
                    if c_rnd >= self.rnd:
                        self.v_rnd = c_rnd
                        self.v_val = c_val
                        self.send_phase_2b()
                case _:
                    print("Acceptor ignoring message:", msg)


if __name__ == "__main__":
    cfgpath = sys.argv[1]
    config = parse_cfg(cfgpath)
    id = int(sys.argv[2])

    acceptor = Acceptor(config, id)
    acceptor.run()
