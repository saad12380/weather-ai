// ============ WEATHER CHECK PAGE ============
function setupWeatherPage() {
    const getWeatherBtn = document.getElementById('get-weather-btn');
    if (getWeatherBtn) getWeatherBtn.addEventListener('click', getWeatherData);
    
    const cityInput = document.getElementById('weather-city-input');
    const countryInput = document.getElementById('weather-country-input');
    
    if (cityInput) cityInput.addEventListener('keypress', function(e) { if (e.key === 'Enter') getWeatherData(); });
    if (countryInput) countryInput.addEventListener('keypress', function(e) { if (e.key === 'Enter') getWeatherData(); });
    
    loadUserWeatherHistory();
    loadPopularCities();
    loadUserHistoryList(); // Add this line
}

async function loadUserWeatherHistory() {
    try {
        const token = localStorage.getItem('weather_ai_token');
        if (!token) return;
        
        const response = await fetch(`${API_BASE_URL}/api/analytics/recent-activity?limit=5`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Cache-Control': 'no-cache'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const weatherActivities = (data.activities || [])
                .filter(a => a.activity_type === 'Weather Check')
                .slice(0, 5);
            
            updateRecentWeatherChecks(weatherActivities);
        }
    } catch (error) {
        console.error('Error loading weather history:', error);
    }
}

function updateRecentWeatherChecks(activities) {
    const container = document.getElementById('recent-weather-checks');
    if (!container) return;
    
    if (activities.length === 0) {
        container.innerHTML = '<p class="text-muted">No recent weather checks</p>';
        return;
    }
    
    container.innerHTML = activities.map(activity => `
        <div class="recent-item" onclick="quickWeatherCheck('${activity.city}')">
            <i class="fas fa-map-marker-alt"></i>
            <span>${activity.city}</span>
            <small>${formatTimestamp(activity.timestamp)}</small>
        </div>
    `).join('');
}

function quickWeatherCheck(city) {
    document.getElementById('weather-city-input').value = city;
    getWeatherData();
}

