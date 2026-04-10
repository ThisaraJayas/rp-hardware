# app.py (enhanced with App 2's encoder endpoints)

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from flask_socketio import SocketIO
from receiver import register_receiver
from hardware import encoder_system, init_encoder
import threading
import logging
import os
from datetime import datetime


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

# Initialize encoder and start hardware thread
init_encoder()
encoder_system.start()  # Use the enhanced start method

# ================= API ENDPOINTS =================

@app.route("/")
def serve_index():
    return send_from_directory('.', 'index.html')

# Existing endpoints
@app.route("/status")
def get_full_status():
    return jsonify(encoder_system.get_status())

@app.route("/length")
def get_length():
    return jsonify(encoder_system.get_length())

@app.route("/rotation")
def get_rotation():
    return jsonify({
        "rotation": encoder_system.get_status()["rotation"]
    })

@app.route('/api/pulse-count')
def get_pulse_count():
    """Simple endpoint that returns just the current pulse count"""
    return str(encoder_system.get_status()["pulses"])

@app.route("/motor/stop", methods=["POST", "GET"])
def stop_motor():
    logger.info("✓ STOP BUTTON CLICKED IN WEB INTERFACE")
    success = encoder_system.stop_motor()
    logger.info(f"Stop command result: {'SUCCESS' if success else 'FAILED'}")
    return jsonify({"success": success, "message": "Motor Stopped"})

@app.route("/motor/start", methods=["POST", "GET"])
def start_motor():
    logger.info("✓ START BUTTON CLICKED IN WEB INTERFACE")
    success = encoder_system.start_motor()
    logger.info(f"Start command result: {'SUCCESS' if success else 'FAILED'}")
    return jsonify({"success": success, "message": "Motor Started"})

# New endpoints from App 2
@app.route("/encoder/status", methods=["GET"])
def encoder_status():
    """Get full encoder status including all measurements"""
    try:
        status = encoder_system.get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/encoder/length", methods=["GET"])
def encoder_length():
    """Get current length in cm and inches"""
    try:
        length_data = encoder_system.get_length()
        return jsonify(length_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/encoder/pulses", methods=["GET"])
def encoder_pulses():
    """Get current pulse data for chart"""
    try:
        pulse_data = encoder_system.get_pulse_data()
        return jsonify(pulse_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/encoder/history", methods=["GET"])
def encoder_history():
    """Get historical pulse data for chart"""
    try:
        limit = request.args.get("limit", 100, type=int)
        history = encoder_system.get_history(limit)
        return jsonify({
            "success": True,
            "history": history,
            "count": len(history)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/encoder/reset", methods=["POST"])
def encoder_reset():
    """Reset the encoder counter to zero"""
    try:
        encoder_system.reset_counter()
        return jsonify({
            "success": True,
            "message": "Encoder counter reset to zero",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/encoder/fabric-state", methods=["GET"])
def encoder_fabric_state():
    """Get the latest fabric detection state"""
    try:
        fabric_state = encoder_system.get_fabric_state()
        return jsonify(fabric_state)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================= RUN SERVER =================
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Starting Fabric Measurement Server on http://localhost:5000")
    logger.info("=" * 50)
    
    # Register shutdown handler
    import atexit
    atexit.register(encoder_system.shutdown)
    
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)