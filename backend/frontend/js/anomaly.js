// ============ ENHANCED ANOMALY DETECTION ============
// Supports: Isolation Forest, Autoencoder, LSTM, Prophet, ARIMA, Z-Score

// Helper function for title case
function toTitleCase(str) {
    return str.replace('_', ' ').replace(/\w\S*/g, function(txt) {
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    });
}

function setupAnomalyDetection() {
    const detectBtn = document.getElementById('detect-anomaly-btn');
    if (detectBtn) detectBtn.addEventListener('click', detectAnomalies);
    
    const cityInput = document.getElementById('anomaly-city-input');
    const countryInput = document.getElementById('anomaly-country-input');
    
    if (cityInput) cityInput.addEventListener('keypress', function(e) { 
        if (e.key === 'Enter') detectAnomalies(); 
    });
    if (countryInput) countryInput.addEventListener('keypress', function(e) { 
        if (e.key === 'Enter') detectAnomalies(); 
    });
}

async function detectAnomalies() {
    const cityInput = document.getElementById('anomaly-city-input');
    const countryInput = document.getElementById('anomaly-country-input');
    const predictionPeriod = document.getElementById('prediction-period');
    const detectBtn = document.getElementById('detect-anomaly-btn');
    
    const city = cityInput.value.trim();
    if (!city) {
        showAlert('Please enter a city name', 'error');
        return;
    }
    
    const days = predictionPeriod.value === 'current' ? 0 : parseInt(predictionPeriod.value);
    
    const originalText = detectBtn.innerHTML;
    detectBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running Ensemble ML Models...';
    detectBtn.disabled = true;
    
    try {
        const futureContainer = document.getElementById('future-anomalies-container');
        if (futureContainer) futureContainer.style.display = 'none';
        
        const token = localStorage.getItem('weather_ai_token');
        const headers = {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        };
        
        const requestData = {
            city: city,
            country: countryInput.value.trim() || ""
        };
        
        // Get current anomaly detection
        const response = await fetch(`${API_BASE_URL}/api/weather/predict-anomaly`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) throw new Error('Failed to detect anomalies');
        
        const currentAnomalyData = await response.json();
        displayEnhancedAnomalyResult(currentAnomalyData);
        
        // Get future predictions if requested
        if (days > 0) {
            const futureResponse = await fetch(`${API_BASE_URL}/api/weather/future-anomalies`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ ...requestData, days })
            });
            
            if (futureResponse.ok) {
                const futureData = await futureResponse.json();
                displayEnhancedFutureAnomalies(futureData);
            }
        }
        
        showAlert(`✅ Ensemble ML analysis complete for ${city}!`, 'success');
        loadDashboardData();
        loadAnomalyChart();
        
    } catch (error) {
        console.error('Error detecting anomalies:', error);
        showAlert(error.message || 'Failed to detect anomalies. Please try again.', 'error');
    } finally {
        detectBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Run Ensemble ML Detection';
        detectBtn.disabled = false;
    }
}

// ============ ENHANCED DISPLAY FUNCTIONS WITH PRACTICAL GUIDANCE ============

