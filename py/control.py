#!/usr/bin/env python

import argparse
import common
import logging
import math
import sys

from collections import defaultdict
from threading import Thread
from time import time
from urllib.request import urlopen


class ControlHandler(common.BaseHandler):
    def do_GET(self):
        """ Get the current value of the counter.

        Poll all our backend servers and see if we have majority consensus.
        Sends a 200 and the value to the client if we have a consensus, 500 otherwise.
        """
        if not self.validate_or_reject_path():
            return
        value = self.server.get_value_from_vaults()
        status_code = 200 if value >= 0 else 500
        body = f'{value}'.encode('utf-8')
        self.send_status_and_response(status_code, 'text/plain', body)

    def do_POST(self):
        """ Update the value in storage to what is provided in the body.
        """
        if not self.validate_or_reject_path():
            return
        post_body_bytes = self.get_post_body_bytes()
        if not post_body_bytes:
            self.send_status_and_response(400, 'text/plain', 'Invalid or missing POST body')
            return
        [status_code, update_bytes] = self.server.send_value_to_vaults(post_body_bytes)
        self.send_status_and_response(status_code, 'text/plain', update_bytes)


class VaultUpdater(Thread):
    """ Vault thread to send an updated value to a single storage vault.

    We subclass from the Thread object so we can pass back the response (if any) we get from the vault.
    """
    def __init__(self, vault, value, timeout_sec=1):
        Thread.__init__(self)
        self.vault = vault
        self.value = value.encode('utf-8') if isinstance(value, str) else value
        self.timeout_sec = timeout_sec
        self._response = None

    def run(self):
        logging.debug(f'Setting vault {self.vault} value {self.value}')
        try:
            with urlopen(f'http://{self.vault}/', self.value, timeout=self.timeout_sec) as f:
                response = f.read()
                if response is not None and response:
                    self._response = int(response.decode('utf-8'))
        except Exception as error:
            logging.warning(f'Error setting vault {self.vault} value to {self.value}: {error}')

    def response(self):
        return self._response


class ControlServer(common.BaseServer):
    """ Control server which manages all our vaults and is the single point of contact for all reads and writes.
    """
    def __init__(self, address='', port=8000, vaults=None):
        super(ControlServer, self).__init__(address=address, port=port, handler_class=ControlHandler)
        self._vaults = []
        self._min_value = 0
        self._set_vaults(vaults)
        logging.info(f'Defined {len(self._vaults)} vaults')

    def vaults(self):
        """ Get the list of vaults on which we're storing information.
        """
        return self._vaults

    def send_value_to_vaults(self, value):
        """ Store a value on each of the vaults specified in the constructor.

        We spawn an updater thread for each vault so we won't get slowed down by an unreachable or slow vault.
        Let the client know how many vaults were successfully updated.
        """
        n = int(value.decode('utf-8'))
        if n < self._min_value:
            msg = f'Client would make value decrease from {self._min_value} to {n}'
            logging.warning(msg)
            return [400, msg]
        count = 0
        threads = []
        for vault in self._vaults:
            thread = VaultUpdater(vault, value)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
            count = count + 1 if thread.response() is not None else count
        status_code = 200
        if not self._has_majority(count):
            # If we don't have a majority, this is an error on the storage infrastructure. Indicate that we
            # do not have confidence that the storage request was successful.
            status_code = 500
        else:
            self._min_value = n
        return [status_code, f'Sent updates to {count}/{len(self._vaults)} vaults'.encode('utf-8')]

    def get_value_from_vaults(self):
        """ Get the consensus value stored across our vaults.

        Talk to each vault and get the value stored in said vault. If a majority of the vaults have the same
        value, then we have consensus and can return that value. If there is no consensus, return -1.
        """
        # The 'counts' dictionary stores a map from a possible value to the number of vaults which have that value.
        counts = defaultdict(int)
        for vault in self._vaults:
            value = self._get_value_from_vault(vault)
            if value is not None:
                logging.debug(f'Get vault {vault} Value {value}')
                counts[value] += 1
        logging.info(f'Counts data: {counts}')
        if not counts:
            # We got back no data at all from the vaults. Maybe they're all unreachable?
            logging.error('Could not reach any vaults to get counts data')
            return -1
        # How many vaults store the most common value(s)?
        # Note that there could be more than one value which is the "most common" value;
        # E.g., if we have seven vaults, and:
        # - vaults (A, C, G) have value "1";
        # - vaults (B, D, E) have value "2"; and
        # - vault F has value "4"
        # then the maximum number of vaults with the same value is three (the first two groups).
        max_vaults_with_common_value = max(counts.values())
        if not self._has_majority(max_vaults_with_common_value):
            # The largest grouping of vaults with a common value is not enough to reach consensus.
            logging.warning(f'No majority; only have {max_vaults_with_common_value}/{len(self._vaults)} with a consensus value')
            return -1
        # Return the value which represents consensus.
        return max([v for v,c in counts.items() if c == max_vaults_with_common_value])

    def _set_vaults(self, vaults):
        """ Set the addresses of each vault we're going to use to store information.
        """
        if vaults is None or not vaults:
            return
        self._vaults = vaults.strip().split(',') if vaults.strip() else []
        self._vaults = [w for w in self._vaults if w]

    def _has_majority(self, max_vaults_with_common_value):
        """ Is the largest grouping of vaults with a common value enough to represent a >50% majority?
        """
        num_vaults = len(self._vaults)
        num_for_majority = math.floor(num_vaults / 2) + 1
        return max_vaults_with_common_value >= num_for_majority

    def _get_value_from_vault(self, vault, timeout_sec=1):
        """ Fetch the current value from a given vault, with a timeout.
        """
        try:
            with urlopen(f'http://{vault}/', timeout=timeout_sec) as f:
                v = f.read()
                if v is not None and v:
                    return int(v.decode('utf-8'))
            return None
        except Exception as error:
            logging.warning(f'Error getting value from vault {vault}: {error}')
        return None


def main(argv):
    parser = common.make_parser()
    parser.add_argument('--vaults', type=str, default='', help='Comma-separated list of vaults')
    parsed = parser.parse_args()
    logging.getLogger().setLevel(parsed.loglevel)
    with ControlServer(port=parsed.port, vaults=parsed.vaults) as control:
        control.serve_forever()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
