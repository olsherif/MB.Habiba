from flask import Flask, request
import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return "Koyeb RDP API Online"

@app.route("/ping", methods=["POST"])
def ping():
    data = request.json
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] Ping from: {data.get('name', 'Unknown')}")
    return {"status": "online", "server": data.get('name', 'unknown')}
