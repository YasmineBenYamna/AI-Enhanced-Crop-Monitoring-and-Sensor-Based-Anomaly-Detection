checkAuth();

// Load alerts when page opens
document.addEventListener('DOMContentLoaded', async () => {
    await loadAlerts('active');
});

async function loadAlerts(filter) {
    try {
        let endpoint = '/alerts/';
        if (filter === 'active') endpoint += '?resolved=false';
        if (filter === 'resolved') endpoint += '?resolved=true';
        
        const alerts = await apiGet(endpoint);
        renderAlerts(alerts);
    } catch (error) {
        console.error('Error:', error);
    }
}

function renderAlerts(alerts) {
    const alertsList = document.getElementById('alertsList');
    
    if (alerts.length === 0) {
        alertsList.innerHTML = '<p>No alerts found.</p>';
        return;
    }
    
    alertsList.innerHTML = alerts.map(alert => `
        <div class="alert-card severity-${alert.severity}">
            <div class="alert-header">
                <span class="severity">${alert.severity}</span>
                <h3>${alert.anomaly_type}</h3>
                <span class="time">${new Date(alert.detected_at).toLocaleString()}</span>
            </div>
            
            <div class="alert-info">
                <p><strong>Plot:</strong> ${alert.plot_name}</p>
                <p><strong>Sensor:</strong> ${alert.sensor_type}</p>
                <p><strong>Value:</strong> ${alert.value}</p>
            </div>
            
            <button onclick="showRecommendations(${alert.id})">
                Show AI Recommendations
            </button>
            
            <div id="rec-${alert.id}" class="recommendations" style="display:none;">
                <!-- Loaded by JavaScript -->
            </div>
            
            ${!alert.resolved ? `
                <button onclick="resolveAlert(${alert.id})">
                    Mark as Resolved
                </button>
            ` : '<span class="resolved">✅ Resolved</span>'}
        </div>
    `).join('');
}

async function showRecommendations(alertId) {
    const recDiv = document.getElementById(`rec-${alertId}`);
    
    if (recDiv.style.display === 'none') {
        try {
            // THIS IS WHERE YOU USE YOUR AI AGENT FROM DAYS 1-2!
            const recommendations = await apiGet(`/ai-agent/recommendations/${alertId}/`);
            
            recDiv.innerHTML = recommendations.map(rec => `
                <div class="recommendation">
                    <h4>💡 ${rec.action_type}</h4>
                    <p>${rec.explanation}</p>
                    <span class="confidence">Confidence: ${rec.confidence}%</span>
                </div>
            `).join('');
            
            recDiv.style.display = 'block';
        } catch (error) {
            alert('Failed to load recommendations');
        }
    } else {
        recDiv.style.display = 'none';
    }
}

async function resolveAlert(alertId) {
    try {
        await apiPost(`/alerts/${alertId}/resolve/`, {});
        alert('Alert resolved!');
        await loadAlerts('active');
    } catch (error) {
        alert('Failed to resolve alert');
    }
}