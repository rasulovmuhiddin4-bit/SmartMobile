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
    
def start_keep_alive():
    """Botni doimiy ishlashini ta'minlash"""
    # Flask serverni ishga tushirish
    t = Thread(target=run)
    t.daemon = True
    t.start()
    logging.info("🌐 Web server started on port 8080")
    
    # Self-ping funksiyasi
    def ping_self():
        url = "https://smartmobile-bot.onrender.com"  # Render URL
        while True:
            try:
                requests.get(url, timeout=10)
                logging.info("🏓 Self-ping successful")
                time.sleep(240)  # 4 daqiqa
            except Exception as e:
                logging.error(f"❌ Self-ping error: {e}")
                time.sleep(60)
    
    # Ping thread
    ping_thread = Thread(target=ping_self)
    ping_thread.daemon = True
    ping_thread.start()
    logging.info("⏲ Self-ping thread started")
    
    # Monitor thread
    def monitor():
        while True:
            logging.info(f"📊 Bot is running... Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(600)  # 10 daqiqa
    
    monitor_thread = Thread(target=monitor)
    monitor_thread.daemon = True
    monitor_thread.start()    