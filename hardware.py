import serial
import threading
import math
import time

# ================= SETTINGS =================
SERIAL_PORT = 'COM3'
BAUD_RATE = 115200
PPR = 1200
WHEEL_DIAMETER = 3.8
CIRCUMFERENCE = math.pi * WHEEL_DIAMETER
STOP_TIMEOUT = 2.0  # seconds without pulse = stopped

class FabricEncoder:
    def __init__(self):
        self.data = {
            "pulses": 0,
            "cm": 0.0,
            "status": "Initializing...",
            "rotation": "Stopped",
            "last_update": "",
            "motor_on": True
        }
        self.last_pulse_time = time.time()
        self.last_pulse_count = 0
        self.socketio = None
        self.ser = None  # Store serial object

    def set_socket(self, socket):
        self.socketio = socket

    def send_command(self, cmd):
        """Sends '0' for stop or '1' for start to Arduino"""
        try:
            if self.ser and self.ser.is_open:
                # 1. Clear any old data in the output buffer
                self.ser.reset_output_buffer() 
                # 2. Write the command
                self.ser.write(cmd.encode('utf-8'))
                # 3. Force it out now
                self.ser.flush() 
                
                self.data["motor_on"] = (cmd == '1')
                print(f"SENT TO ARDUINO: {cmd}")
                return True
            else:
                print("Serial port not open")
                return False
        except Exception as e:
            print(f"Error sending command: {e}")
            return False

    def run(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
            self.data["status"] = "Connected & Reading"
            print(f"Connected to {SERIAL_PORT}")

            while True:
                # 1. READ SERIAL (As fast as possible)
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode(errors="ignore").strip()
                    
                    if "Pulse Count:" in line:
                        try:
                            count = int(line.split(":")[1].strip())
                            self.data["pulses"] = count
                            self.data["cm"] = round((count / PPR) * CIRCUMFERENCE, 2)
                            self.data["last_update"] = time.strftime("%H:%M:%S")

                            # Detect movement
                            if count != self.last_pulse_count:
                                self.data["rotation"] = "Running"
                                self.last_pulse_time = time.time()
                                self.last_pulse_count = count

                            # Emit via WebSocket immediately when data arrives
                            if self.socketio:
                                self.socketio.emit("encoder_update", self.data)
                        except Exception as e:
                            print(f"Error parsing pulse: {e}")
                            pass

                # 2. CHECK STOP STATUS (Only update if it was running)
                if self.data["rotation"] == "Running":
                    if time.time() - self.last_pulse_time > STOP_TIMEOUT:
                        self.data["rotation"] = "Stopped"
                        if self.socketio:
                            self.socketio.emit("encoder_update", self.data)

                # 3. VERY TINY SLEEP (Just to keep CPU cool, but not miss pulses)
                time.sleep(0.01) 

        except Exception as e:
            self.data["status"] = f"Error: {str(e)}"
            print(f"Hardware Error: {e}")

# Global instance
encoder_system = FabricEncoder()