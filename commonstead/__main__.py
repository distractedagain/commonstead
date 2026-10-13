"""Run the Commonstead local development server."""
import argparse
import os

from .server import Server


def main():
    parser = argparse.ArgumentParser(description='Commonstead local development CRM (not a production HTTP server).')
    parser.add_argument('--db', default='data/commonstead.sqlite3', help='SQLite database path')
    parser.add_argument('--host', default='127.0.0.1', help='Bind address (default: loopback only)')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--secure-cookies', action='store_true', help='Require HTTPS for session cookies; local TLS termination required')
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('--port must be between 0 and 65535')
    os.umask(0o077)
    server = Server((args.host, args.port), args.db, args.secure_cookies)
    print(f'Commonstead local development server: http://{args.host}:{server.server_port}', flush=True)
    print('Development use only. Keep this server on a trusted local machine.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
