import http.server
import socketserver
import webbrowser
import threading
import os

PORT = 8081
os.chdir(os.path.dirname(__file__))

Handler = http.server.SimpleHTTPRequestHandler

def open_browser():
    # Open key pages to make navigation easy
    webbrowser.open(f'http://localhost:{PORT}/login.html')
    webbrowser.open(f'http://localhost:{PORT}/register.html')
    webbrowser.open(f'http://localhost:{PORT}/profile.html')

if __name__ == "__main__":
    threading.Timer(1.0, open_browser).start()
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(
            f"Serving frontend at http://localhost:{PORT}/ (login.html, register.html, profile.html)"
        )
        httpd.serve_forever()
