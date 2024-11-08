## Motivation

Glitch Grid is a toy distributed system for demonstrating how to
integrate with the [Antithesis Platform](https://antithesis.com/). This project demonstrates:

* Use of [the Antithesis SDK]((https://antithesis.com/docs/using_antithesis/sdk/overview.html#))
   to [define properties](https://antithesis.com/docs/using_antithesis/properties/)
* Instrumenting a Go project for [coverage information](https://antithesis.com/docs/instrumentation/overview.html)
* Triggering tests and receiving results using [Github Actions](https://antithesis.com/docs/using_antithesis/ci.html)

Why demonstrate with a toy project? Most software has bugs, but for demonstration purposes 
we wanted obvious, low-context bugs that project maintainers would not fix. Welcome, GlitchGrid!

Please refer to the [Antithesis Documentation](https://antithesis.com/docs/) for more information about
how to get started with Antithesis, best practices, etc.

### SDK Use

This project demonstrates how to [use the Antithesis SDK](https://github.com/search?q=repo%3Aantithesishq%2Fglitch-grid+%28Always+OR+Sometimes%29&type=code) to add assertions about your software.
This includes conventional assertions, and also [Sometimes Assertions](https://antithesis.com/docs/best_practices/sometimes_assertions.html) which can help you
assess the quality of your testing or check for unreachable code. 

When software starts up in the Antithesis platform, there is usually setup work during which
injecting faults is not productive. Because of this, Antithesis waits to start injecting
faults until the software under test indicates that it is booted and ready. The SDK
[lifecycle functions](https://antithesis.com/docs/using_antithesis/sdk/overview.html#)
[are used](https://github.com/search?q=repo%3Aantithesishq%2Fglitch-grid+SetupComplete&type=code)
to coordinate with the simulation.

### Architecture

This is a distributed system which will remember the most recent positive
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

The Go implementation can be found in the `go/` subdirectory. It requires Go version 1.20 or higher.
