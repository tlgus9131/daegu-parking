import http.server
import urllib.request
import urllib.error
import json
import os
from datetime import datetime

PORT = int(os.environ.get('PORT', 8000))
API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
WEATHER_KEY = os.environ.get('WEATHER_API_KEY', '')

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/weather':
            self.get_weather()
        else:
            super().do_GET()

    def get_weather(self):
        now = datetime.now()
        base_date = now.strftime('%Y%m%d')
        hour = now.hour
        base_times = [2, 5, 8, 11, 14, 17, 20, 23]
        base_time = max([t for t in base_times if t <= hour], default=23)
        base_time_str = str(base_time).zfill(2) + '00'
        url = (
            'https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst'
            '?serviceKey=' + WEATHER_KEY +
            '&numOfRows=10&pageNo=1&dataType=JSON'
            '&base_date=' + base_date +
            '&base_time=' + base_time_str +
            '&nx=89&ny=90'
        )
        try:
            with urllib.request.urlopen(url) as res:
                data = res.read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def do_POST(self):
        if self.path == '/api/chat':
            length = int(self.headers['Content-Length'])
            body = self.rfile.read(length)
            req = urllib.request.Request(
                'https://api.anthropic.com/v1/messages',
                data=body,
                headers={
                    'Content-Type': 'application/json',
                    'x-api-key': API_KEY,
                    'anthropic-version': '2023-06-01'
                },
                method='POST'
            )
            try:
                with urllib.request.urlopen(req) as res:
                    result = res.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(result)
            except urllib.error.HTTPError as e:
                body = e.read()
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print("[%s] %s" % (self.address_string(), format % args))

with http.server.HTTPServer(('', PORT), Handler) as httpd:
    print("server running on port %d" % PORT)
    httpd.serve_forever()
