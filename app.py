import os, time, threading, json, requests
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", 8080))
PLATFORM = os.environ.get("PLATFORM", "blitz-jef")
CITY = os.environ.get("CITY", "平壤")
NAME = os.environ.get("NAME", "Blitz jef")
FLAG = os.environ.get("FLAG", "\U0001F1F0\U0001F1F5")
LAT = float(os.environ.get("LAT", "39.0339"))
LON = float(os.environ.get("LON", "125.7544"))
TZ = os.environ.get("TZ", "Asia/Pyongyang")
WORKER_URL = os.environ.get("WORKER_URL", "https://weather-push.jardanlau-e4b.workers.dev/weather")
INTERVAL = int(os.environ.get("INTERVAL", "300"))

latest_weather = {"temp": "--", "desc": "Initializing", "ts": 0}


def fetch_weather():
    global latest_weather
    url = ("https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s"
           "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&timezone=%s"
           % (LAT, LON, TZ))
    try:
        r = requests.get(url, timeout=15).json()
        curr = r.get("current", {})
        w_data = {
            "platform": PLATFORM,
            "city": CITY,
            "flag": FLAG,
            "name": NAME,
            "temp": str(curr.get("temperature_2m")),
            "desc": "Weather",
            "humidity": str(curr.get("relative_humidity_2m")),
            "wind": str(curr.get("wind_speed_10m")),
            "rain": "0",
            "source": "Open-Meteo",
            "ts": int(time.time()),
        }
        latest_weather = w_data
        print("[Weather] Fetched %s: %s C" % (CITY, w_data["temp"]), flush=True)
        try:
            pr = requests.post(WORKER_URL, json=w_data, timeout=15)
            print("[Weather] Posted to worker: %s" % pr.status_code, flush=True)
        except Exception as pe:
            print("[Weather] Worker post error: %s" % pe, flush=True)
    except Exception as e:
        print("[Weather] Fetch error: %s" % e, flush=True)


def loop():
    while True:
        fetch_weather()
        time.sleep(INTERVAL)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = {"status": "ok", "service": "pyongyang-weather", "platform": PLATFORM, "city": CITY}
        elif self.path in ("/weather", "/weather/today"):
            body = latest_weather
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(("%s Weather Node (%s)" % (CITY, PLATFORM)).encode())
            return
        payload = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *a):
        pass


def run_server():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print("Server started on port %s" % PORT, flush=True)
    server.serve_forever()


if __name__ == "__main__":
    threading.Thread(target=loop, daemon=True).start()
    run_server()
