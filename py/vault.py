#!/usr/bin/env python

import argparse
import common
import logging
import sys

from random import uniform
from time import sleep, time


class VaultHandler(common.BaseHandler):
    def do_GET(self):
        """ Get the current value of the counter.
        """
        if not self.validate_or_reject_path():
            return
        counter_value = self.server.get_counter()
        response_bytes = f'{counter_value}'.encode('utf-8')
        self.send_status_and_response(200, 'text/plain', response_bytes)

    def do_POST(self):
        """ Update the value in storage to what is provided in the body.
        """
        if not self.validate_or_reject_path():
            return
        post_body = self.get_post_body_bytes()
        counter = self.server.set_counter(int(post_body.decode('utf-8')))
        response = f'{counter}'.encode('utf-8')
        self.send_status_and_response(200, 'text/plain', response)


class VaultServer(common.BaseServer):
    def __init__(self, address='', port=8001):
        super(VaultServer, self).__init__(address=address, port=port, handler_class=VaultHandler)
        self._counter = 0
        logging.info(f'Vault listening on {self._address}:{self._port} with counter at {self._counter}')

    def get_counter(self):
        """ Get the value stored in the counter.
        """
        logging.info(f'Get Vault {self._address}:{self._port} value={self._counter}')
        return self._counter

    def set_counter(self, value):
        """ Update the value of the counter.

        Logs a warning if the counter counts down for whatever reason (but still update it).
        """
        if value < self._counter:
            logging.warning(f'THIS SHOULD NEVER HAPPEN: Counter value will regress from {self._counter} to {value}')
        self._counter = value
        logging.info(f'Set Vault {self._address}:{self._port} Counter {self._counter}')
        return self._counter


def main(argv):
    parsed = common.make_parser().parse_args()
    logging.getLogger().setLevel(parsed.loglevel)
    with VaultServer(port=parsed.port) as vault:
        vault.serve_forever()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
