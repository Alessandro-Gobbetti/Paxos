#!/usr/bin/env python3
import sys
import socket
import struct
import json
import time

from utils import *


class Learner():
    def __init__(self, config, id):
        print("-> learner", id, file=sys.stderr, flush=True)
        self.config = config
        self.id = id
        self.r = mcast_receiver(self.config["learners"])
        self.s = mcast_sender()

        self.decided_values = []
        self.is_catching_up = False

    def catchup(self):
        print("learner %s catching up" % self.id, file=sys.stderr, flush=True)
        msg = json.dumps((MsgType.CATCHUP_REQ, self.id))
        self.s.sendto(msg.encode(), self.config["learners"])

    def run(self):
        catchup_time = time.time() + 2
        self.is_catching_up = True
        self.catchup()

        while True:
            if self.is_catching_up and time.time() > catchup_time:
                # no catchup response received, no one is alive. catchup is not needed
                self.is_catching_up = False
                for value in self.decided_values:
                    print(value[0], flush=True)

            msg = self.r.recv(2**16)
            # print("learner: received %s from %s" %
            #       (msg, sender), file=sys.stderr, flush=True)
            msg = json.loads(msg.decode())
            match msg[0]:
                case MsgType.DECISION:
                    _, value, prop_id = msg
                    self.decided_values.append(value)
                    if not self.is_catching_up:
                        print(value[0], flush=True)
                    # case MsgType.CATCHU_REQ:
                    #     if not self.is_catching_up:
                    #         msg = json.dumps((MsgType.CATCHUP, self.decided_values))
                case MsgType.CATCHUP_REQ:
                    if not self.is_catching_up:
                        _, sender = msg
                        if sender != self.id:
                            msg = json.dumps(
                                (MsgType.CATCHUP, self.decided_values))
                            self.s.sendto(
                                msg.encode(), self.config["learners"])
                            print("\033[94mlearner %s sending catchup to %s: %s\033[0m" %
                                  (self.id, sender, self.decided_values), file=sys.stderr, flush=True)
                case MsgType.CATCHUP:
                    print("learner %s catching up" %
                          self.id, file=sys.stderr, flush=True)
                    if self.is_catching_up:
                        _, values = msg

                        self.is_catching_up = False
                        # concatenate decided values
                        self.decided_values = values + self.decided_values
                        for value in self.decided_values:
                            print(value[0], flush=True)
                        print("\033[94mlearner %s caught up: %s\033[0m" % (self.id, self.decided_values),
                              file=sys.stderr, flush=True)
                case _:
                    print("learner %s ignoring message: %s" %
                          (self.id, msg), file=sys.stderr, flush=True)


if __name__ == "__main__":
    cfgpath = sys.argv[1]
    config = parse_cfg(cfgpath)
    id = int(sys.argv[2])

    l = Learner(config, id)
    l.run()
