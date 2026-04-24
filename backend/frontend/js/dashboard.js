// ============ DASHBOARD PAGE ============
async function loadDashboardData() {
    try {
        const token = localStorage.getItem('weather_ai_token');
        if (!token) {
            console.log('No token found, using default data');
            setDefaultDashboardData();
            setDefaultRecentActivity();
            return;
        }
        
        // Add timestamp to prevent caching
        const timestamp = Date.now();
        
        // Fetch dashboard stats with authentication
        const statsResponse = await fetch(`${API_BASE_URL}/api/analytics/dashboard-stats?_=${timestamp}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache'
            }
        });
        
        if (statsResponse.ok) {
            const stats = await statsResponse.json();
            console.log('Dashboard stats received:', stats);
            updateDashboardStats(stats);
        } else {
            console.error('Failed to load dashboard stats:', statsResponse.status);
            setDefaultDashboardData();
        }
        
        // Fetch recent activity with authentication
        const activityResponse = await fetch(`${API_BASE_URL}/api/analytics/recent-activity?limit=10&_=${timestamp}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache'
            }
        });
        
        if (activityResponse.ok) {
            const activity = await activityResponse.json();
            console.log('Recent activity received:', activity);
            updateRecentActivity(activity.activities || []);
        } else {
            console.error('Failed to load recent activity:', activityResponse.status);
            setDefaultRecentActivity();
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        setDefaultDashboardData();
        setDefaultRecentActivity();
    }
}

function updateDashboardStats(stats) {
    const statsContainer = document.getElementById('dashboard-stats');
    if (!statsContainer) {
        console.error('Dashboard stats container not found!');
        return;
    }
    
    const citiesCount = stats.cities_monitored || 5;
    const anomaliesCount = stats.anomalies_detected || 12;
    const accuracy = stats.model_accuracy || 94.5;
    const apiRequests = stats.api_requests ? stats.api_requests.toLocaleString() : '1,245';
    
    statsContainer.innerHTML = `
        <div class="stat-card fade-in-up">
            <div class="stat-header">
                <div class="stat-icon"><i class="fas fa-globe-americas"></i></div>
                <div class="stat-trend ${citiesCount > 0 ? 'positive' : ''}">
                    <i class="fas fa-arrow-up"></i><span>+${Math.min(citiesCount, 12)}%</span>
                </div>
            </div>
            <div class="stat-value">${citiesCount}</div>
            <div class="stat-label">Cities Monitored</div>
            <div class="stat-subtext">Worldwide coverage</div>
        </div>

        <div class="stat-card warning fade-in-up">
            <div class="stat-header">
                <div class="stat-icon"><i class="fas fa-exclamation-triangle"></i></div>
                <div class="stat-trend ${anomaliesCount > 0 ? 'negative' : ''}">
                    <i class="fas fa-arrow-down"></i><span>-${Math.min(anomaliesCount, 3)}%</span>
                </div>
            </div>
            <div class="stat-value">${anomaliesCount}</div>
            <div class="stat-label">Anomalies Detected</div>
            <div class="stat-subtext">Last 24 hours</div>
        </div>

        <div class="stat-card success fade-in-up">
            <div class="stat-header">
                <div class="stat-icon"><i class="fas fa-brain"></i></div>
                <div class="stat-trend positive"><i class="fas fa-arrow-up"></i><span>+2.3%</span></div>
            </div>
            <div class="stat-value">${accuracy}%</div>
            <div class="stat-label">Model Accuracy</div>
            <div class="stat-subtext">Continual learning</div>
        </div>

        <div class="stat-card info fade-in-up">
            <div class="stat-header">
                <div class="stat-icon"><i class="fas fa-server"></i></div>
                <div class="stat-trend positive">
                    <i class="fas fa-arrow-up"></i><span>+${Math.min(parseInt(apiRequests.replace(',', '')) / 100, 45)}%</span>
                </div>
            </div>
            <div class="stat-value">${apiRequests}</div>
            <div class="stat-label">API Requests</div>
            <div class="stat-subtext">Real-time processing</div>
        </div>
    `;
    
    // Also update the API accuracy in the sidebar if it exists
    const apiAccuracy = document.getElementById('api-accuracy');
    if (apiAccuracy) apiAccuracy.textContent = accuracy + '% Model Accuracy';
    
    // Update anomaly badge if it exists
    const anomalyBadge = document.getElementById('anomaly-badge');
    if (anomalyBadge) anomalyBadge.textContent = anomaliesCount;
    
    console.log('✅ Dashboard stats updated:', stats);
}

