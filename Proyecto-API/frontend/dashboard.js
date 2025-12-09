// Configuración MQTT
const MQTT_CONFIG = {
    brokerUrl: 'ws://localhost:9001', // WebSocket para MQTT
    topics: {
        temperature: 'sensors/temperature',
        rotation: 'sensors/rotation'
    }
};

// Variables globales
let mqttClient = null;
let temperatureData = [];
let rotationData = [];
let dailyRotationCount = 0;
let temperatureChart = null;
let rotationChart = null;
let lastTemperature = null;

// Elementos DOM
const elements = {
    temperatureValue: document.getElementById('temperatureValue'),
    rotationCount: document.getElementById('rotationCount'),
    rotationToday: document.getElementById('rotationToday'),
    tempTimestamp: document.getElementById('tempTimestamp'),
    rotationTimestamp: document.getElementById('rotationTimestamp'),
    mqttStatus: document.getElementById('mqttStatus'),
    piStatus: document.getElementById('piStatus'),
    brokerStatus: document.getElementById('brokerStatus'),
    lastUpdate: document.getElementById('lastUpdate'),
    brokerAddress: document.getElementById('brokerAddress'),
    eventsList: document.getElementById('eventsList'),
    refreshBtn: document.getElementById('refreshBtn'),
    logoutBtn: document.getElementById('logoutBtn'),
    tempTrend: document.getElementById('tempTrend'),
    trendUp: document.querySelector('.trend-up'),
    trendDown: document.querySelector('.trend-down')
};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    setupEventListeners();
    connectToMQTT();
    updateBrokerAddress();
    addEvent('Sistema de dashboard inicializado', 'info');
});

// Configurar listeners de eventos
function setupEventListeners() {
    elements.refreshBtn.addEventListener('click', refreshData);
    elements.logoutBtn.addEventListener('click', logout);
    
    // Botones de rango de tiempo
    document.querySelectorAll('.time-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            updateChartRange(this.dataset.range);
        });
    });
}

// Conectar al broker MQTT
async function connectToMQTT() {
    try {
        updateStatus('mqttStatus', 'connecting', 'Conectando...');
        
        // Usando WebSocket para MQTT (puedes cambiar a MQTT.js si prefieres)
        mqttClient = new Paho.MQTT.Client(
            MQTT_CONFIG.brokerUrl.replace('ws://', '').split(':')[0],
            parseInt(MQTT_CONFIG.brokerUrl.split(':')[2]),
            "dashboard_" + Math.random().toString(16).substr(2, 8)
        );

        mqttClient.onConnectionLost = onConnectionLost;
        mqttClient.onMessageArrived = onMessageArrived;

        mqttClient.connect({
            onSuccess: onConnect,
            onFailure: onConnectFailure,
            useSSL: false
        });

    } catch (error) {
        console.error('Error al conectar MQTT:', error);
        updateStatus('mqttStatus', 'disconnected', 'Error de conexión');
        addEvent(`Error MQTT: ${error.message}`, 'error');
    }
}

// Callbacks MQTT
function onConnect() {
    updateStatus('mqttStatus', 'connected', 'Conectado');
    updateStatus('brokerStatus', 'online', 'Online');
    addEvent('Conectado al broker MQTT', 'success');
    
    // Suscribirse a los tópicos
    Object.values(MQTT_CONFIG.topics).forEach(topic => {
        mqttClient.subscribe(topic);
        console.log(`Suscrito a: ${topic}`);
    });
}

function onConnectFailure(error) {
    console.error('Conexión MQTT fallida:', error);
    updateStatus('mqttStatus', 'disconnected', 'Desconectado');
    updateStatus('brokerStatus', 'offline', 'Offline');
    addEvent(`Falló conexión MQTT: ${error.errorMessage}`, 'error');
    
    // Reintentar conexión después de 5 segundos
    setTimeout(connectToMQTT, 5000);
}

function onConnectionLost(response) {
    if (response.errorCode !== 0) {
        console.error('Conexión MQTT perdida:', response.errorMessage);
        updateStatus('mqttStatus', 'disconnected', 'Desconectado');
        addEvent('Conexión MQTT perdida', 'error');
    }
}

function onMessageArrived(message) {
    const topic = message.destinationName;
    const payload = message.payloadString;
    const timestamp = new Date().toLocaleTimeString();
    
    console.log(`MQTT: ${topic} -> ${payload}`);
    
    if (topic === MQTT_CONFIG.topics.temperature) {
        updateTemperature(parseFloat(payload), timestamp);
    } else if (topic === MQTT_CONFIG.topics.rotation) {
        updateRotation(parseInt(payload), timestamp);
    }
    
    updateStatus('piStatus', 'online', 'Online');
    elements.lastUpdate.textContent = new Date().toLocaleTimeString();
}

// Actualizar temperatura
function updateTemperature(value, timestamp) {
    elements.temperatureValue.textContent = value.toFixed(1);
    elements.tempTimestamp.textContent = timestamp;
    
    // Detectar tendencia
    if (lastTemperature !== null) {
        const diff = value - lastTemperature;
        if (Math.abs(diff) > 0.1) {
            if (diff > 0) {
                elements.tempTrend.textContent = 'Subiendo';
                elements.trendUp.classList.remove('hidden');
                elements.trendDown.classList.add('hidden');
            } else {
                elements.tempTrend.textContent = 'Bajando';
                elements.trendUp.classList.add('hidden');
                elements.trendDown.classList.remove('hidden');
            }
        } else {
            elements.tempTrend.textContent = 'Estable';
            elements.trendUp.classList.add('hidden');
            elements.trendDown.classList.add('hidden');
        }
    }
    lastTemperature = value;
    
    // Agregar al historial
    temperatureData.push({
        time: new Date(),
        value: value
    });
    
    // Mantener solo últimas 100 lecturas
    if (temperatureData.length > 100) {
        temperatureData.shift();
    }
    
    // Actualizar gráfico
    updateTemperatureChart();
    
    addEvent(`Temperatura actualizada: ${value.toFixed(1)}°C`, 'info');
}

