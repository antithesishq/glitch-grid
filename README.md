## Glitch Grid

This is a toy distributed system which we will use to demonstrate how to
transform your system to run within [Antithesis](https://antithesis.com/). We have the same
basic system implemented in Go and Python, as well as a language-agnostic
workload which can be used to test the system.

### Architecture

The overall system is a distributed system which will remember the most recent positive
integer sent to it by a client. Clients talk to a mostly-stateless **control** server,
which in turn will write to and read from one or more **vault** servers. Operations
are only successful if *more than 50%* of vaults report success. The number stored in
the system *should* only increase in value; vaults will log an error if the number
decreases, but will not block the update. Both the control server and all vaults are
multi-threaded.

There are two types of error states a client might see from the system:
* on both reads and writes, the system may report it is in an *inconsistent* state if
  it cannot get a successful response from a majority of the vaults;
* on reads, a client might find the system in an *incorrect* state if the value the
  system returns does not match the most recent value written by the client.

The control server can detect if the system is in an *inconsistent* state, but only the
client can detect if the system is in an *incorrect* state.

The language-agnostic workload will attempt to write increasingly-large numbers to the
system, and occasionally pause to confirm that the value it reads from the system
matches the most recent value it wrote to the system. At the end of the test, it will
pause for a few seconds before performing one final read to confirm that the system
completed in a correct and consistent state.

### Workload

The test workload is written in bash and uses `curl` to perform reads and writes. The workload
can be configured using environment variables, controlling everything from startup times to the
number of values written to the system during the test to (approximately) how often it will stop
writing values and check if the system is in the correct state.

### Python

The Python implementation can be found in the `py/` subdirectory. It requires Python version 3.11 or higher.

### Go

The Go implementation can be found in the `go/` subdirectory. It requires Go version 1.20 or higher.
