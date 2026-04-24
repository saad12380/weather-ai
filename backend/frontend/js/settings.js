// ============ SETTINGS PAGE ============
function setupSettings() {
    loadSettings();
    loadUserPreferences();
    
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    if (darkModeToggle) darkModeToggle.addEventListener('change', toggleDarkMode);
    
    const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
    if (autoRefreshToggle) autoRefreshToggle.addEventListener('change', toggleAutoRefresh);
    
    const notificationToggle = document.getElementById('notification-toggle');
    if (notificationToggle) notificationToggle.addEventListener('change', toggleNotifications);
    
    const savePrefsBtn = document.getElementById('save-preferences-btn');
    if (savePrefsBtn) savePrefsBtn.addEventListener('click', saveUserPreferences);
}

async function loadUserPreferences() {
    try {
        const token = localStorage.getItem('weather_ai_token');
        if (!token) return;
        
        const response = await fetch(`${API_BASE_URL}/api/user/preferences`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Cache-Control': 'no-cache'
            }
        });
        
        if (response.ok) {
            const prefs = await response.json();
            applyUserPreferences(prefs);
        }
    } catch (error) {
        console.error('Error loading user preferences:', error);
    }
}

function applyUserPreferences(prefs) {
    // Apply theme
    if (prefs.theme === 'dark') {
        document.body.classList.add('dark-mode');
        const darkModeToggle = document.getElementById('dark-mode-toggle');
        if (darkModeToggle) darkModeToggle.checked = true;
    } else if (prefs.theme === 'light') {
        document.body.classList.remove('dark-mode');
        const darkModeToggle = document.getElementById('dark-mode-toggle');
        if (darkModeToggle) darkModeToggle.checked = false;
    }
    
    // Apply temperature unit preference
    const tempUnitRadios = document.querySelectorAll('input[name="temperature-unit"]');
    tempUnitRadios.forEach(radio => {
        if (radio.value === prefs.temperature_unit) {
            radio.checked = true;
        }
    });
    
    // Apply wind speed unit preference
    const windUnitRadios = document.querySelectorAll('input[name="wind-unit"]');
    windUnitRadios.forEach(radio => {
        if (radio.value === prefs.wind_speed_unit) {
            radio.checked = true;
        }
    });
    
    // Apply pressure unit preference
    const pressureUnitRadios = document.querySelectorAll('input[name="pressure-unit"]');
    pressureUnitRadios.forEach(radio => {
        if (radio.value === prefs.pressure_unit) {
            radio.checked = true;
        }
    });
    
    // Apply distance unit preference
    const distanceUnitRadios = document.querySelectorAll('input[name="distance-unit"]');
    distanceUnitRadios.forEach(radio => {
        if (radio.value === prefs.distance_unit) {
            radio.checked = true;
        }
    });
    
    // Apply date format preference
    const dateFormatSelect = document.getElementById('date-format');
    if (dateFormatSelect && prefs.date_format) {
        dateFormatSelect.value = prefs.date_format;
    }
    
    // Apply notification preferences
    const emailNotifications = document.getElementById('email-notifications');
    if (emailNotifications) emailNotifications.checked = prefs.notifications_email !== false;
    
    const anomalyAlerts = document.getElementById('anomaly-alerts');
    if (anomalyAlerts) anomalyAlerts.checked = prefs.anomaly_alerts !== false;
    
    const weatherUpdates = document.getElementById('weather-updates');
    if (weatherUpdates) weatherUpdates.checked = prefs.weather_updates !== false;
}