function displayEnhancedAnomalyResult(anomalyData) {
    const container = document.getElementById('anomaly-result-container');
    
    const isAnomaly = anomalyData.is_anomaly;
    const probability = (anomalyData.anomaly_probability * 100).toFixed(1);
    const confidence = (anomalyData.confidence * 100).toFixed(1);
    const weather = anomalyData.current_weather;
    const modelDetails = anomalyData.model_details || {};
    const modelsUsed = modelDetails.models_used || [];
    const modelScores = modelDetails.model_scores || {};
    const zscoreDetails = modelDetails.zscore_details || {};
    const statisticalAnomalies = modelDetails.statistical_anomalies || [];
    
    // Generate model badges HTML
    const modelBadges = modelsUsed.filter(m => m).map(model => {
        let icon = 'fa-brain';
        if (model.includes('Isolation')) icon = 'fa-tree';
        else if (model.includes('Autoencoder')) icon = 'fa-brain';
        else if (model.includes('LSTM')) icon = 'fa-chart-line';
        else if (model.includes('Prophet')) icon = 'fa-calendar';
        else if (model.includes('ARIMA')) icon = 'fa-wave-square';
        else if (model.includes('Z-Score')) icon = 'fa-calculator';
        
        return `<span class="model-badge-small"><i class="fas ${icon}"></i> ${model}</span>`;
    }).join('');
    
    // Generate practical advice based on anomaly type
    const practicalAdvice = generatePracticalAdvice(anomalyData);
    
    // Generate causes explanation
    const causesExplanation = generateCausesExplanation(anomalyData, statisticalAnomalies);
    
    // Generate actionable tips
    const actionableTips = generateActionableTips(anomalyData, weather);
    
    container.innerHTML = `
        <div class="anomaly-alert-card fade-in-up">
            <div class="anomaly-header">
                <div class="anomaly-icon" style="background: ${isAnomaly ? 'linear-gradient(135deg, #1a6bb3 0%, #00c9ff 100%)' : 'linear-gradient(135deg, #10b981 0%, #059669 100%)'};">
                    <i class="fas fa-${isAnomaly ? 'exclamation-triangle' : 'check-circle'}"></i>
                </div>
                <div>
                    <h3 style="color: ${isAnomaly ? '#1a6bb3' : '#10b981'};">${isAnomaly ? '⚠️ ' + anomalyData.anomaly_type + ' Detected!' : '✅ Normal Weather Patterns'}</h3>
                    <p style="color: var(--text-primary);">${anomalyData.anomaly_explanation || 'Ensemble ML analysis complete'}</p>
                </div>
            </div>
            
            <div class="model-badges-container">
                ${modelBadges}
                <span class="model-badge-small"><i class="fas fa-cogs"></i> Ensemble Score: ${probability}%</span>
            </div>
            
            <div class="confidence-meter">
                <div class="meter-label">
                    <span>Ensemble Confidence</span>
                    <span><strong>${confidence}%</strong></span>
                </div>
                <div class="meter-bar">
                    <div class="meter-fill" style="width: ${confidence}%; background: ${isAnomaly ? 'linear-gradient(90deg, #1a6bb3 0%, #00c9ff 100%)' : 'linear-gradient(90deg, #10b981 0%, #059669 100%)'};"></div>
                </div>
            </div>
            
            <div class="weather-grid">
                <div class="weather-item"><i class="fas fa-thermometer-half"></i><span>${Math.round(weather.temperature)}°C</span><small>Temperature</small></div>
                <div class="weather-item"><i class="fas fa-tint"></i><span>${weather.humidity}%</span><small>Humidity</small></div>
                <div class="weather-item"><i class="fas fa-wind"></i><span>${Math.round(weather.wind_speed)} km/h</span><small>Wind Speed</small></div>
                <div class="weather-item"><i class="fas fa-chart-bar"></i><span>${weather.pressure} hPa</span><small>Pressure</small></div>
            </div>
            
            <!-- Weather Impact Summary -->
            <div class="impact-summary">
                <h4><i class="fas fa-clipboard-list"></i> What This Means For You:</h4>
                <p>${practicalAdvice.summary}</p>
            </div>
            
            <!-- Why This Happens (Scientific Explanation) -->
            <div class="causes-section">
                <h4><i class="fas fa-microscope"></i> Why This Weather Anomaly Occurs:</h4>
                <div class="causes-content">
                    ${causesExplanation}
                </div>
            </div>
            
            <!-- Actionable Tips Grid -->
            <div class="tips-grid">
                <h4><i class="fas fa-lightbulb"></i> Practical Tips & Precautions:</h4>
                <div class="tips-container">
                    ${actionableTips}
                </div>
            </div>
            
            <!-- Affected Groups Section -->
            <div class="affected-groups">
                <h4><i class="fas fa-users"></i> Who Should Be Concerned:</h4>
                <div class="groups-container">
                    ${generateAffectedGroups(anomalyData)}
                </div>
            </div>
            
            <!-- Historical Context -->
            <div class="historical-context">
                <h4><i class="fas fa-history"></i> How Unusual Is This?</h4>
                <p>${generateHistoricalContext(anomalyData, weather)}</p>
            </div>
            
            <!-- Recommendations Card -->
            <div class="recommendations-card">
                <h4><i class="fas fa-check-circle"></i> Recommended Actions:</h4>
                <ul class="recommendations-list">
                    ${generateRecommendationsList(anomalyData)}
                </ul>
            </div>
            
            <!-- Dynamic Safety Guidance Section -->
            ${generateCurrentAnomalySafetyGuidance(anomalyData)}
            
            <!-- Model Scores (Collapsible) -->
            <details class="model-details">
                <summary><i class="fas fa-chart-bar"></i> View Detailed Model Scores</summary>
                <div class="model-scores-grid">
                    <h4 style="margin: 20px 0 10px; color: var(--text-primary);">Model Scores:</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
                        ${Object.entries(modelScores).map(([model, score]) => {
                            const modelName = toTitleCase(model.replace('_', ' '));
                            return `
                            <div class="model-score-item">
                                <span>${modelName}:</span>
                                <span class="score-value ${score > 0 ? 'anomaly' : 'normal'}">${score}</span>
                            </div>
                        `}).join('')}
                    </div>
                </div>
                
                ${Object.keys(zscoreDetails).length > 0 ? `
                <div class="zscore-details">
                    <h4 style="margin: 20px 0 10px; color: var(--text-primary);">Z-Score Analysis:</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                        ${Object.entries(zscoreDetails).map(([param, data]) => `
                            <div class="zscore-item ${data.is_anomaly ? 'anomaly' : ''}">
                                <span>${param}:</span>
                                <span>Z=${data.zscore?.toFixed(2) || 'N/A'}</span>
                                ${data.is_anomaly ? '<span class="badge-danger">⚠️</span>' : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
                
                <div class="mt-4">
                    <div style="background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px;">
                        <h5 style="margin-bottom: 10px; color: var(--text-primary);"><i class="fas fa-info-circle"></i> Analysis Details</h5>
                        <p style="color: var(--text-secondary); font-size: 14px; margin-bottom: 5px;"><strong>Models used:</strong> ${modelsUsed.filter(m => m).join(' + ')}</p>
                        <p style="color: var(--text-secondary); font-size: 14px; margin-bottom: 5px;"><strong>Anomaly type:</strong> ${anomalyData.anomaly_type || 'N/A'}</p>
                        <p style="color: var(--text-secondary); font-size: 14px; margin-bottom: 5px;"><strong>Severity:</strong> <span class="badge-${anomalyData.severity?.toLowerCase() || 'normal'}">${anomalyData.severity || 'None'}</span></p>
                        <p style="color: var(--text-secondary); font-size: 14px;"><strong>Analysis time:</strong> ${new Date().toLocaleString()}</p>
                    </div>
                </div>
            </details>
            
            <!-- Share/Export Buttons -->
            <div class="action-buttons">
                <button class="btn btn-secondary" onclick="downloadAnomalyReport()">
                    <i class="fas fa-download"></i> Download Report
                </button>
                <button class="btn btn-primary" onclick="shareAnomalyAlert()">
                    <i class="fas fa-share-alt"></i> Share Alert
                </button>
                <button class="btn btn-info" onclick="getDetailedGuidance()">
                    <i class="fas fa-book-open"></i> Detailed Guidance
                </button>
            </div>
        </div>
    `;
    
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function displayEnhancedFutureAnomalies(futureData) {
    const container = document.getElementById('future-anomalies-container');
    const tableBody = document.getElementById('future-anomalies-table-body');
    const confidenceSpan = document.getElementById('ensemble-confidence');
    const confidenceFill = document.getElementById('confidence-fill');
    const trendSpan = document.getElementById('ensemble-trend');
    
    if (!container || !tableBody) return;
    
    container.style.display = 'block';
    
    // Update confidence meter
    if (confidenceSpan) confidenceSpan.textContent = `${futureData.confidence.toFixed(1)}%`;
    if (confidenceFill) confidenceFill.style.width = `${futureData.confidence}%`;
    if (trendSpan) {
        trendSpan.innerHTML = `Trend: <strong>${futureData.trend}</strong> | Models: ${futureData.models_used?.length || 0}`;
    }
    
    updateFutureAnomalyChart(futureData);
    
    if (futureData.anomalies && futureData.anomalies.length > 0) {
        tableBody.innerHTML = futureData.anomalies.map(day => {
            const zscore = day.zscore_details?.temperature?.zscore || 0;
            
            return `
            <tr class="${day.is_anomaly ? 'anomaly-row' : ''}">
                <td><strong>${day.date}</strong></td>
                <td>${day.day_name}</td>
                <td>${day.temperature}°C</td>
                <td>${day.condition}</td>
                <td>
                    <span class="activity-badge ${day.is_anomaly ? 'badge-warning' : 'badge-success'}">
                        ${day.anomaly_type}
                    </span>
                </td>
                <td>
                    ${day.is_anomaly ? 
                        `<span class="activity-badge 
                            ${day.severity === 'Critical' ? 'badge-danger' : 
                              day.severity === 'High' ? 'badge-warning' : 
                              'badge-primary'}">
                            ${day.severity}
                        </span>` : 
                        '<span class="activity-badge badge-success">None</span>'
                    }
                </td>
                <td>
                    <span style="color: ${zscore > 3 ? '#f72585' : zscore > 2 ? '#f59e0b' : '#10b981'};">
                        ${zscore.toFixed(2)}σ
                    </span>
                </td>
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="flex: 1; height: 8px; background: rgba(0,0,0,0.1); border-radius: 4px;">
                            <div style="width: ${day.probability}%; height: 100%; background: ${day.is_anomaly ? '#f72585' : '#10b981'}; border-radius: 4px;"></div>
                        </div>
                        <span>${day.probability}%</span>
                    </div>
                </td>
            </tr>
        `}).join('');
    } else {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; color: var(--text-muted); padding: 40px;">
                    No future anomaly data available
                </td>
            </tr>
        `;
    }
    
    generateEnhancedSafetyGuidance(futureData);
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function generateEnhancedSafetyGuidance(futureData) {
    const container = document.getElementById('safety-guidance-container');
    if (!container) return;
    
    const guidance = futureData.safety_guidance || {};
    const recommendations = futureData.recommendations || {};
    
    // Build guidance items from the dynamic backend data
    const guidanceHTML = Object.entries(guidance)
        .filter(([key, value]) => key !== 'model_confidence' && value)
        .map(([key, value]) => {
            let icon = 'fa-users';
            if (key === 'farmers') icon = 'fa-tractor';
            else if (key === 'construction') icon = 'fa-hard-hat';
            else if (key === 'transportation') icon = 'fa-truck';
            else if (key === 'health_elderly') icon = 'fa-heartbeat';
            else if (key === 'emergency_prep') icon = 'fa-ambulance';
            
            return `
                <div class="guidance-item">
                    <i class="fas ${icon}"></i>
                    <p>${value}</p>
                </div>
            `;
        }).join('');
    
    // Extract actions from recommendations
    const actionsHTML = (recommendations.actions || [])
        .slice(0, 5)
        .map(action => `<li>${action}</li>`)
        .join('');
    
    container.innerHTML = `
        <div class="safety-guidance-card">
            <h4><i class="fas fa-shield-alt"></i> AI-Generated Safety & Guidance</h4>
            <p class="guidance-level" style="color: ${
                recommendations.level === 'Critical' ? '#f72585' : 
                recommendations.level === 'High' ? '#f59e0b' : 
                recommendations.level === 'Medium' ? '#0ea5e9' :
                '#10b981'
            };">
                <strong>${recommendations.level || 'Normal'}</strong> Level Alert
            </p>
            
            <div class="guidance-grid">
                ${guidanceHTML}
            </div>
            
            ${actionsHTML ? `
            <div class="recommendation-actions">
                <h5><i class="fas fa-check-circle"></i> Recommended Actions:</h5>
                <ul>
                    ${actionsHTML}
                </ul>
            </div>
            ` : ''}
            
            <p class="model-note">
                <i class="fas fa-robot"></i> 
                Guidance dynamically generated by ensemble ML models based on predicted weather patterns and real-time anomaly analysis
            </p>
        </div>
    `;
}

function updateFutureAnomalyChart(futureData) {
    const ctx = document.getElementById('futureAnomalyChart').getContext('2d');
    
    if (charts.futureAnomalyChart) charts.futureAnomalyChart.destroy();
    
    const labels = futureData.anomalies.map(day => `${day.day_name.substring(0, 3)} ${day.date.split('-')[2]}`);
    const temperatures = futureData.anomalies.map(day => day.temperature);
    const anomalyFlags = futureData.anomalies.map(day => day.is_anomaly);
    const zscores = futureData.anomalies.map(day => day.zscore_details?.temperature?.zscore || 0);
    
    charts.futureAnomalyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Temperature (°C)',
                    data: temperatures,
                    borderColor: '#1a6bb3',
                    backgroundColor: 'rgba(26, 107, 179, 0.1)',
                    fill: true,
                    tension: 0.3,
                    borderWidth: 2,
                    pointRadius: 4,
                    yAxisID: 'y'
                },
                {
                    label: 'Z-Score (Anomaly Threshold > 3)',
                    data: zscores,
                    type: 'line',
                    borderColor: '#1a6bb3',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 2,
                    yAxisID: 'y1'
                },
                {
                    label: 'Anomaly Days',
                    data: temperatures.map((temp, index) => anomalyFlags[index] ? temp : null),
                    type: 'scatter',
                    backgroundColor: '#1a6bb3',
                    borderColor: '#00c9ff',
                    borderWidth: 2,
                    pointRadius: 8,
                    pointHoverRadius: 12,
                    yAxisID: 'y'
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: { position: 'top', labels: { color: '#1e293b' } },
                title: {
                    display: true,
                    text: `7-Day Forecast with Ensemble ML Anomaly Detection for ${futureData.city}`,
                    color: '#1e293b',
                    font: { size: 14, weight: '600' }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const dayIndex = context.dataIndex;
                            const day = futureData.anomalies[dayIndex];
                            
                            if (context.dataset.label === 'Z-Score (Anomaly Threshold > 3)') {
                                return `Z-Score: ${context.raw.toFixed(2)}σ (Threshold: 3σ)`;
                            }
                            
                            let tooltip = `${context.dataset.label}: ${context.raw}`;
                            if (day.is_anomaly) {
                                tooltip += `\n⚠️ Anomaly: ${day.anomaly_type}`;
                                tooltip += `\nSeverity: ${day.severity}`;
                                tooltip += `\nProbability: ${day.probability}%`;
                                tooltip += `\nZ-Score: ${day.zscore_details?.temperature?.zscore?.toFixed(2) || 'N/A'}σ`;
                            }
                            return tooltip;
                        }
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: { display: true, text: 'Temperature (°C)', color: '#64748b' },
                    ticks: { color: '#64748b' },
                    grid: { color: 'rgba(0, 0, 0, 0.05)' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: { display: true, text: 'Z-Score (σ)', color: '#64748b' },
                    ticks: { color: '#64748b' },
                    grid: { drawOnChartArea: false },
                    min: 0,
                    max: 5
                },
                x: {
                    title: { display: true, text: 'Date', color: '#64748b' },
                    ticks: { color: '#64748b' },
                    grid: { color: 'rgba(0, 0, 0, 0.05)' }
                }
            }
        }
    });
}

// ============ PRACTICAL GUIDANCE HELPER FUNCTIONS ============

function generateCurrentAnomalySafetyGuidance(anomalyData) {
    const safetyGuidance = anomalyData.safety_guidance || {};
    const recommendations = anomalyData.recommendations || {};
    
    if (!safetyGuidance || Object.keys(safetyGuidance).length === 0) {
        return '';
    }
    
    // Build guidance items from the dynamic backend data
    const guidanceItems = [
        { key: 'general_public', icon: 'fa-users', label: 'General Public' },
        { key: 'farmers', icon: 'fa-tractor', label: 'Farmers' },
        { key: 'construction', icon: 'fa-hard-hat', label: 'Construction' },
        { key: 'transportation', icon: 'fa-truck', label: 'Transportation' },
        { key: 'health_elderly', icon: 'fa-heartbeat', label: 'Health & Elderly' },
        { key: 'emergency_prep', icon: 'fa-ambulance', label: 'Emergency Prep' }
    ];
    
    const guidanceHTML = guidanceItems
        .filter(item => safetyGuidance[item.key])
        .map(item => {
            return `
                <div class="guidance-item">
                    <i class="fas ${item.icon}"></i>
                    <p>${safetyGuidance[item.key]}</p>
                </div>
            `;
        }).join('');
    
    const actionsHTML = (recommendations.actions || [])
        .map(action => `<li>${action}</li>`)
        .join('');
    
    const severityColor = recommendations.level === 'Critical' ? '#f72585' : 
                         recommendations.level === 'High' ? '#f59e0b' : 
                         recommendations.level === 'Medium' ? '#0ea5e9' :
                         '#10b981';
    
    return `
        <div class="safety-guidance-card">
            <h4><i class="fas fa-shield-alt"></i> AI-Generated Safety & Guidance</h4>
            <p class="guidance-level" style="color: ${severityColor};">
                <strong>${recommendations.level || 'Normal'}</strong> Level Alert
            </p>
            
            <div class="guidance-grid">
                ${guidanceHTML}
            </div>
            
            ${actionsHTML ? `
            <div class="recommendation-actions">
                <h5><i class="fas fa-check-circle"></i> Critical Actions:</h5>
                <ul>
                    ${actionsHTML}
                </ul>
            </div>
            ` : ''}
            
            <p class="model-note">
                <i class="fas fa-robot"></i> 
                Guidance dynamically generated by ensemble ML models based on real-time weather parameters and anomaly analysis
            </p>
        </div>
    `;
}

function generatePracticalAdvice(anomalyData) {
    const type = anomalyData.anomaly_type || 'Normal';
    const severity = anomalyData.severity || 'None';
    const temp = anomalyData.current_weather?.temperature || 0;
    
    let summary = "";
    
    if (type.includes("Temperature") || type.includes("Heat") || type.includes("Cold")) {
        if (temp > 35) {
            summary = "🌡️ Extreme heat warning! This can cause heat exhaustion, dehydration, and heat stroke. Stay indoors during peak hours (11am-4pm).";
        } else if (temp < 0) {
            summary = "❄️ Freezing conditions detected! Risk of hypothermia and frozen pipes. Dress in layers and limit outdoor exposure.";
        } else if (type.includes("Spike")) {
            summary = "📈 Rapid temperature change! Your body needs time to adjust. Monitor for headaches, fatigue, and respiratory issues.";
        }
    } else if (type.includes("Wind")) {
        summary = "💨 High winds expected! Secure loose outdoor items, be cautious while driving (especially high-profile vehicles), and watch for falling branches.";
    } else if (type.includes("Humidity")) {
        if (anomalyData.current_weather?.humidity > 80) {
            summary = "💧 High humidity makes the air feel hotter than it is. Risk of heat exhaustion increases. Use fans/AC and stay hydrated.";
        } else if (anomalyData.current_weather?.humidity < 30) {
            summary = "🏜️ Very dry air! Can cause dehydration, dry skin, and respiratory irritation. Use moisturizer and keep hydrated.";
        }
    } else if (type.includes("Pressure") || type.includes("Storm")) {
        summary = "⛈️ Low pressure system approaching! May cause headaches, joint pain in some people. Secure outdoor items and prepare for possible storms.";
    }
    
    return {
        summary: summary || "Normal weather conditions. No special precautions needed."
    };
}

function generateCausesExplanation(anomalyData, statisticalAnomalies) {
    const type = anomalyData.anomaly_type || 'Normal';
    let explanation = "";
    
    const causes = {
        "Temperature Spike": "Sudden temperature increases often result from high-pressure systems trapping warm air, urban heat island effects, or changes in wind patterns bringing hot air from other regions. Climate change is making these events more frequent and intense.",
        
        "Extreme Temperature": "Extreme temperatures occur when atmospheric circulation patterns create persistent high or low-pressure systems. In cities, concrete and asphalt absorb heat during the day and release it slowly at night, preventing cooling.",
        
        "High Winds": "Strong winds develop from large pressure differences between weather systems. This can happen when cold fronts push into warm areas, or when storms create strong pressure gradients.",
        
        "Extreme Humidity": "High humidity happens when warm, moist air from oceans or large water bodies moves inland. Low humidity occurs when dry continental air masses dominate, often behind cold fronts.",
        
        "Pressure Drop": "Rapid pressure drops indicate approaching storms or low-pressure systems. The air rises, cools, and condenses into clouds and precipitation. This often precedes rain, storms, or cyclones.",
        
        "Multi-Factor Anomaly": "Multiple weather factors deviating simultaneously often indicates a significant weather system moving through the area - like a frontal system, tropical storm, or unusual jet stream pattern."
    };
    
    explanation = causes[type] || "Weather anomalies occur when atmospheric conditions deviate from normal patterns due to factors like jet stream changes, ocean temperature variations (El Niño/La Niña), or climate change impacts.";
    
    // Add specific factor details if available
    if (statisticalAnomalies.length > 0) {
        explanation += `<br><br><strong>Specific factors detected:</strong><ul>`;
        statisticalAnomalies.forEach(a => {
            explanation += `<li>${a.feature} is ${a.deviation} normal range (${a.normal_range[0].toFixed(1)}-${a.normal_range[1].toFixed(1)})</li>`;
        });
        explanation += `</ul>`;
    }
    
    return explanation;
}

function generateActionableTips(anomalyData, weather) {
    const type = anomalyData.anomaly_type || 'Normal';
    const temp = weather?.temperature || 0;
    const humidity = weather?.humidity || 50;
    const wind = weather?.wind_speed || 0;
    
    let tips = [];
    
    // Temperature-based tips
    if (temp > 35 || type.includes("Heat")) {
        tips = [
            { icon: "💧", tip: "Drink water every 20 minutes even if not thirsty" },
            { icon: "🏠", tip: "Stay in air-conditioned spaces between 11am-4pm" },
            { icon: "👕", tip: "Wear light, loose-fitting, light-colored clothing" },
            { icon: "🚗", tip: "Never leave children or pets in parked cars" },
            { icon: "🧓", tip: "Check on elderly neighbors and relatives" }
        ];
    } else if (temp < 0 || type.includes("Cold")) {
        tips = [
            { icon: "🧥", tip: "Dress in layers - moisture-wicking base, insulating middle, waterproof outer" },
            { icon: "🏠", tip: "Keep your home at 18°C (65°F) minimum to prevent pipes freezing" },
            { icon: "🚰", tip: "Let faucets drip slowly during extreme cold to prevent freezing" },
            { icon: "🐕", tip: "Bring pets indoors - if it's too cold for you, it's too cold for them" },
            { icon: "⚠️", tip: "Watch for signs of hypothermia: shivering, confusion, slurred speech" }
        ];
    } else if (type.includes("Wind") || wind > 30) {
        tips = [
            { icon: "🏠", tip: "Secure patio furniture, garbage cans, and outdoor decorations" },
            { icon: "🚚", tip: "High-profile vehicles should avoid driving or use extreme caution" },
            { icon: "🌳", tip: "Avoid parking under trees or near power lines" },
            { icon: "🔌", tip: "Charge devices and prepare for possible power outages" },
            { icon: "🚶", tip: "If walking, be aware of falling branches and debris" }
        ];
    } else if (humidity > 80) {
        tips = [
            { icon: "💧", tip: "Drink water frequently - humidity makes you sweat without noticing" },
            { icon: "❄️", tip: "Use fans or AC - moving air helps your body cool down" },
            { icon: "🚿", tip: "Take cool showers to lower body temperature" },
            { icon: "🧴", tip: "Use powder to prevent skin chafing and rashes" },
            { icon: "🌙", tip: "Use dehumidifier at night for better sleep" }
        ];
    } else {
        tips = [
            { icon: "☀️", tip: "Enjoy the weather! Perfect for outdoor activities" },
            { icon: "🧴", tip: "Still use sunscreen - UV can be high even on cloudy days" },
            { icon: "💧", tip: "Maintain normal hydration throughout the day" },
            { icon: "🌿", tip: "Good time for gardening or outdoor projects" }
        ];
    }
    
    return tips.map(t => `
        <div class="tip-item">
            <span class="tip-icon">${t.icon}</span>
            <span class="tip-text">${t.tip}</span>
        </div>
    `).join('');
}

function generateAffectedGroups(anomalyData) {
    const type = anomalyData.anomaly_type || 'Normal';
    
    const groups = {
        "Temperature": [
            { group: "👴 Elderly (65+)", risk: "Higher risk of heat stroke/hypothermia" },
            { group: "👶 Infants & Children", risk: "Body temperature regulates less efficiently" },
            { group: "🏥 People with chronic illness", risk: "Heart/lung conditions worsen in extremes" },
            { group: "💊 People on certain medications", risk: "Some drugs affect temperature regulation" },
            { group: "🏗️ Outdoor workers", risk: "Prolonged exposure increases risk" }
        ],
        "Wind": [
            { group: "🚚 Truck drivers", risk: "High-profile vehicles at risk of overturning" },
            { group: "🏠 People in mobile homes", risk: "Less structural stability in high winds" },
            { group: "⚡ Utility workers", risk: "Power line repair during outages" },
            { group: "🚶 Pedestrians", risk: "Falling debris risk" }
        ],
        "Humidity": [
            { group: "🏃 Athletes", risk: "Dehydration and heat exhaustion" },
            { group: "🌿 People with asthma", risk: "Breathing difficulties" },
            { group: "👴 Elderly", risk: "Heat stress from combined heat-humidity" }
        ]
    };
    
    let relevantGroups = [];
    if (type.includes("Temperature") || type.includes("Heat") || type.includes("Cold")) {
        relevantGroups = groups.Temperature;
    } else if (type.includes("Wind")) {
        relevantGroups = groups.Wind;
    } else if (type.includes("Humidity")) {
        relevantGroups = groups.Humidity;
    } else {
        return "<p>No specific groups at risk under normal conditions.</p>";
    }
    
    return relevantGroups.map(g => `
        <div class="group-item">
            <span class="group-icon">${g.group}</span>
            <span class="group-risk">${g.risk}</span>
        </div>
    `).join('');
}

function generateHistoricalContext(anomalyData, weather) {
    const stats = anomalyData.historical_comparison?.temperature || {};
    const current = weather?.temperature || 0;
    const mean = stats.historical_mean || 0;
    
    if (!mean) return "Comparing to 90 days of historical data for this location.";
    
    const diff = Math.abs(current - mean);
    let context = "";
    
    if (diff > 10) {
        context = `🔥 This temperature is EXTREMELY unusual - ${diff.toFixed(1)}°C different from the historical average of ${mean.toFixed(1)}°C. Events like this typically occur only a few times per decade.`;
    } else if (diff > 5) {
        context = `⚠️ This temperature is significantly unusual - ${diff.toFixed(1)}°C different from the historical average of ${mean.toFixed(1)}°C. This might happen a few times per year.`;
    } else if (diff > 2) {
        context = `📊 This temperature is moderately unusual - ${diff.toFixed(1)}°C different from the historical average of ${mean.toFixed(1)}°C. Common during seasonal transitions.`;
    } else {
        context = `✅ This temperature is within normal variation - only ${diff.toFixed(1)}°C from the historical average of ${mean.toFixed(1)}°C.`;
    }
    
    return context;
}

function generateRecommendationsList(anomalyData) {
    const type = anomalyData.anomaly_type || 'Normal';
    
    let recommendations = [];
    
    if (type.includes("Temperature") || type.includes("Heat")) {
        recommendations = [
            "🚰 Carry water with you at all times",
            "🏠 Plan outdoor activities for early morning or evening",
            "🧴 Apply sunscreen (SPF 30+) even on cloudy days",
            "👕 Wear light-colored, loose clothing",
            "📱 Set weather alerts on your phone",
            "🏥 Know the signs of heat exhaustion: dizziness, nausea, headache"
        ];
    } else if (type.includes("Cold")) {
        recommendations = [
            "🧥 Wear multiple layers - thermal, regular, waterproof",
            "🧤 Cover exposed skin to prevent frostbite",
            "🚗 Keep emergency kit in car: blanket, food, water, flashlight",
            "🏠 Insulate windows and doors to keep heat in",
            "🐕 Bring pets inside - they get cold too!",
            "📞 Check on elderly neighbors"
        ];
    } else if (type.includes("Wind")) {
        recommendations = [
            "🏠 Secure outdoor furniture and decorations",
            "🔋 Charge phones and power banks",
            "🕯️ Have flashlights and batteries ready",
            "🚗 If driving, keep both hands on wheel",
            "🌳 Avoid parking under trees",
            "📻 Listen to local news for updates"
        ];
    } else {
        recommendations = [
            "🌤️ Enjoy the good weather!",
            "📱 Still check daily forecast for updates",
            "💧 Maintain normal hydration",
            "🧴 Sunscreen recommended even on cloudy days",
            "🌿 Great day for outdoor activities"
        ];
    }
    
    return recommendations.map(r => `<li>${r}</li>`).join('');
}

// ============ SHARE/DOWNLOAD FUNCTIONS ============

function downloadAnomalyReport() {
    // Get current anomaly data from the page
    const report = {
        timestamp: new Date().toISOString(),
        location: document.querySelector('.location-info h3')?.textContent || 'Unknown',
        anomaly_type: document.querySelector('.anomaly-header h3')?.textContent || 'Unknown',
        recommendations: Array.from(document.querySelectorAll('.recommendations-list li')).map(li => li.textContent)
    };
    
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `weather-anomaly-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    
    showAlert('Report downloaded successfully!', 'success');
}

function shareAnomalyAlert() {
    const text = `⚠️ Weather Alert: ${document.querySelector('.anomaly-header h3')?.textContent || 'Anomaly detected'} in ${document.querySelector('.location-info h3')?.textContent || 'your area'}. Check Weather AI for details and safety tips.`;
    
    if (navigator.share) {
        navigator.share({
            title: 'Weather Anomaly Alert',
            text: text,
            url: window.location.href
        });
    } else {
        navigator.clipboard.writeText(text);
        showAlert('Alert copied to clipboard!', 'success');
    }
}

function getDetailedGuidance() {
    // Scroll to safety guidance section or open detailed view
    const guidanceSection = document.getElementById('safety-guidance-container');
    if (guidanceSection) {
        guidanceSection.scrollIntoView({ behavior: 'smooth' });
    }
}