import os
import json
import sqlite3
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart_home_secret_key_2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPICS = {
    'device_status': 'smarthome/+/status',
    'device_control': 'smarthome/+/control',
    'sensor_data': 'smarthome/+/sensor',
    'energy_data': 'smarthome/+/energy'
}

# Global variables
mqtt_client = None
devices = {}
sensor_data = {}

# Database initialization
def init_database():
    """Initialize SQLite database for device management and logging"""
    conn = sqlite3.connect('smart_home.db')
    cursor = conn.cursor()
    
    # Devices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            room TEXT NOT NULL,
            status TEXT DEFAULT 'offline',
            last_seen TIMESTAMP,
            config TEXT
        )
    ''')
    
    # Device logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            action TEXT,
            value TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    ''')
    
    # Energy consumption table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS energy_consumption (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            power_watts REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id)
        )
    ''')
    
    # Security events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT,
            event_type TEXT,
            description TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample devices if none exist
    cursor.execute('SELECT COUNT(*) FROM devices')
    if cursor.fetchone()[0] == 0:
        sample_devices = [
            ('living_room_light', 'Living Room Light', 'light', 'living_room', 'offline', '{"brightness": 100}'),
            ('living_room_fan', 'Living Room Fan', 'fan', 'living_room', 'offline', '{"speed": 0}'),
            ('bedroom_light', 'Bedroom Light', 'light', 'bedroom', 'offline', '{"brightness": 100}'),
            ('bedroom_ac', 'Bedroom AC', 'ac', 'bedroom', 'offline', '{"temperature": 24, "mode": "cool"}'),
            ('kitchen_light', 'Kitchen Light', 'light', 'kitchen', 'offline', '{"brightness": 100}'),
            ('motion_sensor_entrance', 'Entrance Motion Sensor', 'motion_sensor', 'entrance', 'offline', '{}'),
        ]
        
        cursor.executemany('''
            INSERT INTO devices (id, name, type, room, status, config) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_devices)
    
    conn.commit()
    conn.close()

# MQTT Functions
def on_mqtt_connect(client, userdata, flags, rc):
    """Callback for MQTT connection"""
    if rc == 0:
        print("Connected to MQTT broker")
        # Subscribe to all device topics
        for topic in MQTT_TOPICS.values():
            client.subscribe(topic)
        socketio.emit('mqtt_status', {'connected': True})
    else:
        print(f"Failed to connect to MQTT broker: {rc}")

def on_mqtt_message(client, userdata, msg):
    """Handle incoming MQTT messages"""
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        
        # Extract device ID from topic
        topic_parts = topic.split('/')
        device_id = topic_parts[1] if len(topic_parts) > 1 else None
        
        if 'status' in topic:
            handle_device_status(device_id, payload)
        elif 'sensor' in topic:
            handle_sensor_data(device_id, payload)
        elif 'energy' in topic:
            handle_energy_data(device_id, payload)
            
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

def handle_device_status(device_id, payload):
    """Handle device status updates"""
    if device_id:
        devices[device_id] = payload
        
        # Update database
        conn = sqlite3.connect('smart_home.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE devices SET status = ?, last_seen = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (payload.get('status', 'online'), device_id))
        
        # Log the status change
        cursor.execute('''
            INSERT INTO device_logs (device_id, action, value) 
            VALUES (?, ?, ?)
        ''', (device_id, 'status_update', json.dumps(payload)))
        
        conn.commit()
        conn.close()
        
        # Broadcast to web clients
        socketio.emit('device_update', {
            'device_id': device_id,
            'data': payload
        })

def handle_sensor_data(device_id, payload):
    """Handle sensor data updates"""
    if device_id:
        sensor_data[device_id] = payload
        
        # Check for security events
        if payload.get('motion_detected'):
            conn = sqlite3.connect('smart_home.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO security_events (sensor_id, event_type, description) 
                VALUES (?, ?, ?)
            ''', (device_id, 'motion_detected', 'Motion detected by sensor'))
            conn.commit()
            conn.close()
            
            # Broadcast security alert
            socketio.emit('security_alert', {
                'sensor_id': device_id,
                'event': 'motion_detected',
                'timestamp': datetime.now().isoformat()
            })

def handle_energy_data(device_id, payload):
    """Handle energy consumption data"""
    if device_id and 'power_watts' in payload:
        conn = sqlite3.connect('smart_home.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO energy_consumption (device_id, power_watts) 
            VALUES (?, ?)
        ''', (device_id, payload['power_watts']))
        conn.commit()
        conn.close()

def init_mqtt():
    """Initialize MQTT client"""
    global mqtt_client
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message
    
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")

# Flask Routes
@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/api/devices')
def get_devices():
    """Get all devices from database"""
    conn = sqlite3.connect('smart_home.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, type, room, status, last_seen, config 
        FROM devices
    ''')
    
    devices_list = []
    for row in cursor.fetchall():
        device = {
            'id': row[0],
            'name': row[1],
            'type': row[2],
            'room': row[3],
            'status': row[4],
            'last_seen': row[5],
            'config': json.loads(row[6]) if row[6] else {}
        }
        devices_list.append(device)
    
    conn.close()
    return jsonify(devices_list)

@app.route('/api/device/<device_id>/control', methods=['POST'])
def control_device(device_id):
    """Control a specific device"""
    try:
        command = request.json
        
        # Publish MQTT command
        topic = f"smarthome/{device_id}/control"
        mqtt_client.publish(topic, json.dumps(command))
        
        # Log the command
        conn = sqlite3.connect('smart_home.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO device_logs (device_id, action, value) 
            VALUES (?, ?, ?)
        ''', (device_id, 'control_command', json.dumps(command)))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Command sent'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/energy/summary')
