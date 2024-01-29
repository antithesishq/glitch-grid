## Motivation

Glitch Grid is a toy distributed system for demonstrating how to
interface your system with the [Antithesis Platform](https://antithesis.com/). This project demonstrates:

* Use of an SDK for [assertion definition](https://antithesis.com/docs/using_antithesis/properties.html)
   and control flow.
* Build and, for Go, [source instrumentation](https://antithesis.com/docs/instrumentation/go_instrumentation.html)
* Triggering tests and displaying results via [CI Integrations](https://antithesis.com/docs/using_antithesis/ci.html)

Why demonstrate on a toy project? In order to have interesting test results, we wanted
to have a software system that contains bugs! Welcome, GlitchGrid.

Please refer to the [Antithesis Docs](https://antithesis.com/docs/) for more information about
how to get started with Antithesis, best practrices, etc.

### SDK Use

This project includes [a variety of assertions](https://github.com/search?q=repo%3Aantithesishq%2Fglitch-grid+%28Always+OR+Sometimes%29&type=code)
meant to demonstrate how to configure Antitehsis to look for violations of test properties
about your software that you consider important. Test results include summaries and debugging
information about each violation, if found.

When software starts up in the Antithesis platform, there is usually setup work during which
injecting faults is not productive. Because of this, Antithesis waits to start injecting
faults until the software under test indicates that it is booted and ready. The SDK
[lifecycle functions](https://antithesis.com/docs/using_antithesis/sdk/overview.html#)
[are used](https://github.com/search?q=repo%3Aantithesishq%2Fglitch-grid+SetupComplete&type=code)
to coordinate with the simulation.

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

### Go

The Go implementation can be found in the `go/` subdirectory. It requires Go version 1.19 or higher.
