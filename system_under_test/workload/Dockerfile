# Start from a thin linux distribution.
FROM docker.io/library/alpine:latest
LABEL maintainer="Antithesis <support@antithesis.com>"

# Make sure to update the current packages, then grab the two programs
# we'll need to have in order for the workload driver to run.
RUN apk update
RUN apk upgrade
RUN apk add bash curl

# Add source code
ADD workload.sh .

# Define the entrypoint.
# Make sure to use the array version of this specification, so other command-line
# arguments and parameters can be specified in the Dockerfile.
ENTRYPOINT [ "/bin/bash", "./workload.sh" ]