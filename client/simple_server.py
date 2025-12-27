
import http.server
import socketserver
import os
import threading
import time

# Change to dist directory
os.chdir('dist')

PORT = 5175

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

# Start server in background thread
def run_server():
    with socketserver.TCPServer(('', PORT), Handler) as httpd:
        print(f"Server started at http://localhost:{PORT}")
        httpd.serve_forever()

# Start server
server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

# Keep main thread alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print('Server stopped')
