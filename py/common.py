#!/usr/bin/env python

import argparse
import logging

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def make_parser():
    parser = argparse.ArgumentParser(description='Distributed counter controller')
    parser.add_argument('--port', type=int, default=8000,
                        help='Port on which to listen for requests')
    parser.add_argument('--loglevel', type=str.upper,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'FATAL'],
                        default='WARNING', help='Specify logging level.')
    return parser


def set_log_level(level_name):
    return


class BaseHandler(BaseHTTPRequestHandler):
    """ Base request handler class used by both the control server and vaults.
    """
    def get_post_body_bytes(self):
        """ Get the post body as bytes.

        We need to use the content-length header to make sure we read the correct number of bytes,
        because if we just do a read() we'll end up blocking forever because the HTTP spec does allow
        for streaming requests i.e., more bytes to come through on an open connection.
        """
        content_len = int(self.headers.get('content-length', 0))
        return self.rfile.read(content_len)

    def validate_or_reject_path(self):
        """ Validate the request path, or send back a rejection.

        Returns true if the path is valid, otherwise sends back a 400 to the client and returns false to the caller.
        """
        if self.path == '/':
            return True
        self.send_response(400, f'Invalid path: {self.path}')
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        return False

    def send_status_and_response(self, status_code, content_type, body):
        """ Convenience function to send back a response with the correct headers.
        """
        if isinstance(body, str):
            # If we've been handed a string, encode it to bytes since self.wfile.write expects bytes.
            body = body.encode('utf-8')
        try:
            self.send_response(status_code)
            self.send_header('Content-type', content_type)
            if body is not None:
                self.send_header('Content-length', f'{len(body)}')
            self.end_headers()
            if body is not None and body:
                self.wfile.write(body)
        except Exception as error:
            logging.error(f'Error writing {len(body)}-byte response with status {status_code}: {error}')

    def log_message(self, format, *args):
        """ Disable HTTP logging for now.
        """
        pass


class BaseServer(ThreadingHTTPServer):
    """ Base (threading) HTTP server class used by both the control server and the vaults.
    """
    def __init__(self, address='', port=8000, handler_class=BaseHandler):
        self._address = address
        self._port = port
        super(BaseServer, self).__init__((self._address, self._port), handler_class)
