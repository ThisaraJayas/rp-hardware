from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from receiver import register_receiver
from hardware import encoder_system
import threading
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.')
CORS(app)
# threading mode is best for simple serial apps on Windows
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

register_receiver(app)

# Pass the socket to the hardware logic so it can emit updates
encoder_system.set_socket(socketio)

# Start Hardware Thread
thread = threading.Thread(target=encoder_system.run, daemon=True)
thread.start()

# ================= API ENDPOINTS =================

@app.route("/")
def serve_index():
    return send_from_directory('.', 'index.html')

# Endpoint for Full Status (Postman/Web)
@app.route("/status")
def get_full_status():
    return jsonify(encoder_system.data)

# Endpoint for Length Only
@app.route("/length")
def get_length():
    return jsonify({
        "length_cm": encoder_system.data["cm"],
        "pulses": encoder_system.data["pulses"],
        "unit": "cm"
    })

# Endpoint for Rotation Status
@app.route("/rotation")
def get_rotation():
    return jsonify({
        "rotation": encoder_system.data["rotation"]
    })
    
@app.route('/api/pulse-count')
def get_pulse_count():
    """Simple endpoint that returns just the current pulse count"""
    return str(encoder_system.data["pulses"])
    
@app.route("/motor/stop", methods=["POST", "GET"])
def stop_motor():
    logger.info("✓ STOP BUTTON CLICKED IN WEB INTERFACE")
    success = encoder_system.send_command('0')
    logger.info(f"Stop command result: {'SUCCESS' if success else 'FAILED'}")
    return jsonify({"success": success, "message": "Motor Stopped"})

@app.route("/motor/start", methods=["POST", "GET"])
def start_motor():
    logger.info("✓ START BUTTON CLICKED IN WEB INTERFACE")
    success = encoder_system.send_command('1')
    logger.info(f"Start command result: {'SUCCESS' if success else 'FAILED'}")
    return jsonify({"success": success, "message": "Motor Started"})

# ================= RUN SERVER =================
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Starting Fabric Measurement Server on http://localhost:5000")
    logger.info("=" * 50)
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)