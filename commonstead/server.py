"""A bounded, same-origin HTTP adapter for local development, not production."""
import hmac
import json
import mimetypes
import re
import socket
import sqlite3
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from . import __version__
from .database import SCHEMA_VERSION
from .service import APIError, SESSION_HOURS, Service

COOKIE = 'commonstead_session'
MAX_BODY = 1_048_576
STATIC = Path(__file__).parent / 'static'
CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
       "connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; "
       "frame-ancestors 'none'; form-action 'self'")


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, db, secure_cookies=False, allowed_host=None):
        if ':' in address[0]:
            self.address_family = socket.AF_INET6
        self.service = Service(db)
        self.secure_cookies = secure_cookies
        self.allowed_hosts = {'localhost', '127.0.0.1', '::1'}
        configured = allowed_host or address[0]
        if configured not in ('0.0.0.0', '::'):
            self.allowed_hosts.add(configured.lower())
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = 'Commonstead/' + __version__
    sys_version = ''
    protocol_version = 'HTTP/1.0'

    def log_message(self, format, *args):
        # Omit paths, query strings, cookies, bodies and credentials entirely.
        pass

    def _headers(self, status, content_type, length, cookie=None):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(length))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', CSP)
        self.send_header('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        self.send_header('Cache-Control', 'no-store')
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()

    def _respond(self, value, status=200, cookie=None):
        raw = json.dumps(value, ensure_ascii=True, separators=(',', ':')).encode('utf-8')
        self._headers(status, 'application/json; charset=utf-8', len(raw), cookie)
        if self.command != 'HEAD':
            self.wfile.write(raw)

    def _cookie(self, token='', clear=False):
        value = f'{COOKIE}={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={0 if clear else SESSION_HOURS * 3600}'
        if self.server.secure_cookies:
            value += '; Secure'
        return value

    def _host(self):
        hosts = self.headers.get_all('Host', [])
        if len(hosts) != 1 or not hosts[0] or any(char in hosts[0] for char in '/\\@?# \t\r\n'):
            raise APIError(400, 'invalid_host', 'A valid local Host header is required.')
        try:
            parsed = urlsplit('http://' + hosts[0])
            port = parsed.port
        except ValueError:
            raise APIError(400, 'invalid_host', 'A valid local Host header is required.') from None
        if parsed.hostname not in self.server.allowed_hosts or port not in (None, self.server.server_port):
            raise APIError(403, 'invalid_host', 'Host is not allowed by this local server.')
        return hosts[0].lower()

    def _origin(self, host):
        origins = self.headers.get_all('Origin', [])
        if len(origins) > 1:
            raise APIError(403, 'invalid_origin', 'Request origin is not allowed.')
        if origins:
            expected = ('https' if self.server.secure_cookies else 'http') + '://' + host
            if origins[0].lower() != expected:
                raise APIError(403, 'invalid_origin', 'Request origin must match this application.')
        if self.headers.get('Sec-Fetch-Site', '').lower() == 'cross-site':
            raise APIError(403, 'invalid_origin', 'Cross-site requests are not allowed.')

    def _user(self):
        try:
            cookies = SimpleCookie()
            cookies.load(self.headers.get('Cookie', ''))
            token = cookies[COOKIE].value if COOKIE in cookies else None
        except CookieError:
            token = None
        return self.server.service.authenticate(token)

    def _body(self):
        if self.headers.get_all('Transfer-Encoding'):
            raise APIError(400, 'invalid_body', 'Chunked request bodies are not supported.')
        content_type = self.headers.get('Content-Type', '').split(';', 1)[0].strip().lower()
        if content_type != 'application/json':
            raise APIError(415, 'unsupported_media_type', 'Content-Type must be application/json.')
        lengths = self.headers.get_all('Content-Length', [])
        if len(lengths) != 1 or not re.fullmatch(r'[0-9]+', lengths[0]):
            raise APIError(400, 'invalid_body', 'A valid Content-Length is required.')
        size = int(lengths[0])
        if size > MAX_BODY:
            raise APIError(413, 'body_too_large', 'Request body exceeds 1 MiB.')
        try:
            def unique_pairs(pairs):
                result = {}
                for key, value in pairs:
                    if key in result:
                        raise ValueError('Duplicate JSON key')
                    result[key] = value
                return result
            raw = self.rfile.read(size)
            if len(raw) != size:
                raise ValueError('Incomplete body')
            result = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_pairs,
                                parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Non-finite JSON number')))
            if not isinstance(result, dict):
                raise ValueError('Expected object')
            # Reject unpaired Unicode surrogates before they can reach SQLite or hashing.
            json.dumps(result, ensure_ascii=False).encode('utf-8')
            return result
        except (ValueError, UnicodeError, RecursionError):
            raise APIError(400, 'invalid_json', 'Body must be a valid JSON object with unique keys.') from None

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def do_GET(self):
        self._handle()

    def do_HEAD(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def do_PATCH(self):
        self._handle()

    def do_DELETE(self):
        self._handle()

    def do_OPTIONS(self):
        self._respond({'error': {'code': 'method_not_allowed', 'message': 'Method not allowed.'}}, 405)

    def _handle(self):
        try:
            host = self._host()
            parsed = urlsplit(self.path)
            if parsed.scheme or parsed.netloc:
                raise APIError(400, 'invalid_path', 'Absolute request targets are not supported.')
            path = unquote(parsed.path)
            query_lists = parse_qs(parsed.query, keep_blank_values=True, max_num_fields=20)
            if any(len(values) != 1 for values in query_lists.values()):
                raise APIError(400, 'invalid_query', 'Duplicate query parameters are not supported.')
            query = {key: values[0] for key, values in query_lists.items()}
            service = self.server.service
            user = self._user()
            method = 'GET' if self.command == 'HEAD' else self.command
            data = None
            if method in ('POST', 'PATCH', 'DELETE'):
                self._origin(host)
                if user:
                    csrf = self.headers.get_all('X-CSRF-Token', [])
                    if len(csrf) != 1 or not hmac.compare_digest(csrf[0].encode('utf-8'), user['csrf_token'].encode('utf-8')):
                        raise APIError(403, 'csrf_failed', 'A valid X-CSRF-Token header is required.')
                data = self._body()
            cookie, status = None, 200
            if path == '/health' and method == 'GET':
                result = {'status': 'ok', 'version': __version__, 'schema_version': SCHEMA_VERSION}
            elif path == '/api/session' and method == 'GET':
                result = service.session(user)
            elif path == '/api/register' and method == 'POST':
                result, token = service.register(data)
                cookie, status = self._cookie(token), 201
            elif path == '/api/login' and method == 'POST':
                result, token = service.login(data, self.client_address[0])
                cookie = self._cookie(token)
            elif path == '/api/logout' and method == 'POST':
                result = service.logout(user)
                cookie = self._cookie(clear=True)
            elif path == '/api/members' and method == 'GET':
                result = service.members(user)
            elif re.fullmatch(r'/api/members/[^/]+', path) and method == 'PATCH':
                result = service.change_role(user, path.rsplit('/', 1)[1], data)
            elif path == '/api/invitations' and method == 'POST':
                result, status = service.invite(user, data), 201
            elif path == '/api/invitations/preview' and method == 'GET':
                result = service.invitation_preview(query.get('token', ''))
            elif path == '/api/invitations/accept' and method == 'POST':
                result, token = service.accept_invitation(data)
                cookie, status = self._cookie(token), 201
            elif re.fullmatch(r'/api/records/[^/]+(?:/[^/]+)?', path):
                parts = path.split('/')
                entity = parts[3]
                record_id = parts[4] if len(parts) == 5 else None
                if method == 'GET':
                    result = service.get_record(user, entity, record_id) if record_id else service.records(user, entity, query)
                elif method == 'POST' and not record_id:
                    result, status = service.create_record(user, entity, data), 201
                elif method == 'PATCH' and record_id:
                    result = service.update_record(user, entity, record_id, data)
                elif method == 'DELETE' and record_id:
                    result = service.delete_record(user, entity, record_id)
                else:
                    raise APIError(405, 'method_not_allowed', 'Method not allowed.')
            elif path == '/api/reports/pipeline' and method == 'GET':
                result = service.pipeline(user)
            elif path == '/api/import/contacts' and method == 'POST':
                result = service.import_contacts(user, data)
            elif path == '/api/export/contacts' and method == 'GET':
                raw = service.export_contacts(user).encode('utf-8')
                self._headers(200, 'text/csv; charset=utf-8', len(raw))
                if self.command != 'HEAD':
                    self.wfile.write(raw)
                return
            elif path == '/api/audit' and method == 'GET':
                result = service.audit(user, query)
            elif not path.startswith('/api/') and method == 'GET':
                self._static(path)
                return
            else:
                raise APIError(404, 'not_found', 'Resource not found.')
            self._respond(result, status, cookie)
        except APIError as error:
            self._respond(error.body(), error.status)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            self.close_connection = True
        except (ValueError, UnicodeError):
            self._respond({'error': {'code': 'invalid_request', 'message': 'Request could not be parsed.'}}, 400)
        except sqlite3.Error:
            self._respond({'error': {'code': 'storage_error', 'message': 'Storage operation failed. Try again.'}}, 503)
        except Exception:
            self._respond({'error': {'code': 'internal_error', 'message': 'Unexpected server error.'}}, 500)

    def _static(self, path):
        if path == '/':
            path = '/index.html'
        root = STATIC.resolve()
        file = (root / path.lstrip('/')).resolve()
        if root not in file.parents or file.suffix not in ('.html', '.js', '.css', '.svg', '.ico', '.png') or not file.is_file():
            raise APIError(404, 'not_found', 'Resource not found.')
        raw = file.read_bytes()
        media_type = mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
        if file.suffix in ('.html', '.js', '.css', '.svg'):
            media_type += '; charset=utf-8'
        self._headers(200, media_type, len(raw))
        if self.command != 'HEAD':
            self.wfile.write(raw)
