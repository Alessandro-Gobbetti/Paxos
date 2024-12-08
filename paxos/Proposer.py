#!/usr/bin/env python3
import sys
import socket
import json
import time
from utils import *
import random


ACCEPTOR_COUNT = 3
QUORUM = ACCEPTOR_COUNT // 2 + 1


class Proposer:
    def __init__(self, config, id):
        print("-> proposer", id)
        self.config = config
        self.id = id
        self.r = mcast_receiver(config["proposers"])  # receive from clients
        self.s = mcast_sender()  # send to acceptors
        # print self.s port
        print("----", id,  self.s.getsockname())

        self.r.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF,
                          2**25)  # 32MB buffer

        self.MAX_PROPOSERS = 4

        self.v = None
        self.c_rnd = self.id  # unique by incrementing with MAX_PROPOSERS
        self.c_val = None

        self.values = []

        self.K = []
        self.V = []

        self.accepted_count = 0

        self.prev_decision_rnd = 0
        self.decided_values = []

        self.retry_timer = None
        self.should_retry = False
        self.retry_time = 0

    def send_phase_1a(self):
        """
        Send phase 1a message to acceptors (PHASE_1A, c_rnd)
        """
        msg = json.dumps((MsgType.PHASE_1A, self.c_rnd))
        print("P%d: sending %s" % (self.id, msg),
              "to", self.config["acceptors"])
        self.s.sendto(msg.encode(), self.config["acceptors"])
        self.start_quorum_timer(self.c_rnd, self.c_val)

    def send_phase_2a(self):
        msg = json.dumps((MsgType.PHASE_2A, self.c_rnd, self.c_val))
        self.s.sendto(msg.encode(), self.config["acceptors"])
        self.start_quorum_timer(self.c_rnd, self.c_val)

    def send_decision(self, value):
        msg = json.dumps((MsgType.DECISION, value, self.id))
        self.s.sendto(msg.encode(), self.config["learners"])
        self.s.sendto(msg.encode(), self.config["proposers"])

    def new_round(self):
        # increase c_rnd by an arbitrary unique value
        self.c_rnd += self.MAX_PROPOSERS
        self.K = []
        self.V = []
        self.accepted_count = 0

    def start_quorum_timer(self, round, val, timeout=1.0):
        timeout = 1.0 + random.random()
        self.retry_time = time.time() + timeout
        self.should_retry = (round, val)
        print("P%d starting quorum timer for round %d with value %s" %
              (self.id, round, val))

    def retry(self, round, value):
        if round == self.c_rnd and self.accepted_count < QUORUM:

            if self.c_val is not None and self.c_val == value:
                print("\033[91mP%d retrying round %d with value %s, %s\033[0m" %
                      (self.id, self.c_rnd, self.c_val, value))
                self.new_round()
                # if the value is the same, retry phase 1a
                msg = json.dumps((MsgType.PHASE_1A, self.c_rnd))
                print("P%d: sending %s" %
                      (self.id, msg), "to", self.config["acceptors"])
                self.s.sendto(msg.encode(), self.config["acceptors"])
                self.start_quorum_timer(self.c_rnd, value)
            else:
                self.should_retry = False

    def run(self):
        while True:

            if self.should_retry and time.time() >= self.retry_time:
                print("P%d retrying!!! %s" % (self.id, self.should_retry))
                self.retry(*self.should_retry)

            # listen for broadcasted requests
            msg = self.r.recv(2**16)
            msg = json.loads(msg.decode())

            match msg[0]:
                case MsgType.CLIENT_REQUEST:
                    _, value = msg

                    if self.v is None:
                        self.v = value
                        self.new_round()
                        self.send_phase_1a()
                    else:
                        if value not in self.values:
                            self.values.append(value)

                case MsgType.PHASE_1B:
                    _, rnd, v_rnd, v_val = msg
                    print("P%d PHASE_1B: %s" % (self.id, msg), flush=True)
                    if rnd == self.c_rnd:
                        self.K.append(v_rnd)
                        self.V.append((v_rnd, v_val))

                        if len(self.K) == QUORUM:
                            max_k = max(self.K)
                            print("P%d max_k %d" % (self.id, max_k))
                            print("P%d K %s" % (self.id, self.K))
                            print("P%d V %s" % (self.id, self.V))
                            if max_k == 0 or max_k == self.prev_decision_rnd or v_val is None:
                                self.c_val = self.v
                            else:
                                # find the value corresponding to the highest k
                                self.c_val = self.V[self.K.index(max_k)][1]
                            print("P%d -> c_val %s" % (self.id, self.c_val))
                            self.send_phase_2a()

                case MsgType.PHASE_2B:
                    _, v_rnd, v_val = msg

                    if v_rnd == self.c_rnd and v_val not in self.decided_values:
                        self.accepted_count += 1

                        if self.accepted_count == QUORUM:
                            # decide
                            print("\033[92m[√] P%d Decided on value: %s\033[0m" %
                                  (self.id, v_val))
                            self.send_decision(v_val)
                            self.prev_decision_rnd = self.c_rnd

                            if self.values:
                                # start a new round with the next value
                                self.v = self.values.pop(0)
                                print("P%d starting new round with value %s" %
                                      (self.id, self.v))
                                self.new_round()
                                # skip to phase 2a
                                self.c_val = self.v
                                self.send_phase_2a()
                            else:
                                self.v = None

                case MsgType.DECISION:
                    _, value, prop_id = msg

                    self.decided_values.append(value)

                    if True or prop_id != self.id:
                        print("P%d received decision (%s) from P%d" %
                              (self.id, value, prop_id))

                        # another proposer has decided on a value, so we can remove it from our values
                        print("P%d values %s" %
                              (self.id, [value, self.v, value == self.v]))
                        if value in self.values:
                            self.values.remove(value)
                            print("P%d removed value %s" % (self.id, value))
                        if value == self.v:
                            self.v = None
                            self.c_val = None
                            self.new_round()
                            if self.retry_timer is not None:
                                print("P%d cancelling retry timer" % self.id)
                                self.should_retry = False
                            if self.values:
                                self.v = self.values.pop(0)
                                print("P%d starting new round with value %s" %
                                      (self.id, self.v))
                                self.send_phase_1a()
                            print("P%d value %s" % (self.id, self.v))
                case _:
                    print("-------Proposer ignoring message:", msg)


if __name__ == "__main__":
    cfgpath = sys.argv[1]
    config = parse_cfg(cfgpath)
    id = int(sys.argv[2])

    p = Proposer(config, id)
    p.run()
