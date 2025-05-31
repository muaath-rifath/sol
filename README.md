# 🏠 Smart Home Automation System

A privacy-focused Smart Home Automation system built with Flask, MQTT, and AI integration using Google's Gemini Flash 2.5. This system provides centralized control of home appliances and security monitoring while keeping all data local.

## 🌟 Features

### Core Functionality
- **Device Control**: Remote control of lights, fans, air conditioners
- **Security Monitoring**: Motion sensor integration and event logging
- **Energy Monitoring**: Track power consumption and usage patterns
- **Real-time Updates**: WebSocket-based live device status updates

### AI Integration
- **Natural Language Commands**: Control devices using plain English
- **Smart Automation**: AI-powered device control suggestions
- **Privacy-First**: Uses Gemini API while keeping personal data local

### Privacy & Security
- **Local-First Architecture**: All core operations run locally
- **SQLite Database**: Local data storage with no cloud dependency
- **MQTT Protocol**: Secure local network communication
- **Real-time Monitoring**: Live security event notifications

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Flask Server   │    │  MQTT Broker    │
│                 │◄──►│                  │◄──►│  (Mosquitto)    │
│  - Dashboard    │    │  - API Routes    │    │                 │
│  - Device UI    │    │  - SocketIO      │    │                 │
│  - AI Commands  │    │  - Database      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        ▲
                                ▼                        │
                       ┌──────────────────┐              │
                       │   Gemini AI API  │              │
                       │                  │              │
                       │  - NL Processing │              │
                       │  - Command Parse │              │
                       └──────────────────┘              │
                                                         │
                                               ┌─────────▼──────────┐
                                               │    ESP32 Devices   │
                                               │                    │
                                               │  - Relay Control   │
                                               │  - Sensor Reading  │
                                               │  - Status Reports  │
                                               └────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Mosquitto MQTT Broker
- Google Gemini API Key

### Installation

1. **Clone and Setup**
   ```bash
   git clone <repository>
   cd smart-home-automation
   pip install -r requirements.txt
   ```

2. **Install MQTT Broker**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install mosquitto mosquitto-clients
   sudo systemctl start mosquitto
   sudo systemctl enable mosquitto

   # macOS
   brew install mosquitto
   brew services start mosquitto

   # Or run locally
   mosquitto -v
   ```

3. **Configure Environment**
   ```bash
   cp env.example .env
   # Edit .env and add your Gemini API key
   ```

4. **Run the Application**
   ```bash
   python main.py
   ```

5. **Access Dashboard**
   Open http://localhost:5000 in your browser

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Required: Get from https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_api_key_here

# Optional MQTT settings
MQTT_BROKER=localhost
MQTT_PORT=1883
```

### Device Configuration

The system comes with pre-configured sample devices:
- Living Room Light
- Living Room Fan  
- Bedroom Light
- Bedroom AC
- Kitchen Light
- Entrance Motion Sensor

You can modify these in the `init_database()` function in `main.py`.

## 📱 Usage

### Web Dashboard

1. **Device Control**
   - Click on device cards to open control modal
   - Use sliders and buttons to control device settings
   - Filter devices by room using the room filter buttons

2. **AI Commands**
   - Type natural language commands like:
     - "Turn on living room lights"
     - "Set bedroom AC to 22 degrees"
     - "Turn off all lights"
   - The AI will parse commands and execute appropriate actions

3. **Energy Monitoring**
   - View real-time energy consumption
   - Track average and peak power usage by device

4. **Security Events**
   - Monitor motion sensor alerts
   - View security event history
   - Real-time notifications for motion detection

### MQTT Commands

Send commands directly to devices via MQTT:

```bash
# Turn on a light
mosquitto_pub -t "smarthome/living_room_light/control" -m '{"power": "on", "brightness": 80}'

# Control fan speed
mosquitto_pub -t "smarthome/living_room_fan/control" -m '{"power": "on", "speed": 3}'

# Set AC temperature
mosquitto_pub -t "smarthome/bedroom_ac/control" -m '{"power": "on", "temperature": 24, "mode": "cool"}'

# Simulate motion detection
mosquitto_pub -t "smarthome/motion_sensor_entrance/sensor" -m '{"motion_detected": true}'
```

## 🔌 ESP32 Integration

### MQTT Topic Structure

```
smarthome/{device_id}/control    # Send commands to devices
smarthome/{device_id}/status     # Device status updates
smarthome/{device_id}/sensor     # Sensor data
smarthome/{device_id}/energy     # Energy consumption data
```

### Example ESP32 Code Snippet

```cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* mqtt_server = "192.168.1.100";  // Your hub IP
const char* device_id = "living_room_light";

void callback(char* topic, byte* payload, unsigned int length) {
    // Parse JSON command and control relay
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, payload, length);
    
    if (doc["power"] == "on") {
        digitalWrite(RELAY_PIN, HIGH);
        publishStatus("on");
    }
}

void publishStatus(String status) {
    String topic = "smarthome/" + String(device_id) + "/status";
    String payload = "{\"status\":\"" + status + "\"}";
    client.publish(topic.c_str(), payload.c_str());
}
```

## 🎯 API Endpoints

### Device Management
- `GET /api/devices` - List all devices
- `POST /api/device/{id}/control` - Send command to device

### Monitoring
- `GET /api/energy/summary` - Energy consumption summary
- `GET /api/security/events` - Recent security events

### AI Integration
- `POST /api/ai/command` - Process natural language command

## 🛠️ Development

### Project Structure
```
smart-home-automation/
├── main.py                 # Main Flask application
├── requirements.txt        # Python dependencies
├── env.example            # Environment variables template
├── templates/
│   └── index.html         # Web dashboard
├── static/
│   ├── css/
│   │   └── style.css      # Styling
│   └── js/
│       └── app.js         # Frontend JavaScript
└── README.md
```

### Adding New Device Types

1. **Update Database Schema** (in `init_database()`)
2. **Add Device Controls** (in `static/js/app.js`)
3. **Update Device Icons** (in `getDeviceIcon()`)
4. **Add MQTT Handlers** (in message processing functions)

### Extending AI Commands

Modify the prompt in the `/api/ai/command` endpoint to support new command types and device interactions.

## 🔐 Security Considerations

- **Network Security**: Run on isolated IoT network
- **MQTT Security**: Consider enabling MQTT authentication
- **API Security**: Add authentication for production use
- **Data Privacy**: All personal data stays local
- **Regular Updates**: Keep dependencies updated

## 🏃‍♂️ Production Deployment

### Using systemd (Linux)

1. **Create Service File**
   ```bash
   sudo nano /etc/systemd/system/smarthome.service
   ```

2. **Service Configuration**
   ```ini
   [Unit]
   Description=Smart Home Automation System
   After=network.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/smart-home-automation
   ExecStart=/usr/bin/python3 main.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and Start**
   ```bash
   sudo systemctl enable smarthome
   sudo systemctl start smarthome
   ```

### Using Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "main.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **MQTT Connection Failed**
   - Ensure Mosquitto is running: `sudo systemctl status mosquitto`
   - Check firewall settings
   - Verify broker IP address

2. **Gemini API Errors**
   - Verify API key is correct
   - Check API quotas and limits
   - Ensure internet connectivity

3. **Database Issues**
   - Delete `smart_home.db` to reset database
   - Check file permissions

4. **WebSocket Connection Issues**
   - Check browser console for errors
   - Verify Flask-SocketIO installation
   - Try refreshing the page

### Support

For issues and questions:
- Check the GitHub issues page
- Review the troubleshooting section
- Create a new issue with detailed information

---

**Happy Home Automation! 🏠✨** 