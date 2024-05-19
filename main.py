import mimetypes
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import socket
import json
from datetime import datetime
import os
import threading

BASE_DIR = pathlib.Path()


class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}

        # Відправляємо дані на сокет-сервер
        self.send_to_socket_server(data_dict)

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_to_socket_server(self, data):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_address = ('localhost', 5000)
        message = json.dumps(data).encode()
        try:
            sock.sendto(message, server_address)
        finally:
            sock.close()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static(BASE_DIR.joinpath(pr_url.path[1:]))
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header("Content-Type", mime_type)
        else:
            self.send_header("Content-Type", "text/plain")
        self.end_headers()
        with open(filename, "rb", ) as file:
            self.wfile.write(file.read())


def run_http_server():
    server_address = ('0.0.0.0', 3000)
    httpd = HTTPServer(server_address, HttpHandler)
    print("HTTP server is running on port 3000")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


def run_socket_server():
    # Створюємо папку storage, якщо вона не існує
    if not os.path.exists('storage'):
        os.makedirs('storage')

    # Ініціалізуємо або завантажуємо існуючий файл data.json
    data_file_path = 'storage/data.json'
    if os.path.exists(data_file_path):
        with open(data_file_path, 'r') as file:
            data = json.load(file)
    else:
        data = {}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('localhost', 5000)
    sock.bind(server_address)

    print("Socket server is running on port 5000")

    while True:
        print("Waiting for a message...")
        message, address = sock.recvfrom(4096)
        if message:
            data_dict = json.loads(message.decode())
            timestamp = datetime.now().isoformat()
            data[timestamp] = data_dict
            with open(data_file_path, 'w') as file:
                json.dump(data, file, indent=4)
            print(f"Data received and stored at {timestamp}")


if __name__ == '__main__':
    threading.Thread(target=run_http_server).start()
    threading.Thread(target=run_socket_server).start()