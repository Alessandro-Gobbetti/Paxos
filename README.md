# Paxos

This project implements the Paxos consensus algorithm with the goal of reaching atomic
broadcast. The implementation includes roles for Proposers, Acceptors, Learners, and Clients. This README provides instructions on how to set up, run, and test the implementation.

## Roles

### Proposer

The Proposer initiates the consensus process by proposing values to the Acceptors. It goes through two phases:

Phase 1a: The Proposer sends a prepare request to the Acceptors.
Phase 2a: If a quorum of Acceptors responds, the Proposer sends an accept request with the proposed value.

If the proposer already has a quorum of acceptors when deciding a value, it can skip phase 1 and go directly to phase 2.

### Acceptor

The Acceptor responds to the Proposer's requests and helps achieve consensus:

Phase 1b: The Acceptor responds to the prepare request.
Phase 2b: The Acceptor responds to the accept request.

### Learner

The Learner learns the final value once consensus is reached. It listens for decisions from the Proposers and updates its state accordingly.
Learners can join the system at any time and catch up on the decisions they missed.

### Client

The Client sends values to the Proposers to be proposed for consensus. It reads values from standard input and sends them to the Proposers.

### Running the Roles

The implementation can be found in the `paxos` directory.
Each role has a corresponding script to run it:

Proposer: proposer.sh <id> <config>`
Acceptor: acceptor.sh <id> <config>`
Learner: learner.sh <id> <config>`
Client: client.sh <id> <config>

The `id` is the unique identifier for the role, and the `config` is the path to the configuration file.

## Configuration

The configuration file paxos.conf specifies the multicast addresses and ports for each role:

```
clients 239.0.0.1 5000
proposers 239.0.0.1 6000
acceptors 239.0.0.1 7000
learners 239.0.0.1 8000
```

## Running the Tests

The tests can be found in the root directory. To run the tests, execute the following command:

- `./run.sh <path-to-paxos-directory> <number-of-values>`
- `./run_catch_up.sh <path-to-paxos-directory> <number-of-values>`
- `./run_loss.sh <path-to-paxos-directory> <number-of-values>`

The result of the test can then be checked by running the following commands:

- `./check1.sh`
- `./check2.sh`
- `./check3.sh`
- `./check_all.sh` to run all checks