function updateRecentActivity(activities) {
    const tableBody = document.getElementById('activity-table-body');
    if (!tableBody) return;
    
    if (activities.length === 0) {
        setDefaultRecentActivity();
        return;
    }
    
    tableBody.innerHTML = activities.map(activity => `
        <tr>
            <td><div class="time-ago"><i class="far fa-clock"></i> ${formatTimestamp(activity.timestamp) || 'Just now'}</div></td>
            <td><strong>${activity.city || 'Unknown'}</strong></td>
            <td>${activity.activity_type || 'Activity'}</td>
            <td><span class="activity-badge ${getBadgeClass(activity)}">${activity.status || 'Unknown'}</span></td>
            <td>${activity.is_anomaly ? 
                '<i class="fas fa-exclamation-triangle text-warning"></i> Anomaly detected' : 
                '<i class="fas fa-check-circle text-success"></i> Normal conditions'}
            </td>
        </tr>
    `).join('');
}

function setDefaultDashboardData() {
    const statsContainer = document.getElementById('dashboard-stats');
    if (!statsContainer) return;
    
    statsContainer.innerHTML = `
        <div class="stat-card fade-in-up">
            <div class="stat-header">
                <div class="stat-icon"><i class="fas fa-globe-americas"></i></div>
                <div class="stat-trend positive"><i class="fas fa-arrow-up"></i><span>+12%</span></div>
            </div>
            <div class="stat-value">5</div>
            <div class="stat-label">Cities Monitored</div>
            <div class="stat-subtext">Worldwide coverage</div>
        </div>
        <div class="stat-card warning fade-in-up">
            <div class="stat-header">
                <div class="stat-icon"><i class="fas fa-exclamation-triangle"></i></div>
                <div class="stat-trend negative"><i class="fas fa-arrow-down"></i><span>-3%</span></div>
            </div>
            <div class="stat-value">12</div>
            <div class="stat-label">Anomalies Detected</div>
            <div class="stat-subtext">Last 24 hours</div>
        </div>
        <div class="stat-card success fade-in-up">
            <div class="stat-header">
                <div class="stat-icon"><i class="fas fa-brain"></i></div>
                <div class="stat-trend positive"><i class="fas fa-arrow-up"></i><span>+2.3%</span></div>
            </div>
            <div class="stat-value">94.5%</div>
            <div class="stat-label">Model Accuracy</div>
            <div class="stat-subtext">Continual learning</div>
        </div>
        <div class="stat-card info fade-in-up">
            <div class="stat-header">
                <div class="stat-icon"><i class="fas fa-server"></i></div>
                <div class="stat-trend positive"><i class="fas fa-arrow-up"></i><span>+45%</span></div>
            </div>
            <div class="stat-value">1,245</div>
            <div class="stat-label">API Requests</div>
            <div class="stat-subtext">Real-time processing</div>
        </div>
    `;
}

function setDefaultRecentActivity() {
    const tableBody = document.getElementById('activity-table-body');
    if (!tableBody) return;
    
    tableBody.innerHTML = `
        <tr>
            <td><div class="time-ago"><i class="far fa-clock"></i>5 mins ago</div></td>
            <td><strong>London</strong></td>
            <td>Weather Check</td>
            <td><span class="activity-badge badge-success">Normal</span></td>
            <td><i class="fas fa-check-circle text-success"></i> Temperature: 15°C</td>
        </tr>
        <tr>
            <td><div class="time-ago"><i class="far fa-clock"></i>12 mins ago</div></td>
            <td><strong>Dubai</strong></td>
            <td>Anomaly Detection</td>
            <td><span class="activity-badge badge-warning">Anomaly</span></td>
            <td><i class="fas fa-exclamation-triangle text-warning"></i> Unusual temperature spike</td>
        </tr>
        <tr>
            <td><div class="time-ago"><i class="far fa-clock"></i>30 mins ago</div></td>
            <td><strong>New York</strong></td>
            <td>Weather Check</td>
            <td><span class="activity-badge badge-success">Normal</span></td>
            <td><i class="fas fa-check-circle text-success"></i> Clear sky, 22°C</td>
        </tr>
        <tr>
            <td><div class="time-ago"><i class="far fa-clock"></i>1 hour ago</div></td>
            <td><strong>Tokyo</strong></td>
            <td>Anomaly Detection</td>
            <td><span class="activity-badge badge-success">Normal</span></td>
            <td><i class="fas fa-check-circle text-success"></i> Standard conditions</td>
        </tr>
    `;
}

function formatTimestamp(timestamp) {
    if (!timestamp) return null;
    try {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} mins ago`;
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)} hours ago`;
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
        return timestamp;
    }
}

function getBadgeClass(activity) {
    if (activity.is_anomaly) return 'badge-warning';
    if (activity.status === 'Normal' || activity.status === 'Completed') return 'badge-success';
    if (activity.status === 'Error' || activity.status === 'Failed') return 'badge-danger';
    return 'badge-primary';
}