async function saveUserPreferences() {
    try {
        const token = localStorage.getItem('weather_ai_token');
        if (!token) {
            showAlert('Please login again', 'error');
            return;
        }
        
        // Gather preferences from UI
        const theme = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
        const temperatureUnit = document.querySelector('input[name="temperature-unit"]:checked')?.value || 'celsius';
        const windUnit = document.querySelector('input[name="wind-unit"]:checked')?.value || 'kmh';
        const pressureUnit = document.querySelector('input[name="pressure-unit"]:checked')?.value || 'hpa';
        const distanceUnit = document.querySelector('input[name="distance-unit"]:checked')?.value || 'km';
        const dateFormat = document.getElementById('date-format')?.value || 'MM/DD/YYYY';
        
        const emailNotifications = document.getElementById('email-notifications')?.checked || false;
        const anomalyAlerts = document.getElementById('anomaly-alerts')?.checked || false;
        const weatherUpdates = document.getElementById('weather-updates')?.checked || false;
        
        const preferences = {
            language: 'en',
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
            date_format: dateFormat,
            temperature_unit: temperatureUnit,
            wind_speed_unit: windUnit,
            pressure_unit: pressureUnit,
            distance_unit: distanceUnit,
            theme: theme,
            notifications_email: emailNotifications,
            anomaly_alerts: anomalyAlerts,
            weather_updates: weatherUpdates
        };
        
        const response = await fetch(`${API_BASE_URL}/api/user/preferences`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(preferences)
        });
        
        if (response.ok) {
            showAlert('Preferences saved successfully!', 'success');
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save preferences');
        }
    } catch (error) {
        console.error('Error saving preferences:', error);
        showAlert(error.message || 'Failed to save preferences', 'error');
    }
}

function loadSettings() {
    // Load localStorage settings as fallback/override
    const darkMode = localStorage.getItem('weather_ai_dark_mode') === 'true';
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    if (darkModeToggle) {
        darkModeToggle.checked = darkMode;
        if (darkMode) document.body.classList.add('dark-mode');
    }
    
    const autoRefresh = localStorage.getItem('weather_ai_auto_refresh') !== 'false';
    const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
    if (autoRefreshToggle) autoRefreshToggle.checked = autoRefresh;
    
    const notifications = localStorage.getItem('weather_ai_notifications') !== 'false';
    const notificationToggle = document.getElementById('notification-toggle');
    if (notificationToggle) notificationToggle.checked = notifications;
    
    const confidenceThreshold = localStorage.getItem('weather_ai_confidence_threshold') || '75';
    const modelSensitivity = localStorage.getItem('weather_ai_model_sensitivity') || 'medium';
    
    const thresholdSlider = document.getElementById('confidence-threshold');
    const thresholdValue = document.getElementById('threshold-value');
    const modelSensitivitySelect = document.getElementById('model-sensitivity');
    
    if (thresholdSlider && thresholdValue) {
        thresholdSlider.value = confidenceThreshold;
        thresholdValue.textContent = confidenceThreshold + '%';
    }
    
    if (modelSensitivitySelect) modelSensitivitySelect.value = modelSensitivity;
}

function toggleDarkMode() {
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const isDarkMode = darkModeToggle.checked;
    
    document.body.classList.toggle('dark-mode', isDarkMode);
    localStorage.setItem('weather_ai_dark_mode', isDarkMode);
    
    // Also save to backend if logged in
    saveUserPreferences();
    
    showAlert(`Dark mode ${isDarkMode ? 'enabled' : 'disabled'}`, 'success');
}

function toggleAutoRefresh() {
    const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
    const isAutoRefresh = autoRefreshToggle.checked;
    
    localStorage.setItem('weather_ai_auto_refresh', isAutoRefresh);
    
    if (isAutoRefresh && !refreshInterval) {
        setupAutoRefresh();
    } else if (!isAutoRefresh && refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
    
    showAlert(`Auto-refresh ${isAutoRefresh ? 'enabled' : 'disabled'}`, 'success');
}

function toggleNotifications() {
    const notificationToggle = document.getElementById('notification-toggle');
    const isNotifications = notificationToggle.checked;
    
    localStorage.setItem('weather_ai_notifications', isNotifications);
    
    // Also save to backend
    saveUserPreferences();
    
    showAlert(`Notifications ${isNotifications ? 'enabled' : 'disabled'}`, 'success');
}

function saveModelSettings() {
    const threshold = document.getElementById('confidence-threshold').value;
    const sensitivity = document.getElementById('model-sensitivity').value;
    
    localStorage.setItem('weather_ai_confidence_threshold', threshold);
    localStorage.setItem('weather_ai_model_sensitivity', sensitivity);
    
    showAlert(`Model settings saved: Threshold ${threshold}%, Sensitivity ${sensitivity}`, 'success');
}