def energy_summary():
    """Get energy consumption summary"""
    conn = sqlite3.connect('smart_home.db')
    cursor = conn.cursor()
    
    # Get today's consumption by device
    cursor.execute('''
        SELECT d.name, AVG(e.power_watts) as avg_power, MAX(e.power_watts) as peak_power
        FROM energy_consumption e
        JOIN devices d ON e.device_id = d.id
        WHERE DATE(e.timestamp) = DATE('now')
        GROUP BY d.id, d.name
    ''')
    
    energy_data = []
    for row in cursor.fetchall():
        energy_data.append({
            'device': row[0],
            'avg_power': round(row[1] or 0, 2),
            'peak_power': round(row[2] or 0, 2)
        })
    
    conn.close()
    return jsonify(energy_data)

@app.route('/api/security/events')
def security_events():
    """Get recent security events"""
    conn = sqlite3.connect('smart_home.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sensor_id, event_type, description, timestamp
        FROM security_events
        ORDER BY timestamp DESC
        LIMIT 10
    ''')
    
    events = []
    for row in cursor.fetchall():
        events.append({
            'sensor_id': row[0],
            'event_type': row[1],
            'description': row[2],
            'timestamp': row[3]
        })
    
    conn.close()
    return jsonify(events)

@app.route('/api/ai/command', methods=['POST'])
def ai_command():
    """Process natural language commands using Gemini API"""
    try:
        user_input = request.json.get('command', '')
        
        # Configure Gemini API (you'll need to set GEMINI_API_KEY in .env)
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return jsonify({'success': False, 'error': 'Gemini API key not configured'})
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Get current device list for context
        conn = sqlite3.connect('smart_home.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, type, room FROM devices')
        device_list = cursor.fetchall()
        conn.close()
        
        context = "Available devices:\n"
        for device in device_list:
            context += f"- {device[1]} (ID: {device[0]}, Type: {device[2]}, Room: {device[3]})\n"
        
        prompt = f"""
        You are a smart home assistant. Based on this command: "{user_input}"
        
        {context}
        
        Generate a JSON response with device control commands. Format:
        {{
            "actions": [
                {{"device_id": "device_id", "command": {{"action": "value"}}}}
            ],
            "response": "Human-readable response"
        }}
        
        For lights: {{"power": "on/off", "brightness": 0-100}}
        For fans: {{"power": "on/off", "speed": 0-5}}
        For AC: {{"power": "on/off", "temperature": 16-30, "mode": "cool/heat/auto"}}
        
        Only return valid JSON.
        """
        
        response = model.generate_content(prompt)
        ai_response = json.loads(response.text)
        
        # Execute the actions
        for action in ai_response.get('actions', []):
            device_id = action.get('device_id')
            command = action.get('command')
            if device_id and command:
                topic = f"smarthome/{device_id}/control"
                mqtt_client.publish(topic, json.dumps(command))
        
        return jsonify({
            'success': True,
            'response': ai_response.get('response', 'Commands executed'),
            'actions': ai_response.get('actions', [])
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# SocketIO Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'message': 'Connected to Smart Home Hub'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

if __name__ == '__main__':
    print("Initializing Smart Home Automation System...")
    
    # Initialize database
    init_database()
    print("✓ Database initialized")
    
    # Initialize MQTT
    init_mqtt()
    print("✓ MQTT client initialized")
    
    print("✓ Starting Flask server...")
    print("Dashboard will be available at: http://localhost:5000")
    print("Make sure Mosquitto MQTT broker is running on localhost:1883")
    
    # Run the Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