async function loadPopularCities() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/cities/supported`);
        if (response.ok) {
            const data = await response.json();
            updatePopularCities(data.supported_cities || []);
        }
    } catch (error) {
        console.error('Error loading popular cities:', error);
        // Only use fallback if API completely fails
        updatePopularCities([
            "London, GB", "New York, US", "Tokyo, JP", "Dubai, AE",
            "Paris, FR", "Sydney, AU", "Berlin, DE", "Mumbai, IN"
        ]);
    }
}

function updatePopularCities(cities) {
    const container = document.getElementById('popular-cities-grid');
    if (!container) return;
    
    const popularCities = cities.slice(0, 8);
    
    container.innerHTML = popularCities.map(city => {
        const [cityName, countryCode] = city.split(', ');
        const iconMap = {
            'London': 'landmark', 'New York': 'building', 'Tokyo': 'torii-gate',
            'Dubai': 'mosque', 'Paris': 'eiffel-tower', 'Sydney': 'opera-house',
            'Berlin': 'landmark', 'Mumbai': 'landmark'
        };
        
        return `
            <button class="action-btn" data-quick-city="${cityName}" data-quick-country="${countryCode || ''}">
                <div class="action-icon"><i class="fas fa-${iconMap[cityName] || 'city'}"></i></div>
                <div class="action-info">
                    <h4>${cityName}</h4>
                    <p>${countryCode ? `Check weather in ${countryCode}` : 'Check weather'}</p>
                </div>
            </button>
        `;
    }).join('');
    
    document.querySelectorAll('.action-btn[data-quick-city]').forEach(btn => {
        btn.addEventListener('click', function() {
            const city = this.getAttribute('data-quick-city');
            const country = this.getAttribute('data-quick-country') || '';
            
            document.getElementById('weather-city-input').value = city;
            if (country) document.getElementById('weather-country-input').value = country;
            
            setTimeout(() => getWeatherData(), 300);
        });
    });
}

async function getWeatherData() {
    const cityInput = document.getElementById('weather-city-input');
    const countryInput = document.getElementById('weather-country-input');
    const getWeatherBtn = document.getElementById('get-weather-btn');
    
    const city = cityInput.value.trim();
    if (!city) {
        showAlert('Please enter a city name', 'error');
        return;
    }
    
    const originalText = getWeatherBtn.innerHTML;
    getWeatherBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    getWeatherBtn.disabled = true;
    
    try {
        const params = new URLSearchParams();
        params.append('city', city);
        if (countryInput.value.trim()) params.append('country', countryInput.value.trim());
        
        const token = localStorage.getItem('weather_ai_token');
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        
        const response = await fetch(`${API_BASE_URL}/api/weather/current?${params.toString()}`, { headers });
        
        if (response.ok) {
            const weatherData = await response.json();
            displayWeatherResult(weatherData);
            showAlert(`Weather data loaded for ${city}!`, 'success');
            loadDashboardData();
            loadUserWeatherHistory(); // Refresh recent history
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to fetch weather data');
        }
    } catch (error) {
        console.error('Error fetching weather:', error);
        showAlert(error.message || 'Failed to load weather data. Please try again.', 'error');
        // Only use fallback display for UI, don't save to database
        displayFallbackWeather(city, countryInput.value.trim());
    } finally {
        getWeatherBtn.innerHTML = '<i class="fas fa-search"></i> Get Weather Data';
        getWeatherBtn.disabled = false;
    }
}

function displayWeatherResult(weatherData) {
    const container = document.getElementById('weather-result-container');
    
    const weatherIcon = getWeatherIcon(weatherData.description || 'Clear');
    const feelsLike = weatherData.feels_like || weatherData.temperature;
    const visibility = weatherData.visibility ? `${(weatherData.visibility / 1000).toFixed(1)} km` : 'N/A';
    const clouds = weatherData.clouds || 'N/A';
    const source = weatherData.source || 'unknown';
    const isFallback = source === 'fallback';
    
    container.innerHTML = `
        <div class="weather-display-card fade-in-up">
            <div class="weather-content">
                <div class="weather-header">
                    <div class="location-info">
                        <h3>${weatherData.city}</h3>
                        <p>${weatherData.country || 'Unknown'}</p>
                        ${isFallback ? 
                            '<small style="color: #f59e0b;"><i class="fas fa-exclamation-triangle"></i> Using fallback data</small>' : 
                            '<small style="color: #10b981;"><i class="fas fa-check-circle"></i> Live data from OpenWeatherMap</small>'}
                    </div>
                    <div class="weather-condition">
                        <i class="${weatherIcon} weather-icon"></i>
                        <span>${weatherData.description || 'Unknown'}</span>
                    </div>
                </div>
                
                <div class="temperature-display">
                    <div class="temp-main">
                        <span>${Math.round(weatherData.temperature)}</span>
                        <span class="temp-unit">°C</span>
                    </div>
                    <p>Feels like <strong>${Math.round(feelsLike)}°C</strong></p>
                    ${weatherData.temp_min && weatherData.temp_max ? 
                        `<p>Min: ${Math.round(weatherData.temp_min)}°C | Max: ${Math.round(weatherData.temp_max)}°C</p>` : ''}
                </div>
                
                <div class="weather-grid">
                    <div class="weather-item"><i class="fas fa-tint"></i><span>${weatherData.humidity}%</span><small>Humidity</small></div>
                    <div class="weather-item"><i class="fas fa-wind"></i><span>${Math.round(weatherData.wind_speed)} km/h</span><small>Wind Speed</small></div>
                    <div class="weather-item"><i class="fas fa-compress-alt"></i><span>${weatherData.pressure} hPa</span><small>Pressure</small></div>
                    <div class="weather-item"><i class="fas fa-eye"></i><span>${visibility}</span><small>Visibility</small></div>
                    ${clouds !== 'N/A' ? `
                        <div class="weather-item"><i class="fas fa-cloud"></i><span>${clouds}%</span><small>Cloud Cover</small></div>
                    ` : ''}
                    <div class="weather-item"><i class="fas fa-database"></i><span>${isFallback ? 'Fallback' : 'Live'}</span><small>Data Source</small></div>
                </div>
                
                ${weatherData.coordinates ? 
                    `<div class="mt-3 text-center">
                        <small style="color: var(--text-muted);">
                            <i class="fas fa-map-marker-alt"></i>
                            Coordinates: ${weatherData.coordinates.lat.toFixed(4)}, ${weatherData.coordinates.lon.toFixed(4)}
                        </small>
                    </div>` : ''}
                    
                <div class="mt-4 text-center">
                    <small style="color: var(--text-muted);">
                        <i class="far fa-clock"></i>
                        Last updated: ${new Date().toLocaleTimeString()}
                    </small>
                </div>
            </div>
        </div>
    `;
    
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function displayFallbackWeather(city, country) {
    const container = document.getElementById('weather-result-container');
    
    const temp = Math.floor(Math.random() * 30) + 10;
    const humidity = Math.floor(Math.random() * 50) + 40;
    const wind = Math.floor(Math.random() * 20) + 5;
    const pressure = Math.floor(Math.random() * 40) + 1000;
    const conditions = ['Sunny', 'Cloudy', 'Partly Cloudy', 'Rainy', 'Clear'];
    const condition = conditions[Math.floor(Math.random() * conditions.length)];
    const weatherIcon = getWeatherIcon(condition);
    
    container.innerHTML = `
        <div class="weather-display-card fade-in-up">
            <div class="weather-content">
                <div class="weather-header">
                    <div class="location-info">
                        <h3>${city}</h3>
                        <p>${country || 'Unknown'}</p>
                        <small style="color: #f59e0b;"><i class="fas fa-exclamation-triangle"></i> Using fallback data (API unavailable)</small>
                    </div>
                    <div class="weather-condition">
                        <i class="${weatherIcon} weather-icon"></i>
                        <span>${condition}</span>
                    </div>
                </div>
                
                <div class="temperature-display">
                    <div class="temp-main"><span>${temp}</span><span class="temp-unit">°C</span></div>
                    <p>Feels like <strong>${temp + 2}°C</strong></p>
                </div>
                
                <div class="weather-grid">
                    <div class="weather-item"><i class="fas fa-tint"></i><span>${humidity}%</span><small>Humidity</small></div>
                    <div class="weather-item"><i class="fas fa-wind"></i><span>${wind} km/h</span><small>Wind Speed</small></div>
                    <div class="weather-item"><i class="fas fa-compress-alt"></i><span>${pressure} hPa</span><small>Pressure</small></div>
                    <div class="weather-item"><i class="fas fa-eye"></i><span>10 km</span><small>Visibility</small></div>
                    <div class="weather-item"><i class="fas fa-cloud"></i><span>${Math.floor(Math.random() * 100)}%</span><small>Cloud Cover</small></div>
                    <div class="weather-item"><i class="fas fa-database"></i><span>Fallback</span><small>Data Source</small></div>
                </div>
                
                <div class="mt-4 text-center">
                    <small style="color: var(--text-muted);">
                        <i class="fas fa-info-circle"></i>
                        Real-time data is temporarily unavailable. Showing simulated data.
                    </small>
                </div>
            </div>
        </div>
    `;
}

// ============ WEATHER HISTORY PAGE ============
function setupHistoryPage() {
    const loadHistoryBtn = document.getElementById('load-history-btn');
    if (loadHistoryBtn) loadHistoryBtn.addEventListener('click', loadWeatherHistory);
    
    const cityInput = document.getElementById('history-city-input');
    if (cityInput) cityInput.addEventListener('keypress', function(e) { if (e.key === 'Enter') loadWeatherHistory(); });
    
    loadUserHistoryList();
}

async function loadUserHistoryList() {
    try {
        const token = localStorage.getItem('weather_ai_token');
        if (!token) return;
        
        const response = await fetch(`${API_BASE_URL}/api/analytics/recent-activity?limit=20`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Cache-Control': 'no-cache'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const historyActivities = (data.activities || [])
                .filter(a => a.activity_type === 'Weather Check' || a.activity_type === 'Weather History')
                .slice(0, 10);
            
            updateRecentHistoryList(historyActivities);
        }
    } catch (error) {
        console.error('Error loading history list:', error);
    }
}

function updateRecentHistoryList(activities) {
    const container = document.getElementById('recent-history-list');
    if (!container) return;
    
    if (activities.length === 0) {
        container.innerHTML = '<p class="text-muted">No recent activity</p>';
        return;
    }
    
    container.innerHTML = activities.map(activity => `
        <div class="history-item" onclick="quickAction('${activity.city}', '${activity.activity_type}')">
            <i class="fas fa-${activity.activity_type === 'Weather History' ? 'history' : 'cloud-sun'}"></i>
            <div>
                <strong>${activity.city}</strong>
                <small>${activity.activity_type}</small>
            </div>
            <small>${formatTimestamp(activity.timestamp)}</small>
        </div>
    `).join('');
}

function quickAction(city, type) {
    if (type === 'Weather Check') {
        document.getElementById('weather-city-input').value = city;
        getWeatherData();
    } else if (type === 'Weather History') {
        document.getElementById('history-city-input').value = city;
        loadWeatherHistory();
    }
}

function updateRecentHistoryList(activities) {
    const container = document.getElementById('recent-history-list');
    if (!container) return;
    
    if (activities.length === 0) {
        container.innerHTML = '<p class="text-muted">No history yet</p>';
        return;
    }
    
    container.innerHTML = activities.map(activity => `
        <div class="history-item" onclick="quickHistoryLoad('${activity.city}')">
            <i class="fas fa-${activity.activity_type === 'Anomaly Detection' ? 'exclamation-triangle' : 'cloud-sun'}"></i>
            <div>
                <strong>${activity.city}</strong>
                <small>${activity.activity_type}</small>
            </div>
            <small>${formatTimestamp(activity.timestamp)}</small>
        </div>
    `).join('');
}

function quickHistoryLoad(city) {
    document.getElementById('history-city-input').value = city;
    loadWeatherHistory();
}

async function loadWeatherHistory() {
    const cityInput = document.getElementById('history-city-input');
    const periodSelect = document.getElementById('history-period');
    const loadBtn = document.getElementById('load-history-btn');
    
    const city = cityInput.value.trim();
    if (!city) {
        showAlert('Please enter a city name', 'error');
        return;
    }
    
    const originalText = loadBtn.innerHTML;
    loadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    loadBtn.disabled = true;
    
    try {
        const token = localStorage.getItem('weather_ai_token');
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        
        const params = new URLSearchParams();
        params.append('city', city);
        params.append('days', periodSelect.value);
        
        const response = await fetch(`${API_BASE_URL}/api/weather/history?${params.toString()}`, { 
            headers,
            // Add cache busting
            cache: 'no-cache'
        });
        
        if (response.ok) {
            const historyData = await response.json();
            displayWeatherHistory(historyData);
            showAlert(`Historical data loaded for ${city}!`, 'success');
            
            // Refresh dashboard data to show new activity
            loadDashboardData();
            loadUserHistoryList(); // Refresh history list
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to fetch historical data');
        }
    } catch (error) {
        console.error('Error loading history:', error);
        showAlert(error.message || 'Failed to load historical data. Please try again.', 'error');
    } finally {
        loadBtn.innerHTML = '<i class="fas fa-history"></i> Load Historical Data';
        loadBtn.disabled = false;
    }
}

function displayWeatherHistory(historyData) {
    updateHistoryChart(historyData);
    updateHistoryTable(historyData);
}

function updateHistoryChart(historyData) {
    const ctx = document.getElementById('historyChart').getContext('2d');
    
    if (charts.historyChart) charts.historyChart.destroy();
    
    const labels = historyData.history.map(item => {
        const date = new Date(item.date);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });
    
    const temperatures = historyData.history.map(item => item.temperature);
    const anomalies = historyData.history.map(item => item.was_anomaly);
    const anomalyPoints = temperatures.map((temp, index) => anomalies[index] ? temp : null);
    
    charts.historyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Temperature (°C)',
                    data: temperatures,
                    borderColor: '#1a6bb3',
                    backgroundColor: 'rgba(26, 107, 179, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2
                },
                {
                    label: 'Anomalies',
                    data: anomalyPoints,
                    type: 'scatter',
                    backgroundColor: '#f72585',
                    borderColor: '#b5179e',
                    borderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 10
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top', labels: { color: '#1e293b' } },
                title: {
                    display: true,
                    text: `Temperature Trends for ${historyData.city} (Last ${historyData.days} Days)`,
                    color: '#1e293b',
                    font: { size: 14, weight: '600' }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.datasetIndex === 0) return `Temperature: ${context.raw}°C`;
                            else return `Anomaly: ${context.raw}°C`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: { display: true, text: 'Temperature (°C)', color: '#64748b' },
                    ticks: { color: '#64748b' },
                    grid: { color: 'rgba(0, 0, 0, 0.05)' }
                },
                x: {
                    title: { display: true, text: 'Date', color: '#64748b' },
                    ticks: { color: '#64748b' },
                    grid: { color: 'rgba(0, 0, 0, 0.05)' }
                }
            },
            interaction: { intersect: false, mode: 'nearest' }
        }
    });
}

function updateHistoryTable(historyData) {
    const tableBody = document.getElementById('history-table-body');
    if (!tableBody) return;
    
    if (historyData.history.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 40px;">
                    No historical data available for ${historyData.city}
                </td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = historyData.history.map(item => `
        <tr>
            <td><strong>${item.date}</strong></td>
            <td>${item.temperature}°C</td>
            <td>${item.humidity}%</td>
            <td>${item.pressure} hPa</td>
            <td>${getWeatherCondition(item.temperature)}</td>
            <td>
                <span class="activity-badge ${item.was_anomaly ? 'badge-warning' : 'badge-success'}">
                    <i class="fas fa-${item.was_anomaly ? 'exclamation-triangle' : 'check-circle'}"></i>
                    ${item.was_anomaly ? 'Anomaly' : 'Normal'}
                </span>
            </td>
        </tr>
    `).join('');
}