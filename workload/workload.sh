#!/usr/bin/env bash

# How long to wait for everything to come up before starting the test?
START_DELAY=${START_DELAY:-10}
# How logn to wait after the final write to check if the system gets into a consistent state?
FINAL_DELAY=${FINAL_DELAY:-5}
# How many steps (i.e., numbers) should we try and write to the system during this test?
NUM_STEPS=${NUM_STEPS:-100}
# What is the maximum amount the counter should jump up each step?
MAX_STEP_SIZE=${MAX_STEP_SIZE:-5}
# Check the consistency of the system when the counter is a multiple of what number?
CHECK_WHEN_MULTIPLE_OF=${CHECK_WHEN_MULTIPLE_OF:-5}

CONTROL_SERVER=$1
if [[ -z "${CONTROL_SERVER}" ]]
then
    echo "Usage: $0 <control_server>"
    exit 1
fi

# Wait a bit for the other services to come up
echo -n "Waiting ${START_DELAY} seconds for the storage system to become available ... "
sleep ${START_DELAY}
echo "done."

# Emit a message we can look for to see that the test is starting.
# This is useful for us to know when we've pivoted from setup to actual test so we don't
# fuzz/test the setup phase.
echo {\"antithesis_setup\": {\"status\": \"complete\"}} > "$ANTITHESIS_OUTPUT_DIR/sdk.json"
echo "=== START TEST ==="

# Go through and store numbers in our system. When our current number is a multiple of a certain value,
# do a read to check that the storage system is consistent and fully caught-up.
n=0
for c in $(seq 1 ${NUM_STEPS} )
do
    n=$(( $n + ($RANDOM % $MAX_STEP_SIZE) + 1 ))
    outfile="/tmp/${n}.out"
    http_code=$(curl -s -o "${outfile}" -w "%{http_code}" -X POST "http://${CONTROL_SERVER}" -d "${n}")
    echo "HttpStatus=${http_code} Message=$(cat "${outfile}" 2> /dev/null)"
    rm -f "${outfile}"
    if [[ $(( $n % $CHECK_WHEN_MULTIPLE_OF )) -eq 0 ]]
    then
        outfile="/tmp/${n}.out"
        http_code=$(curl -s -o "${outfile}" -w "%{http_code}" "http://${CONTROL_SERVER}")
        actual=$(cat "${outfile}" 2> /dev/null)
        actual=${actual//[!0-9]/}
        echo "HttpStatus=${http_code} Expected=${n} Actual=${actual}"
        if [[ "${http_code}" != "200" ]]
        then
            echo "ERROR: Storage vaults are in an inconsistent state!"
        elif [[ "${n}" != "${actual}" ]]
        then
            echo "ERROR: Storage vaults returned unexpected value!"
        fi
        rm -f "${outfile}"
        sleep 1
    fi
done

# Now give the system a few seconds to settle, and do one final check for consistency.
echo -n "Waiting ${FINAL_DELAY} seconds for any straggling writes ... "
sleep ${FINAL_DELAY}
echo "done."
outfile="/tmp/${n}.out"
http_code=$(curl -s -o "${outfile}" -w "%{http_code}" "http://${CONTROL_SERVER}")
actual=$(cat "${outfile}" 2> /dev/null)
actual=${actual//[!0-9]/}
echo "HttpStatus=${http_code} Expected=${n} Actual=${actual}"
if [[ "${http_code}" != "200" ]]
then
    echo "ERROR: Storage vaults finished in an inconsistent state!"
elif [[ "${n}" != "${actual}" ]]
then
    echo "ERROR: Storage vaults finished with unexpected value!"
else
    echo "Test completed with storage in a consistent and correct state."
fi
rm -f "${outfile}"

# Tag the end of the test.
echo "==== END TEST ===="
