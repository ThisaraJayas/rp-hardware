from pathlib import Path
from flask import request, jsonify
import os
import time

# ==========================================================
# SAVE DIRECTORY
# ==========================================================

SAVE_DIR = Path(r"E:\fabric_images\input")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================================
# GLOBAL DASHBOARD STATE
# ==========================================================

LATEST_FABRIC_STATE = {
    "pattern": None,
    "pattern_type": None,
    "dominant_color": None,
    "secondary_color": None,
    "quality_score": None,
    "enhancement_mode": None,
    "frames_processed": 0,
    "fps": 0,
    "last_update": None
}

# ==========================================================
# HELPER
# ==========================================================

def get_safe_filename(filename):
    """
    Keep original filename but remove unsafe path parts.
    """
    return os.path.basename(filename)


# ==========================================================
# REGISTER ROUTES
# ==========================================================

def register_receiver(app):

    # ------------------------------------------------------
    # RECEIVE FRAME + METADATA FROM COMPONENT 2
    # ------------------------------------------------------
    @app.route("/receive-enhanced-frame", methods=["POST"])
    def receive_enhanced_frame():

        try:

            if "file" not in request.files:
                return jsonify({
                    "status": "error",
                    "message": "No file part in request"
                }), 400

            file = request.files["file"]

            frame_name = request.form.get("frame_name", file.filename)
            timestamp = request.form.get("timestamp", "")

            if not frame_name:
                return jsonify({
                    "status": "error",
                    "message": "frame_name is missing"
                }), 400

            # --------------------------------------------
            # SAVE IMAGE
            # --------------------------------------------
            safe_name = get_safe_filename(frame_name)
            save_path = SAVE_DIR / safe_name

            file.save(str(save_path))

            # --------------------------------------------
            # RECEIVE METADATA FROM PI
            # --------------------------------------------
            pattern = request.form.get("pattern")
            pattern_type = request.form.get("pattern_type")
            dominant_color = request.form.get("dominant_color")
            secondary_color = request.form.get("secondary_color")
            quality_score = request.form.get("quality_score")
            enhancement_mode = request.form.get("enhancement_mode")
            frames_processed = request.form.get("frames_processed")
            fps = request.form.get("fps")

            # --------------------------------------------
            # UPDATE DASHBOARD STATE
            # --------------------------------------------
            LATEST_FABRIC_STATE["pattern"] = pattern
            LATEST_FABRIC_STATE["pattern_type"] = pattern_type
            LATEST_FABRIC_STATE["dominant_color"] = dominant_color
            LATEST_FABRIC_STATE["secondary_color"] = secondary_color
            LATEST_FABRIC_STATE["quality_score"] = quality_score
            LATEST_FABRIC_STATE["enhancement_mode"] = enhancement_mode
            LATEST_FABRIC_STATE["frames_processed"] = frames_processed
            LATEST_FABRIC_STATE["fps"] = fps
            LATEST_FABRIC_STATE["last_update"] = time.time()

            # --------------------------------------------
            # DEBUG LOG
            # --------------------------------------------
            print("\n===== FRAME RECEIVED =====")
            print("Saved:", save_path)
            print("Pattern:", pattern)
            print("Pattern Type:", pattern_type)
            print("Dominant Color:", dominant_color)
            print("Secondary Color:", secondary_color)
            print("Quality Score:", quality_score)
            print("Enhancement Mode:", enhancement_mode)
            print("Frames Processed:", frames_processed)
            print("FPS:", fps)

            return jsonify({
                "status": "success",
                "filename": safe_name
            }), 200

        except Exception as e:

            print("Receiver error:", e)

            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500


    # ------------------------------------------------------
    # DASHBOARD API
    # ------------------------------------------------------
    @app.route("/api/fabric-state", methods=["GET"])
    def get_fabric_state():

        return jsonify(LATEST_FABRIC_STATE)