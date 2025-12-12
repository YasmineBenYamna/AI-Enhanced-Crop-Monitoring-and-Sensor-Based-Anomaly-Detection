checkAuth();

// Get plot ID from URL (?id=1)
const urlParams = new URLSearchParams(window.location.search);
const plotId = urlParams.get('id');

let tempChart, humidityChart, moistureChart;

// Load data when page opens
document.addEventListener('DOMContentLoaded', async () => {
    await loadData('24h');
});

async function loadData(range) {
    try {
        // Fetch sensor readings from Django
        const readings = await apiGet(`/sensor-readings/?plot=${plotId}&range=${range}`);
        
        // Separate by sensor type
        const temps = readings.filter(r => r.sensor_type === 'temperature');
        const humidity = readings.filter(r => r.sensor_type === 'humidity');
        const moisture = readings.filter(r => r.sensor_type === 'moisture');
        
        // Get timestamps
        const timestamps = temps.map(r => new Date(r.timestamp).toLocaleTimeString());
        
        // Create charts
        createChart('tempChart', timestamps, temps.map(r => r.value), 'Temperature', '#ff6b6b');
        createChart('humidityChart', timestamps, humidity.map(r => r.value), 'Humidity', '#4dabf7');
        createChart('moistureChart', timestamps, moisture.map(r => r.value), 'Moisture', '#51cf66');
        
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

function createChart(canvasId, labels, data, label, color) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Destroy old chart if exists
    if (canvasId === 'tempChart' && tempChart) tempChart.destroy();
    if (canvasId === 'humidityChart' && humidityChart) humidityChart.destroy();
    if (canvasId === 'moistureChart' && moistureChart) moistureChart.destroy();
    
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: color,
                backgroundColor: color + '30',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
    
    // Save reference
    if (canvasId === 'tempChart') tempChart = chart;
    if (canvasId === 'humidityChart') humidityChart = chart;
    if (canvasId === 'moistureChart') moistureChart = chart;
}