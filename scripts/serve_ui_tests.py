"""Serve the account-free test fixture locally. Account tests supply their own SDK."""
import http.server
import sys
from urllib.parse import urlsplit


class FixtureHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="docs", **kwargs)

    def do_GET(self):
        if urlsplit(self.path).path != "/account-config.js":
            return super().do_GET()
        body = b"window.KEP_ACCOUNT_CONFIG = {};"
        self.send_response(200)
        self.send_header("Content-Type", "application/javascript")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), FixtureHandler).serve_forever()