// Actualizar contador de giros
function updateRotation(count, timestamp) {
    elements.rotationCount.textContent = count;
    elements.rotationTimestamp.textContent = timestamp;
    
    // Incrementar contador diario (simulación)
    dailyRotationCount += 1;
    elements.rotationToday.textContent = dailyRotationCount;
    
    // Agregar al historial
    rotationData.push({
        time: new Date(),
        count: count,
        increment: 1
    });
    
    // Mantener solo últimas 50 lecturas
    if (rotationData.length > 50) {
        rotationData.shift();
    }
    
    // Actualizar gráfico
    updateRotationChart();
    
    addEvent(`Servomotor girado. Total hoy: ${dailyRotationCount}`, 'info');
}

// Inicializar gráficos
function initializeCharts() {
    // Gráfico de temperatura
    const tempCtx = document.getElementById('temperatureChart').getContext('2d');
    temperatureChart = new Chart(tempCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Temperatura (°C)',
                data: [],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    beginAtZero: false,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });

    // Gráfico de giros
    const rotationCtx = document.getElementById('rotationChart').getContext('2d');
    rotationChart = new Chart(rotationCtx, {
        type: 'bar',
        data: {
            labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
            datasets: [{
                label: 'Giros por hora',
                data: [0, 0, 0, 0, 0, 0],
                backgroundColor: 'rgba(118, 75, 162, 0.7)',
                borderColor: 'rgba(118, 75, 162, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });
}

// Actualizar gráfico de temperatura
function updateTemperatureChart() {
    if (temperatureData.length === 0) return;
    
    const labels = temperatureData.map(d => 
        d.time.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
    );
    const data = temperatureData.map(d => d.value);
    
    temperatureChart.data.labels = labels;
    temperatureChart.data.datasets[0].data = data;
    temperatureChart.update();
}

// Actualizar gráfico de giros
function updateRotationChart() {
    if (rotationData.length === 0) return;
    
    // Simular datos por hora para el ejemplo
    const hour = new Date().getHours();
    const hourIndex = Math.floor(hour / 4);
    
    rotationChart.data.datasets[0].data[hourIndex] = dailyRotationCount;
    rotationChart.update();
}

// Actualizar rango del gráfico
function updateChartRange(range) {
    console.log(`Cambiar rango a: ${range}`);
    // Aquí puedes implementar la lógica para cambiar el rango de datos
    addEvent(`Rango de gráfico cambiado a: ${range}`, 'info');
}

// Actualizar estado visual
function updateStatus(elementId, status, text) {
    const element = elements[elementId];
    if (!element) return;
    
    element.className = `status-indicator ${status}`;
    element.innerHTML = `<i class="fas fa-circle"></i> ${text}`;
}

// Añadir evento al historial
function addEvent(text, type = 'info') {
    const eventList = elements.eventsList;
    const timestamp = new Date().toLocaleTimeString();
    
    const eventItem = document.createElement('div');
    eventItem.className = 'event-item';
    
    let icon = 'info-circle';
    if (type === 'error') icon = 'exclamation-circle';
    if (type === 'success') icon = 'check-circle';
    
    eventItem.innerHTML = `
        <i class="fas fa-${icon} event-${type}"></i>
        <span class="event-text">${text}</span>
        <span class="event-time">${timestamp}</span>
    `;
    
    eventList.insertBefore(eventItem, eventList.firstChild);
    
    // Limitar a 10 eventos visibles
    if (eventList.children.length > 10) {
        eventList.removeChild(eventList.lastChild);
    }
}

// Actualizar dirección del broker
function updateBrokerAddress() {
    elements.brokerAddress.textContent = MQTT_CONFIG.brokerUrl;
}

// Refrescar datos
function refreshData() {
    elements.refreshBtn.classList.add('loading');
    addEvent('Actualizando datos...', 'info');
    
    setTimeout(() => {
        elements.refreshBtn.classList.remove('loading');
        addEvent('Datos actualizados manualmente', 'info');
    }, 1000);
}

// Cerrar sesión
function logout() {
    if (mqttClient && mqttClient.isConnected()) {
        mqttClient.disconnect();
    }
    
    addEvent('Sesión cerrada', 'info');
    
    // Redirigir al login después de 1 segundo
    setTimeout(() => {
        window.location.href = 'login.html';
    }, 1000);
}

// Simular datos si no hay conexión real (para pruebas)
function simulateData() {
    if (!mqttClient || !mqttClient.isConnected()) {
        const now = new Date().toLocaleTimeString();
        
        // Simular temperatura
        const temp = 20 + Math.random() * 10;
        updateTemperature(temp, now);
        
        // Simular giros cada 10 segundos
        if (Math.random() > 0.7) {
            updateRotation(dailyRotationCount + 1, now);
        }
    }
}

// Iniciar simulación si estamos en desarrollo
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    setInterval(simulateData, 5000);
}