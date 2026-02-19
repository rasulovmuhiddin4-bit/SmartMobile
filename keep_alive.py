from flask import Flask
from threading import Thread
import logging
import time
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 SmartMobile Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Botni doimiy ishlashini ta'minlash"""
    t = Thread(target=run)
    t.daemon = True
    t.start()
    logging.info("🌐 Web server started on port 8080")
    
    # Self-ping uchun alohida thread
    def self_ping():
        while True:
            try:
                requests.get('http://localhost:8080/')
                time.sleep(300)  # Har 5 daqiqada ping
            except:
                pass
    
    ping_thread = Thread(target=self_ping)
    ping_thread.daemon = True
    ping_thread.start()
    logging.info("⏲ Self-ping thread started")