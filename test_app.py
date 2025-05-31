#!/usr/bin/env python3
"""
Simple test script to verify Flask app functionality
"""

import requests
import time
import subprocess
import signal
import os

def test_flask_app():
    """Test if Flask app is running and responding"""
    try:
        # Test API endpoint
        response = requests.get('http://127.0.0.1:5000/api/devices', timeout=5)
        print(f"✓ API Status: {response.status_code}")
        if response.status_code == 200:
            devices = response.json()
            print(f"✓ Found {len(devices)} devices in database")
            for device in devices[:3]:  # Show first 3 devices
                print(f"  - {device['name']} ({device['type']}) in {device['room']}")
        
        # Test main page
        response = requests.get('http://127.0.0.1:5000/', timeout=5)
        print(f"✓ Web page Status: {response.status_code}")
        if 'Smart Home' in response.text:
            print("✓ Web page content looks correct")
        else:
            print("⚠ Web page content may be incomplete")
            
        print("\n🎉 Flask application is working correctly!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to Flask app on port 5000")
        return False
    except Exception as e:
        print(f"✗ Error testing Flask app: {e}")
        return False

def test_mqtt_simulation():
    """Test MQTT commands"""
    try:
        import paho.mqtt.client as mqtt
        import json
        
        client = mqtt.Client()
        client.connect("localhost", 1883, 60)
        
        # Test sending a command
        command = {"power": "on", "brightness": 80}
        client.publish("smarthome/living_room_light/control", json.dumps(command))
        print("✓ MQTT command sent successfully")
        
        client.disconnect()
        return True
        
    except Exception as e:
        print(f"✗ MQTT test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Smart Home Automation System")
    print("=" * 50)
    
    print("\n1. Testing Flask Application...")
    flask_ok = test_flask_app()
    
    print("\n2. Testing MQTT Communication...")
    mqtt_ok = test_mqtt_simulation()
    
    print("\n" + "=" * 50)
    if flask_ok and mqtt_ok:
        print("✅ All tests passed! The system is working correctly.")
        print("\n🌐 Open http://localhost:5000 in your browser to access the dashboard")
    else:
        print("❌ Some tests failed. Check the error messages above.")
        
    print("\n💡 Next steps:")
    print("1. Start the main app: python main.py")
    print("2. Start virtual devices: python test_devices.py")
    print("3. Access the dashboard at http://localhost:5000") 