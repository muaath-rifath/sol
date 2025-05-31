#!/usr/bin/env python3
"""
Test script to simulate ESP32 devices for Smart Home Automation System
This script creates virtual devices that respond to MQTT commands
"""

import json
import time
import random
import threading
import paho.mqtt.client as mqtt
from datetime import datetime

# Test device configurations
TEST_DEVICES = {
    'living_room_light': {
        'type': 'light',
        'power': 'off',
        'brightness': 100
    },
    'living_room_fan': {
        'type': 'fan',
        'power': 'off',
        'speed': 0
    },
    'bedroom_light': {
        'type': 'light',
        'power': 'off',
        'brightness': 100
    },
    'bedroom_ac': {
        'type': 'ac',
        'power': 'off',
        'temperature': 24,
        'mode': 'cool'
    },
    'kitchen_light': {
        'type': 'light',
        'power': 'off',
        'brightness': 100
    },
    'motion_sensor_entrance': {
        'type': 'motion_sensor',
        'motion_detected': False
    }
}

class VirtualDevice:
    def __init__(self, device_id, config):
        self.device_id = device_id
        self.config = config.copy()
        self.mqtt_client = None
        self.running = False
        
    def connect_mqtt(self, broker='localhost', port=1883):
        """Connect to MQTT broker"""
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        try:
            self.mqtt_client.connect(broker, port, 60)
            self.mqtt_client.loop_start()
            self.running = True
            print(f"✓ {self.device_id} connected to MQTT broker")
            return True
        except Exception as e:
            print(f"✗ {self.device_id} failed to connect: {e}")
            return False
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            # Subscribe to control topic
            control_topic = f"smarthome/{self.device_id}/control"
            client.subscribe(control_topic)
            print(f"✓ {self.device_id} subscribed to {control_topic}")
            
            # Send initial status
            self.publish_status()
        else:
            print(f"✗ {self.device_id} connection failed with code {rc}")
    
    def on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            if 'control' in topic:
                self.handle_control_command(payload)
        except Exception as e:
            print(f"✗ {self.device_id} error processing message: {e}")
    
    def handle_control_command(self, command):
        """Process control commands"""
        print(f"📋 {self.device_id} received command: {command}")
        
        # Update device state based on command
        for key, value in command.items():
            if key in self.config:
                self.config[key] = value
                print(f"   → {key}: {value}")
        
        # Publish updated status
        self.publish_status()
        
        # Simulate energy consumption for powered devices
        if self.config.get('power') == 'on':
            self.publish_energy_data()
    
    def publish_status(self):
        """Publish device status"""
        status_topic = f"smarthome/{self.device_id}/status"
        status_data = {
            'status': 'online',
            'timestamp': datetime.now().isoformat(),
            **self.config
        }
        
        self.mqtt_client.publish(status_topic, json.dumps(status_data))
        print(f"📤 {self.device_id} published status")
    
    def publish_energy_data(self):
        """Publish simulated energy consumption data"""
        if self.config['type'] in ['light', 'fan', 'ac']:
            # Simulate power consumption based on device type and settings
            base_power = {
                'light': 10,
                'fan': 50,
                'ac': 800
            }
            
            power_watts = base_power.get(self.config['type'], 0)
            
            # Adjust power based on settings
            if self.config['type'] == 'light' and 'brightness' in self.config:
                power_watts = power_watts * (self.config['brightness'] / 100)
            elif self.config['type'] == 'fan' and 'speed' in self.config:
                power_watts = power_watts * (self.config['speed'] / 5)
            elif self.config['type'] == 'ac':
                # AC power varies with temperature difference
                power_watts += random.randint(-100, 200)
            
            # Add some random variation
            power_watts += random.randint(-5, 5)
            power_watts = max(0, power_watts)
            
            energy_topic = f"smarthome/{self.device_id}/energy"
            energy_data = {
                'power_watts': round(power_watts, 2),
                'timestamp': datetime.now().isoformat()
            }
            
            self.mqtt_client.publish(energy_topic, json.dumps(energy_data))
            print(f"⚡ {self.device_id} energy: {power_watts:.1f}W")
    
    def simulate_motion_sensor(self):
        """Simulate motion sensor activity"""
        if self.config['type'] == 'motion_sensor':
            while self.running:
                time.sleep(random.randint(30, 120))  # Random motion every 30-120 seconds
                
                if random.random() < 0.3:  # 30% chance of motion
                    motion_detected = True
                    print(f"👁️ {self.device_id} detected motion!")
                    
                    sensor_topic = f"smarthome/{self.device_id}/sensor"
                    sensor_data = {
                        'motion_detected': motion_detected,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    self.mqtt_client.publish(sensor_topic, json.dumps(sensor_data))
                    
                    # Reset motion after 5 seconds
                    time.sleep(5)
                    sensor_data['motion_detected'] = False
                    self.mqtt_client.publish(sensor_topic, json.dumps(sensor_data))
    
    def start_simulation(self):
        """Start device simulation"""
        if self.config['type'] == 'motion_sensor':
            motion_thread = threading.Thread(target=self.simulate_motion_sensor)
            motion_thread.daemon = True
            motion_thread.start()
        
        # Periodic status updates
        status_thread = threading.Thread(target=self.periodic_status_update)
        status_thread.daemon = True
        status_thread.start()
    
    def periodic_status_update(self):
        """Send periodic status updates"""
        while self.running:
            time.sleep(60)  # Status update every minute
            if self.running:
                self.publish_status()
                
                # Publish energy data for active devices
                if self.config.get('power') == 'on':
                    self.publish_energy_data()
    
    def stop(self):
        """Stop the device simulation"""
        self.running = False
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        print(f"🛑 {self.device_id} stopped")

def main():
    """Main function to run virtual device simulation"""
    print("🏠 Starting Virtual Smart Home Devices")
    print("=" * 50)
    
    devices = []
    
    # Create virtual devices
    for device_id, config in TEST_DEVICES.items():
        device = VirtualDevice(device_id, config)
        if device.connect_mqtt():
            device.start_simulation()
            devices.append(device)
    
    print("\n✅ All virtual devices started successfully!")
    print("\nDevices are now listening for commands and sending status updates.")
    print("You can test the system using:")
    print("1. Web dashboard at http://localhost:5000")
    print("2. MQTT commands:")
    print("   mosquitto_pub -t 'smarthome/living_room_light/control' -m '{\"power\": \"on\", \"brightness\": 80}'")
    print("\nPress Ctrl+C to stop all devices")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping all virtual devices...")
        for device in devices:
            device.stop()
        print("✅ All devices stopped")

if __name__ == "__main__":
    main() 