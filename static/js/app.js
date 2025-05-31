// Smart Home Hub - Frontend JavaScript
class SmartHomeHub {
    constructor() {
        this.socket = null;
        this.devices = {};
        this.currentFilter = 'all';
        this.init();
    }

    init() {
        this.initSocketIO();
        this.initEventListeners();
        this.loadDevices();
        this.loadEnergyData();
        this.loadSecurityEvents();
        
        // Refresh data every 30 seconds
        setInterval(() => {
            this.loadEnergyData();
            this.loadSecurityEvents();
        }, 30000);
    }

    initSocketIO() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to Smart Home Hub');
            document.getElementById('client-count').textContent = 'Connected';
            document.getElementById('client-count').className = 'status online';
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from Smart Home Hub');
            document.getElementById('client-count').textContent = 'Disconnected';
            document.getElementById('client-count').className = 'status offline';
        });

        this.socket.on('mqtt_status', (data) => {
            const mqttStatus = document.getElementById('mqtt-status');
            if (data.connected) {
                mqttStatus.textContent = 'MQTT: Connected';
                mqttStatus.className = 'status online';
            } else {
                mqttStatus.textContent = 'MQTT: Disconnected';
                mqttStatus.className = 'status offline';
            }
        });

        this.socket.on('device_update', (data) => {
            this.updateDeviceStatus(data.device_id, data.data);
        });

        this.socket.on('security_alert', (data) => {
            this.showSecurityAlert(data);
            this.loadSecurityEvents(); // Refresh security events
        });
    }

    initEventListeners() {
        // AI Command
        document.getElementById('ai-submit').addEventListener('click', () => {
            this.sendAICommand();
        });

        document.getElementById('ai-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendAICommand();
            }
        });

        // Room Filter
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.filterDevices(e.target.dataset.room);
                
                // Update active filter button
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });

        // Modal
        document.querySelector('.close').addEventListener('click', () => {
            document.getElementById('device-modal').style.display = 'none';
        });

        window.addEventListener('click', (e) => {
            const modal = document.getElementById('device-modal');
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    }

    async loadDevices() {
        try {
            const response = await fetch('/api/devices');
            const devices = await response.json();
            
            this.devices = {};
            devices.forEach(device => {
                this.devices[device.id] = device;
            });
            
            this.renderDevices();
        } catch (error) {
            console.error('Error loading devices:', error);
        }
    }

    renderDevices() {
        const grid = document.getElementById('devices-grid');
        grid.innerHTML = '';

        Object.values(this.devices).forEach(device => {
            if (this.currentFilter === 'all' || device.room === this.currentFilter) {
                const card = this.createDeviceCard(device);
                grid.appendChild(card);
            }
        });
    }

    createDeviceCard(device) {
        const card = document.createElement('div');
        card.className = `device-card ${device.status}`;
        card.dataset.deviceId = device.id;

        const typeIcon = this.getDeviceIcon(device.type);
        const roomName = device.room.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());

        card.innerHTML = `
            <div class="device-header">
                <span class="device-name">${typeIcon} ${device.name}</span>
                <span class="device-status ${device.status}">${device.status}</span>
            </div>
            <div class="device-type">${device.type.replace('_', ' ').toUpperCase()}</div>
            <div class="device-room">📍 ${roomName}</div>
        `;

        card.addEventListener('click', () => {
            this.openDeviceModal(device);
        });

        return card;
    }

    getDeviceIcon(type) {
        const icons = {
            'light': '💡',
            'fan': '🌀',
            'ac': '❄️',
            'motion_sensor': '👁️'
        };
        return icons[type] || '🔌';
    }

    openDeviceModal(device) {
        const modal = document.getElementById('device-modal');
        const deviceName = document.getElementById('modal-device-name');
        const controls = document.getElementById('modal-controls');

        deviceName.textContent = device.name;
        controls.innerHTML = this.createDeviceControls(device);

        modal.style.display = 'block';
    }

    createDeviceControls(device) {
        let controls = '';

        switch (device.type) {
            case 'light':
                controls = `
                    <div class="control-group">
                        <label class="control-label">Power</label>
                        <button class="control-button" onclick="smartHome.controlDevice('${device.id}', {power: 'on'})">ON</button>
                        <button class="control-button" onclick="smartHome.controlDevice('${device.id}', {power: 'off'})">OFF</button>
                    </div>
                    <div class="control-group">
                        <label class="control-label">Brightness: <span id="brightness-value">100</span>%</label>
                        <input type="range" class="control-slider" min="0" max="100" value="100" 
                               oninput="document.getElementById('brightness-value').textContent = this.value"
                               onchange="smartHome.controlDevice('${device.id}', {brightness: parseInt(this.value)})">
                    </div>
                `;
                break;

            case 'fan':
                controls = `
                    <div class="control-group">
                        <label class="control-label">Power</label>
                        <button class="control-button" onclick="smartHome.controlDevice('${device.id}', {power: 'on'})">ON</button>
                        <button class="control-button" onclick="smartHome.controlDevice('${device.id}', {power: 'off'})">OFF</button>
                    </div>
                    <div class="control-group">
                        <label class="control-label">Speed: <span id="speed-value">0</span></label>
                        <input type="range" class="control-slider" min="0" max="5" value="0" 
                               oninput="document.getElementById('speed-value').textContent = this.value"
                               onchange="smartHome.controlDevice('${device.id}', {speed: parseInt(this.value)})">
                    </div>
                `;
                break;

            case 'ac':
                controls = `
                    <div class="control-group">
                        <label class="control-label">Power</label>
                        <button class="control-button" onclick="smartHome.controlDevice('${device.id}', {power: 'on'})">ON</button>
                        <button class="control-button" onclick="smartHome.controlDevice('${device.id}', {power: 'off'})">OFF</button>
                    </div>
                    <div class="control-group">
                        <label class="control-label">Temperature: <span id="temp-value">24</span>°C</label>
                        <input type="range" class="control-slider" min="16" max="30" value="24" 
                               oninput="document.getElementById('temp-value').textContent = this.value"
                               onchange="smartHome.controlDevice('${device.id}', {temperature: parseInt(this.value)})">
                    </div>
                    <div class="control-group">
                        <label class="control-label">Mode</label>
                        <button class="control-button" onclick="smartHome.controlDevice('${device.id}', {mode: 'cool'})">Cool</button>
                        <button class="control-button" onclick="smartHome.controlDevice('${device.id}', {mode: 'heat'})">Heat</button>
                        <button class="control-button" onclick="smartHome.controlDevice('${device.id}', {mode: 'auto'})">Auto</button>
                    </div>
                `;
                break;

            case 'motion_sensor':
                controls = `
                    <div class="control-group">
                        <p>Motion sensor is read-only. Check security events for motion detection data.</p>
                    </div>
                `;
                break;
        }

        return controls;
    }

    async controlDevice(deviceId, command) {
        try {
            const response = await fetch(`/api/device/${deviceId}/control`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(command)
            });

            const result = await response.json();
            if (result.success) {
                console.log('Device command sent successfully');
                // Close modal after successful command
                document.getElementById('device-modal').style.display = 'none';
            } else {
                alert('Error controlling device: ' + result.error);
            }
        } catch (error) {
            console.error('Error controlling device:', error);
            alert('Error controlling device');
        }
    }

    async sendAICommand() {
        const input = document.getElementById('ai-input');
        const response = document.getElementById('ai-response');
        const command = input.value.trim();

        if (!command) return;

        // Show loading state
        response.innerHTML = '<div class="loading">Processing command...</div>';
        response.classList.add('show');

        try {
            const apiResponse = await fetch('/api/ai/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ command })
            });

            const result = await apiResponse.json();
            
            if (result.success) {
                response.innerHTML = `
                    <strong>AI Response:</strong> ${result.response}
                    ${result.actions.length > 0 ? `<br><strong>Actions executed:</strong> ${result.actions.length}` : ''}
                `;
                input.value = '';
            } else {
                response.innerHTML = `<strong>Error:</strong> ${result.error}`;
            }
        } catch (error) {
            console.error('Error sending AI command:', error);
            response.innerHTML = '<strong>Error:</strong> Failed to process command';
        }
    }

    async loadEnergyData() {
        try {
            const response = await fetch('/api/energy/summary');
            const energyData = await response.json();
            
            const container = document.getElementById('energy-summary');
            
            if (energyData.length === 0) {
                container.innerHTML = '<p>No energy data available</p>';
                return;
            }

            container.innerHTML = energyData.map(item => `
                <div class="energy-item">
                    <div class="energy-device">${item.device}</div>
                    <div class="energy-stats">
                        <span>Avg: ${item.avg_power}W</span>
                        <span>Peak: ${item.peak_power}W</span>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error loading energy data:', error);
            document.getElementById('energy-summary').innerHTML = '<p>Error loading energy data</p>';
        }
    }

    async loadSecurityEvents() {
        try {
            const response = await fetch('/api/security/events');
            const events = await response.json();
            
            const container = document.getElementById('security-events');
            
            if (events.length === 0) {
                container.innerHTML = '<p>No security events</p>';
                return;
            }

            container.innerHTML = events.map(event => `
                <div class="security-event">
                    <div class="event-header">
                        <span class="event-type">${event.event_type.replace('_', ' ').toUpperCase()}</span>
                        <span class="event-time">${new Date(event.timestamp).toLocaleString()}</span>
                    </div>
                    <div class="event-description">
                        ${event.description} (${event.sensor_id})
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error loading security events:', error);
            document.getElementById('security-events').innerHTML = '<p>Error loading security events</p>';
        }
    }

    filterDevices(room) {
        this.currentFilter = room;
        this.renderDevices();
    }

    updateDeviceStatus(deviceId, data) {
        if (this.devices[deviceId]) {
            this.devices[deviceId].status = data.status || 'online';
            this.renderDevices();
        }
    }

    showSecurityAlert(data) {
        // Create a temporary alert notification
        const alert = document.createElement('div');
        alert.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #fed7d7;
            color: #c53030;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #f56565;
            z-index: 2000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            max-width: 300px;
        `;
        alert.innerHTML = `
            <strong>🚨 Security Alert</strong><br>
            Motion detected at ${data.sensor_id}<br>
            <small>${new Date(data.timestamp).toLocaleString()}</small>
        `;

        document.body.appendChild(alert);

        // Remove alert after 5 seconds
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
}

// Initialize the Smart Home Hub when page loads
let smartHome;
document.addEventListener('DOMContentLoaded', () => {
    smartHome = new SmartHomeHub();
}); 