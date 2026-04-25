// ============ GLOBAL CONFIGURATION ============
const API_BASE_URL = '';
let charts = {};
let currentUser = null;
let refreshInterval = null;

// ============ DASHBOARD DATA CLEARING ============
function clearAllDashboardData() {
    console.log('🧹 Clearing all dashboard data for new user');
    
    // Clear any stored charts - safely check if they exist and have destroy method
    try {
        if (window.anomalyChart && typeof window.anomalyChart.destroy === 'function') {
            window.anomalyChart.destroy();
            window.anomalyChart = null;
        }
    } catch (e) { console.log('Note: anomalyChart not ready'); }
    
    try {
        if (window.futureAnomalyChart && typeof window.futureAnomalyChart.destroy === 'function') {
            window.futureAnomalyChart.destroy();
            window.futureAnomalyChart = null;
        }
    } catch (e) { console.log('Note: futureAnomalyChart not ready'); }
    
    try {
        if (window.insightsChart && typeof window.insightsChart.destroy === 'function') {
            window.insightsChart.destroy();
            window.insightsChart = null;
        }
    } catch (e) { console.log('Note: insightsChart not ready'); }
    
    try {
        if (window.analyticsChart1 && typeof window.analyticsChart1.destroy === 'function') {
            window.analyticsChart1.destroy();
            window.analyticsChart1 = null;
        }
    } catch (e) { console.log('Note: analyticsChart1 not ready'); }
    
    try {
        if (window.analyticsChart2 && typeof window.analyticsChart2.destroy === 'function') {
            window.analyticsChart2.destroy();
            window.analyticsChart2 = null;
        }
    } catch (e) { console.log('Note: analyticsChart2 not ready'); }
    
    try {
        if (window.historyChart && typeof window.historyChart.destroy === 'function') {
            window.historyChart.destroy();
            window.historyChart = null;
        }
    } catch (e) { console.log('Note: historyChart not ready'); }
    
    try {
        if (window.usageChart && typeof window.usageChart.destroy === 'function') {
            window.usageChart.destroy();
            window.usageChart = null;
        }
    } catch (e) { console.log('Note: usageChart not ready'); }
    
    // Clear dashboard stats container
    const statsContainer = document.getElementById('dashboard-stats');
    if (statsContainer) {
        statsContainer.innerHTML = '';
    }
    
    // Clear activity table
    const activityTable = document.getElementById('activity-table-body');
    if (activityTable) {
        activityTable.innerHTML = '';
    }
    
    // Clear weather results
    const weatherResult = document.getElementById('weather-result-container');
    if (weatherResult) {
        weatherResult.innerHTML = '';
    }
    
    // Clear anomaly results
    const anomalyResult = document.getElementById('anomaly-result-container');
    if (anomalyResult) {
        anomalyResult.innerHTML = '';
    }
    
    // Clear future anomalies container
    const futureContainer = document.getElementById('future-anomalies-container');
    if (futureContainer) {
        futureContainer.style.display = 'none';
    }
    
    // Clear history table
    const historyTable = document.getElementById('history-table-body');
    if (historyTable) {
        historyTable.innerHTML = '';
    }
    
    // Clear any API keys table
    const apiKeysTable = document.getElementById('api-keys-table');
    if (apiKeysTable) {
        apiKeysTable.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 40px;">No API keys generated yet.</td></tr>';
    }
    
    // Clear invoices table
    const invoicesTable = document.getElementById('invoices-table-body');
    if (invoicesTable) {
        invoicesTable.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 40px;">No invoices yet.</td></tr>';
    }
    
    console.log('✅ Dashboard data cleared');
}

// ============ MAIN INITIALIZATION ============
document.addEventListener('DOMContentLoaded', function() {
    console.log('📊 Weather AI Dashboard initialized');
    addSearchStyles();
    checkAuthentication();
});

// Force clear any service worker caches
if ('caches' in window) {
    caches.keys().then(function(names) {
        for (let name of names) {
            caches.delete(name);
        }
    });
}

// ============ AUTHENTICATION ============
async function checkAuthentication() {
    const token = localStorage.getItem('weather_ai_token');
    const switchedAccount = localStorage.getItem('switched_account');
    
    console.log('Checking authentication...', { token: token ? 'exists' : 'none', switchedAccount: switchedAccount ? 'exists' : 'none' });
    
    if (!token && !switchedAccount) {
        console.log('No token or switched account, redirecting to login');
        window.location.href = '/login';
        return;
    }
    
    // Clear old dashboard data before loading new user
    clearAllDashboardData();
    
    // Clear any cached API responses
    if ('caches' in window) {
        try {
            const cacheNames = await caches.keys();
            for (const cacheName of cacheNames) {
                await caches.delete(cacheName);
            }
            console.log('✅ Cleared all caches');
        } catch (e) {
            console.log('Error clearing caches:', e);
        }
    }
    
    // If we have a token, verify it with the server
    if (token) {
        try {
            // Add timestamp to prevent caching
            const response = await fetch(`${API_BASE_URL}/api/auth/verify?token=${token}&t=${Date.now()}`, {
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            });
            const result = await response.json();
            
            if (result.valid) {
                currentUser = result.user;
                
                // If this is a switched account, store it
                if (result.user.is_switched) {
                    localStorage.setItem('switched_account', JSON.stringify(result.user));
                }
                
                console.log('✅ Token verified for:', currentUser.full_name);
                
                setTimeout(() => {
                    const loadingScreen = document.getElementById('loading-screen');
                    const dashboardPage = document.getElementById('dashboard-page');
                    
                    if (loadingScreen) loadingScreen.style.display = 'none';
                    if (dashboardPage) dashboardPage.style.display = 'block';
                    
                    initializeDashboard();
                }, 1000);
            } else {
                console.log('Token invalid, clearing storage');
                localStorage.removeItem('weather_ai_token');
                localStorage.removeItem('weather_ai_user');
                localStorage.removeItem('switched_account');
                window.location.href = '/login';
            }
        } catch (error) {
            console.error('Authentication error:', error);
            // Don't redirect immediately, might be network issue
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        }
    } 
    // If we have a switched account but no token (shouldn't happen, but just in case)
    else if (switchedAccount) {
        try {
            currentUser = JSON.parse(switchedAccount);
            console.log('Using cached switched account:', currentUser.full_name);
            
            setTimeout(() => {
                const loadingScreen = document.getElementById('loading-screen');
                const dashboardPage = document.getElementById('dashboard-page');
                
                if (loadingScreen) loadingScreen.style.display = 'none';
                if (dashboardPage) dashboardPage.style.display = 'block';
                
                initializeDashboard();
            }, 1000);
        } catch (e) {
            console.error('Error parsing switched account:', e);
            localStorage.removeItem('switched_account');
            window.location.href = '/login';
        }
    }
}

// Update logout function to clear switched account
function logoutUser() {
    localStorage.removeItem('weather_ai_token');
    localStorage.removeItem('weather_ai_user');
    localStorage.removeItem('user_preferences');
    localStorage.removeItem('switched_account');
    localStorage.removeItem('account_session_token');
    
    const settingsContainer = document.getElementById('settings-container');
    if (settingsContainer) settingsContainer.style.display = 'none';
    
    const userDropdown = document.getElementById('user-dropdown');
    if (userDropdown) userDropdown.style.display = 'none';
    
    document.cookie = "weather_ai_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    
    if (refreshInterval) clearInterval(refreshInterval);
    
    window.location.href = '/login';
}

function initializeDashboard() {
    setupUserInfo();
    setupNavigation();
    setupLogout();
    setupQuickActions();
    setupSearch();
    setupSettings();
    setupSupport();
    loadDashboardData();
    setupWeatherPage();
    setupAnomalyDetection();
    setupHistoryPage();
    setupAnalyticsPage();
    setupAutoRefresh();
    
    window.userProfileManager = new UserProfileManager();
    console.log('✅ Dashboard fully initialized with user profile management');
}

// ============ DASHBOARD DATA LOADING ============
async function loadDashboardData() {
    console.log('📊 Loading dashboard data...');
    
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
        
        // Fetch dashboard stats
        const statsResponse = await fetch(`${API_BASE_URL}/api/analytics/dashboard-stats?_=${timestamp}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
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
        
        // Fetch recent activity
        const activityResponse = await fetch(`${API_BASE_URL}/api/analytics/recent-activity?limit=10&_=${timestamp}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
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
    if (!tableBody) {
        console.error('Activity table body not found!');
        return;
    }
    
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

// ============ USER MANAGEMENT ============

function setupUserInfo() {
    if (currentUser) {
        updateUserDisplay(currentUser);
        
        // Add indicator if using switched account
        if (currentUser.is_switched) {
            const userRole = document.querySelector('.user-role');
            if (userRole) {
                userRole.innerHTML += ' <span class="badge badge-info" style="background: #f59e0b;">Switched</span>';
            }
        }
    }
}

function updateUserDisplay(user) {
    const userNameElement = document.getElementById('user-name');
    const userAvatarElement = document.getElementById('user-avatar');
    
    if (userNameElement && user.full_name) {
        userNameElement.textContent = user.full_name;
    }
    
    if (userAvatarElement && user.full_name) {
        const initials = user.full_name.split(' ')
            .map(n => n[0])
            .join('')
            .toUpperCase()
            .substring(0, 2);
        userAvatarElement.textContent = initials;
    }
}

function setupLogout() {
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function() {
            const token = localStorage.getItem('weather_ai_token');
            
            if (token) {
                try {
                    await fetch(`${API_BASE_URL}/api/auth/logout?token=${token}`);
                } catch (error) {
                    console.error('Logout error:', error);
                }
            }
            
            logoutUser();
        });
    }
}

// ============ NAVIGATION ============
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item:not(#logout-btn)');
    
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            const section = this.getAttribute('data-section');
            
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
            
            showSection(section);
        });
    });
}

function showSection(sectionId) {
    document.querySelectorAll('.page-content').forEach(section => {
        section.style.display = 'none';
    });
    
    const targetSection = document.getElementById(sectionId + '-page');
    if (targetSection) {
        targetSection.style.display = 'block';
        loadSectionData(sectionId);
    }
}

function loadSectionData(sectionId) {
    switch(sectionId) {
        case 'dashboard': loadDashboardData(); break;
        case 'weather': loadPopularCities(); break;
        case 'anomaly': loadAnomalyChart(); break;
        case 'insights': loadInsightsData(); break;
        case 'analytics': loadAnalyticsData(); break;
        case 'settings': loadSettings(); break;
    }
}

// ============ UTILITY FUNCTIONS ============
function setupQuickActions() {
    const actionButtons = document.querySelectorAll('.action-btn[data-action]');
    
    actionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            const navItem = document.querySelector(`.nav-item[data-section="${action}"]`);
            if (navItem) navItem.click();
        });
    });
}

function setupAutoRefresh() {
    const autoRefresh = localStorage.getItem('weather_ai_auto_refresh') !== 'false';
    
    if (autoRefresh) {
        refreshInterval = setInterval(() => {
            const activeSection = document.querySelector('.nav-item.active');
            if (activeSection) {
                const section = activeSection.getAttribute('data-section');
                if (section === 'dashboard') loadDashboardData();
            }
        }, 5 * 60 * 1000);
    }
}

function getBadgeClass(activity) {
    if (activity.is_anomaly) return 'badge-warning';
    if (activity.status === 'Normal' || activity.status === 'Completed') return 'badge-success';
    if (activity.status === 'Error' || activity.status === 'Failed') return 'badge-danger';
    return 'badge-primary';
}

function getWeatherIcon(description) {
    const desc = description.toLowerCase();
    if (desc.includes('sun') || desc.includes('clear')) return 'fas fa-sun';
    if (desc.includes('cloud')) return 'fas fa-cloud';
    if (desc.includes('rain') || desc.includes('drizzle')) return 'fas fa-cloud-rain';
    if (desc.includes('snow')) return 'fas fa-snowflake';
    if (desc.includes('storm') || desc.includes('thunder')) return 'fas fa-bolt';
    if (desc.includes('fog') || desc.includes('mist') || desc.includes('haze')) return 'fas fa-smog';
    if (desc.includes('wind')) return 'fas fa-wind';
    return 'fas fa-cloud-sun';
}

function getWeatherCondition(temp) {
    if (temp < 0) return '❄️ Freezing';
    if (temp < 10) return '🥶 Cold';
    if (temp < 20) return '😊 Cool';
    if (temp < 30) return '😎 Warm';
    return '🔥 Hot';
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        max-width: 400px;
        box-shadow: var(--shadow-lg);
        animation: slideIn 0.3s ease;
    `;
    
    const icon = type === 'success' ? 'check-circle' : 
                type === 'error' ? 'exclamation-circle' : 
                type === 'warning' ? 'exclamation-triangle' : 'info-circle';
    
    alertDiv.innerHTML = `
        <div style="display: flex; align-items: flex-start; gap: 10px;">
            <i class="fas fa-${icon} text-${type}" style="font-size: 18px; margin-top: 2px;"></i>
            <div style="flex: 1;">
                <strong>${type.charAt(0).toUpperCase() + type.slice(1)}:</strong> ${message}
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" style="margin-left: 10px;"></button>
        </div>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) alertDiv.parentNode.removeChild(alertDiv);
    }, 5000);
}

// ============ ENHANCED SEARCH FUNCTIONALITY ============
function setupSearch() {
    const searchInput = document.getElementById('global-search');
    if (!searchInput) return;
    
    // Create search results dropdown
    createSearchDropdown();
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            hideSearchResults();
            return;
        }
        
        searchTimeout = setTimeout(() => performSearch(query), 300);
    });
    
    searchInput.addEventListener('focus', function() {
        if (this.value.trim().length >= 2) {
            performSearch(this.value.trim());
        }
    });
    
    // Close search results when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-box') && !e.target.closest('.search-results-dropdown')) {
            hideSearchResults();
        }
    });
    
    // Handle keyboard navigation in results
    searchInput.addEventListener('keydown', function(e) {
        const results = document.querySelectorAll('.search-result-item');
        const active = document.querySelector('.search-result-item.active');
        let index = Array.from(results).indexOf(active);
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (active) {
                active.classList.remove('active');
                if (results[index + 1]) {
                    results[index + 1].classList.add('active');
                    results[index + 1].scrollIntoView({ block: 'nearest' });
                }
            } else if (results[0]) {
                results[0].classList.add('active');
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (active) {
                active.classList.remove('active');
                if (results[index - 1]) {
                    results[index - 1].classList.add('active');
                    results[index - 1].scrollIntoView({ block: 'nearest' });
                }
            }
        } else if (e.key === 'Enter' && active) {
            e.preventDefault();
            active.click();
        } else if (e.key === 'Escape') {
            hideSearchResults();
        }
    });
}

function createSearchDropdown() {
    const searchBox = document.querySelector('.search-box');
    if (!searchBox) return;
    
    // Remove existing dropdown if any
    const existingDropdown = document.querySelector('.search-results-dropdown');
    if (existingDropdown) existingDropdown.remove();
    
    const dropdown = document.createElement('div');
    dropdown.className = 'search-results-dropdown';
    dropdown.style.cssText = `
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        margin-top: 8px;
        max-height: 400px;
        overflow-y: auto;
        z-index: 1000;
        display: none;
        border: 1px solid rgba(0,0,0,0.05);
    `;
    
    searchBox.style.position = 'relative';
    searchBox.appendChild(dropdown);
}

function hideSearchResults() {
    const dropdown = document.querySelector('.search-results-dropdown');
    if (dropdown) dropdown.style.display = 'none';
}

async function performSearch(query) {
    const dropdown = document.querySelector('.search-results-dropdown');
    if (!dropdown) return;
    
    // Show loading state
    dropdown.innerHTML = `
        <div style="padding: 20px; text-align: center; color: var(--text-muted);">
            <i class="fas fa-spinner fa-spin"></i> Searching for "${query}"...
        </div>
    `;
    dropdown.style.display = 'block';
    
    try {
        // Search in multiple sources
        const [cityResults, historyResults, anomalyResults] = await Promise.all([
            searchCities(query),
            searchHistory(query),
            searchAnomalies(query)
        ]);
        
        const allResults = {
            cities: cityResults,
            history: historyResults,
            anomalies: anomalyResults
        };
        
        dropdown.innerHTML = `
            <div style="padding: 10px;">
                ${renderSearchResults(allResults, query)}
            </div>
        `;
        
        // Add click handlers to results
        dropdown.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', function(e) {
                const action = this.dataset.action;
                const value = this.dataset.value;
                const country = this.dataset.country;
                const section = this.dataset.section;
                
                handleSearchResultClick(action, value, country, section);
                hideSearchResults();
                document.getElementById('global-search').value = '';
            });
        });
        
        // Add click handlers to quick actions
        dropdown.querySelectorAll('.search-quick-action').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const action = this.dataset.action;
                const value = this.dataset.value;
                
                handleQuickAction(action, value);
                hideSearchResults();
                document.getElementById('global-search').value = '';
            });
        });
        
    } catch (error) {
        console.error('Search error:', error);
        dropdown.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #f72585;">
                <i class="fas fa-exclamation-circle"></i> Error performing search
                <p style="font-size: 12px; margin-top: 5px;">${error.message}</p>
            </div>
        `;
    }
}

async function searchCities(query) {
    const results = [];
    const lowercaseQuery = query.toLowerCase();
    
    try {
        // Try to get cities from API
        const token = localStorage.getItem('weather_ai_token');
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        
        // First check if we can search via API
        const response = await fetch(`${API_BASE_URL}/api/cities/search?q=${encodeURIComponent(query)}`, { headers });
        
        if (response.ok) {
            const data = await response.json();
            if (data.cities && data.cities.length > 0) {
                data.cities.forEach(city => {
                    results.push({
                        type: 'city',
                        title: city.name,
                        subtitle: city.country || 'International',
                        icon: 'fa-city',
                        action: 'check-weather',
                        value: city.name,
                        country: city.country || '',
                        section: 'weather'
                    });
                });
            }
        }
    } catch (error) {
        console.log('API search not available, using local data');
    }
    
    // Always include popular cities as fallback
    const popularCities = [
        { name: 'London', country: 'UK' },
        { name: 'New York', country: 'US' },
        { name: 'Tokyo', country: 'JP' },
        { name: 'Dubai', country: 'AE' },
        { name: 'Paris', country: 'FR' },
        { name: 'Sydney', country: 'AU' },
        { name: 'Berlin', country: 'DE' },
        { name: 'Mumbai', country: 'IN' },
        { name: 'Singapore', country: 'SG' },
        { name: 'Hong Kong', country: 'HK' },
        { name: 'Los Angeles', country: 'US' },
        { name: 'Chicago', country: 'US' },
        { name: 'Toronto', country: 'CA' },
        { name: 'Mexico City', country: 'MX' },
        { name: 'São Paulo', country: 'BR' },
        { name: 'Moscow', country: 'RU' },
        { name: 'Istanbul', country: 'TR' },
        { name: 'Seoul', country: 'KR' },
        { name: 'Bangkok', country: 'TH' },
        { name: 'Cairo', country: 'EG' },
        { name: 'Taxila', country: 'PK' },
        { name: 'Islamabad', country: 'PK' },
        { name: 'Lahore', country: 'PK' },
        { name: 'Karachi', country: 'PK' }
    ];
    
    popularCities.forEach(city => {
        if (city.name.toLowerCase().includes(lowercaseQuery) && 
            !results.some(r => r.title === city.name)) {
            results.push({
                type: 'city',
                title: city.name,
                subtitle: city.country,
                icon: 'fa-city',
                action: 'check-weather',
                value: city.name,
                country: city.country,
                section: 'weather'
            });
        }
    });
    
    // Add current input as a search option if not in results
    if (!results.some(r => r.title.toLowerCase() === lowercaseQuery)) {
        results.push({
            type: 'city',
            title: query,
            subtitle: 'Search this city',
            icon: 'fa-search',
            action: 'check-weather',
            value: query,
            country: '',
            section: 'weather'
        });
    }
    
    return results;
}

async function searchHistory(query) {
    const results = [];
    const lowercaseQuery = query.toLowerCase();
    
    try {
        // Try to get real history data from API
        const token = localStorage.getItem('weather_ai_token');
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        
        const response = await fetch(`${API_BASE_URL}/api/analytics/recent-activity?limit=20`, { headers });
        
        if (response.ok) {
            const data = await response.json();
            if (data.activities && data.activities.length > 0) {
                data.activities.forEach(activity => {
                    const city = activity.city || '';
                    const activityType = activity.activity_type || '';
                    const status = activity.status || '';
                    const timestamp = activity.timestamp || '';
                    
                    if (city.toLowerCase().includes(lowercaseQuery) || 
                        activityType.toLowerCase().includes(lowercaseQuery)) {
                        results.push({
                            type: 'history',
                            title: city,
                            subtitle: `${activityType} - ${status}`,
                            icon: 'fa-history',
                            action: 'view-history',
                            value: city,
                            section: 'history',
                            timestamp: timestamp
                        });
                    }
                });
            }
        }
    } catch (error) {
        console.log('History API not available, using local data');
    }
    
    // Check activity table in dashboard
    const activityRows = document.querySelectorAll('#activity-table-body tr');
    
    activityRows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 5) {
            const city = cells[1]?.textContent.trim() || '';
            const activity = cells[2]?.textContent.trim() || '';
            const status = cells[3]?.textContent.trim() || '';
            const details = cells[4]?.textContent.trim() || '';
            
            if (city.toLowerCase().includes(lowercaseQuery) || 
                activity.toLowerCase().includes(lowercaseQuery) ||
                details.toLowerCase().includes(lowercaseQuery)) {
                
                if (!results.some(r => r.title === city && r.subtitle.includes(activity))) {
                    results.push({
                        type: 'history',
                        title: city,
                        subtitle: `${activity} - ${status}`,
                        icon: 'fa-history',
                        action: 'view-history',
                        value: city,
                        section: 'history'
                    });
                }
            }
        }
    });
    
    return results;
}

async function searchAnomalies(query) {
    const results = [];
    const lowercaseQuery = query.toLowerCase();
    
    // Check anomaly page inputs
    const anomalyCity = document.getElementById('anomaly-city-input')?.value || '';
    
    if (anomalyCity && anomalyCity.toLowerCase().includes(lowercaseQuery)) {
        // Check if there's an anomaly detected
        const anomalyHeader = document.querySelector('.anomaly-header h3')?.textContent || '';
        const isAnomaly = anomalyHeader.includes('Anomaly') || anomalyHeader.includes('⚠️');
        
        results.push({
            type: 'anomaly',
            title: anomalyCity,
            subtitle: isAnomaly ? '⚠️ Anomaly detected' : 'No anomalies detected',
            icon: 'fa-exclamation-triangle',
            action: 'view-anomaly',
            value: anomalyCity,
            section: 'anomaly',
            badge: isAnomaly ? 'Active' : 'Normal'
        });
    }
    
    // Check future anomalies table
    const futureRows = document.querySelectorAll('#future-anomalies-table-body tr');
    futureRows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 8) {
            const date = cells[0]?.textContent.trim() || '';
            const day = cells[1]?.textContent.trim() || '';
            const temp = cells[2]?.textContent.trim() || '';
            const type = cells[4]?.textContent.trim() || '';
            const severity = cells[5]?.textContent.trim() || '';
            
            const rowText = row.textContent.toLowerCase();
            if (rowText.includes(lowercaseQuery) && type !== 'None') {
                results.push({
                    type: 'anomaly',
                    title: `${anomalyCity || 'Weather'} - ${date}`,
                    subtitle: `${type} (${severity}) - ${temp}`,
                    icon: 'fa-exclamation-triangle',
                    action: 'view-anomaly',
                    value: anomalyCity || query,
                    date: date,
                    section: 'anomaly',
                    badge: severity
                });
            }
        }
    });
    
    // Check for anomaly badges in activity table
    const activityRows = document.querySelectorAll('#activity-table-body tr');
    activityRows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 5) {
            const city = cells[1]?.textContent.trim() || '';
            const details = cells[4]?.textContent.trim() || '';
            
            if ((city.toLowerCase().includes(lowercaseQuery) || details.toLowerCase().includes('anomaly')) && 
                details.includes('Anomaly')) {
                results.push({
                    type: 'anomaly',
                    title: city,
                    subtitle: 'Previous anomaly detected',
                    icon: 'fa-exclamation-triangle',
                    action: 'view-anomaly',
                    value: city,
                    section: 'anomaly',
                    badge: 'Past'
                });
            }
        }
    });
    
    return results;
}

function renderSearchResults(groupedResults, query) {
    const totalResults = groupedResults.cities.length + groupedResults.history.length + groupedResults.anomalies.length;
    
    if (totalResults === 0) {
        return `
            <div class="search-no-results">
                <i class="fas fa-map-marker-alt search-no-results-icon"></i>
                <p class="search-no-results-title">No results found for "${query}"</p>
                <p class="search-no-results-subtitle">Try searching for a city or check weather data first</p>
                
                <div class="search-quick-actions-vertical">
                    <button class="search-quick-action" data-action="weather" data-value="${query}">
                        <i class="fas fa-search"></i>
                        <span>Check weather in "${query}"</span>
                    </button>
                    <button class="search-quick-action" data-action="anomaly" data-value="${query}">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span>Detect anomalies in "${query}"</span>
                    </button>
                    <button class="search-quick-action" data-action="history" data-value="${query}">
                        <i class="fas fa-history"></i>
                        <span>View history for "${query}"</span>
                    </button>
                </div>
            </div>
        `;
    }
    
    let html = '<div class="search-results-container">';
    
    // Quick actions section
    html += `
        <div class="search-section quick-actions-section">
            <div class="search-section-header">
                <i class="fas fa-bolt"></i>
                <span>Quick Actions</span>
            </div>
            <div class="quick-actions-grid">
                <button class="search-quick-action" data-action="weather" data-value="${query}">
                    <i class="fas fa-search"></i>
                    <span>Check "${query}"</span>
                </button>
                <button class="search-quick-action" data-action="anomaly" data-value="${query}">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>Detect Anomalies</span>
                </button>
            </div>
        </div>
    `;
    
    // Cities results
    if (groupedResults.cities.length > 0) {
        html += `
            <div class="search-section">
                <div class="search-section-header">
                    <i class="fas fa-city"></i>
                    <span>Cities (${groupedResults.cities.length})</span>
                </div>
                <div class="search-results-list">
        `;
        
        groupedResults.cities.slice(0, 5).forEach(result => {
            html += `
                <div class="search-result-item" 
                     data-action="${result.action}" 
                     data-value="${result.value}" 
                     data-country="${result.country || ''}"
                     data-section="${result.section}">
                    <div class="result-icon city-icon">
                        <i class="fas ${result.icon}"></i>
                    </div>
                    <div class="result-content">
                        <div class="result-title">${result.title}</div>
                        <div class="result-subtitle">
                            ${result.country ? `<span class="country-flag">${getFlagEmoji(result.country)}</span>` : ''}
                            ${result.country || 'International'}
                        </div>
                    </div>
                    <i class="fas fa-chevron-right result-arrow"></i>
                </div>
            `;
        });
        
        if (groupedResults.cities.length > 5) {
            html += `<div class="search-more">+${groupedResults.cities.length - 5} more cities</div>`;
        }
        
        html += `</div></div>`;
    }
    
    // Anomaly results
    if (groupedResults.anomalies.length > 0) {
        html += `
            <div class="search-section">
                <div class="search-section-header">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>Anomaly Detections (${groupedResults.anomalies.length})</span>
                </div>
                <div class="search-results-list">
        `;
        
        groupedResults.anomalies.slice(0, 3).forEach(result => {
            const badgeClass = result.badge === 'Critical' ? 'badge-critical' : 
                              result.badge === 'High' ? 'badge-high' : 
                              result.badge === 'Medium' ? 'badge-medium' : 
                              result.badge === 'Past' ? 'badge-past' : 'badge-normal';
            
            html += `
                <div class="search-result-item anomaly-item" 
                     data-action="${result.action}" 
                     data-value="${result.value}" 
                     data-date="${result.date || ''}"
                     data-section="${result.section}">
                    <div class="result-icon anomaly-icon">
                        <i class="fas ${result.icon}"></i>
                    </div>
                    <div class="result-content">
                        <div class="result-title">${result.title}</div>
                        <div class="result-subtitle">${result.subtitle}</div>
                    </div>
                    ${result.badge ? `<span class="result-badge ${badgeClass}">${result.badge}</span>` : ''}
                </div>
            `;
        });
        
        html += `</div></div>`;
    }
    
    // History results
    if (groupedResults.history.length > 0) {
        html += `
            <div class="search-section">
                <div class="search-section-header">
                    <i class="fas fa-history"></i>
                    <span>Recent Activity (${groupedResults.history.length})</span>
                </div>
                <div class="search-results-list">
        `;
        
        groupedResults.history.slice(0, 3).forEach(result => {
            // Format timestamp to be more readable
            let displayTime = result.timestamp || '';
            if (displayTime) {
                try {
                    const date = new Date(displayTime);
                    const now = new Date();
                    const diffMs = now - date;
                    const diffMins = Math.floor(diffMs / 60000);
                    
                    if (diffMins < 1) displayTime = 'Just now';
                    else if (diffMins < 60) displayTime = `${diffMins}m ago`;
                    else if (diffMins < 1440) displayTime = `${Math.floor(diffMins / 60)}h ago`;
                    else displayTime = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                } catch {
                    displayTime = result.timestamp;
                }
            }
            
            html += `
                <div class="search-result-item" 
                     data-action="${result.action}" 
                     data-value="${result.value}" 
                     data-section="${result.section}">
                    <div class="result-icon history-icon">
                        <i class="fas ${result.icon}"></i>
                    </div>
                    <div class="result-content">
                        <div class="result-title">${result.title}</div>
                        <div class="result-subtitle">${result.subtitle}</div>
                    </div>
                    ${displayTime ? `<span class="result-time">${displayTime}</span>` : ''}
                </div>
            `;
        });
        
        html += `</div></div>`;
    }
    
    html += '</div>';
    return html;
}

// Helper function for flag emoji
function getFlagEmoji(countryCode) {
    if (!countryCode) return '🌍';
    const codePoints = countryCode
        .toUpperCase()
        .split('')
        .map(char => 127397 + char.charCodeAt());
    return String.fromCodePoint(...codePoints);
}

function handleSearchResultClick(action, value, country, section) {
    switch(action) {
        case 'check-weather':
            // Switch to weather page and load the city
            const weatherNav = document.querySelector(`.nav-item[data-section="weather"]`);
            if (weatherNav) {
                weatherNav.click();
                setTimeout(() => {
                    const cityInput = document.getElementById('weather-city-input');
                    const countryInput = document.getElementById('weather-country-input');
                    if (cityInput) {
                        cityInput.value = value;
                        if (country && countryInput) {
                            countryInput.value = country;
                        }
                        getWeatherData();
                    }
                }, 300);
            }
            break;
            
        case 'view-history':
            // Switch to history page and load city history
            const historyNav = document.querySelector(`.nav-item[data-section="history"]`);
            if (historyNav) {
                historyNav.click();
                setTimeout(() => {
                    const historyInput = document.getElementById('history-city-input');
                    if (historyInput) {
                        historyInput.value = value;
                        loadWeatherHistory();
                    }
                }, 300);
            }
            break;
            
        case 'view-anomaly':
            // Switch to anomaly page and detect for city
            const anomalyNav = document.querySelector(`.nav-item[data-section="anomaly"]`);
            if (anomalyNav) {
                anomalyNav.click();
                setTimeout(() => {
                    const anomalyInput = document.getElementById('anomaly-city-input');
                    const countryInput = document.getElementById('anomaly-country-input');
                    if (anomalyInput) {
                        anomalyInput.value = value;
                        if (country && countryInput) {
                            countryInput.value = country;
                        }
                        detectAnomalies();
                    }
                }, 300);
            }
            break;
    }
}

function handleQuickAction(action, value) {
    switch(action) {
        case 'weather':
            const weatherNav = document.querySelector(`.nav-item[data-section="weather"]`);
            if (weatherNav) {
                weatherNav.click();
                setTimeout(() => {
                    const cityInput = document.getElementById('weather-city-input');
                    if (cityInput) {
                        cityInput.value = value;
                        getWeatherData();
                    }
                }, 300);
            }
            break;
            
        case 'anomaly':
            const anomalyNav = document.querySelector(`.nav-item[data-section="anomaly"]`);
            if (anomalyNav) {
                anomalyNav.click();
                setTimeout(() => {
                    const anomalyInput = document.getElementById('anomaly-city-input');
                    if (anomalyInput) {
                        anomalyInput.value = value;
                        detectAnomalies();
                    }
                }, 300);
            }
            break;
            
        case 'history':
            const historyNav = document.querySelector(`.nav-item[data-section="history"]`);
            if (historyNav) {
                historyNav.click();
                setTimeout(() => {
                    const historyInput = document.getElementById('history-city-input');
                    if (historyInput) {
                        historyInput.value = value;
                        loadWeatherHistory();
                    }
                }, 300);
            }
            break;
    }
}

// Add styles for search results
function addSearchStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .search-result-item:hover {
            background: rgba(26, 107, 179, 0.05);
        }
        
        .search-result-item.active {
            background: rgba(26, 107, 179, 0.1);
            border-left: 3px solid #1a6bb3;
        }
        
        .search-quick-action {
            padding: 10px;
            background: rgba(26, 107, 179, 0.05);
            border: 1px solid rgba(26, 107, 179, 0.1);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 13px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s;
            width: 100%;
        }
        
        .search-quick-action:hover {
            background: rgba(26, 107, 179, 0.1);
            border-color: #1a6bb3;
        }
        
        .search-quick-action i {
            color: #1a6bb3;
            font-size: 14px;
        }
        
        /* Scrollbar styling */
        .search-results-dropdown::-webkit-scrollbar {
            width: 6px;
        }
        
        .search-results-dropdown::-webkit-scrollbar-track {
            background: rgba(0,0,0,0.05);
            border-radius: 3px;
        }
        
        .search-results-dropdown::-webkit-scrollbar-thumb {
            background: rgba(0,0,0,0.2);
            border-radius: 3px;
        }
        
        .search-results-dropdown::-webkit-scrollbar-thumb:hover {
            background: rgba(0,0,0,0.3);
        }
        
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            .search-results-dropdown {
                background: #1e293b;
                border-color: rgba(255,255,255,0.1);
            }
            
            .search-result-item:hover {
                background: rgba(255,255,255,0.05);
            }
            
            .search-result-item.active {
                background: rgba(26, 107, 179, 0.2);
            }
            
            .search-quick-action {
                background: rgba(255,255,255,0.05);
                border-color: rgba(255,255,255,0.1);
                color: #e2e8f0;
            }
            
            .search-quick-action:hover {
                background: rgba(26, 107, 179, 0.2);
                border-color: #1a6bb3;
            }
        }
    `;
    document.head.appendChild(style);
}

// ============ PLACEHOLDER FUNCTIONS (to be implemented in other files) ============
function setupSettings() { console.log('Settings setup'); }
function setupSupport() { console.log('Support setup'); }
function loadPopularCities() { console.log('Loading popular cities'); }
function loadAnomalyChart() { console.log('Loading anomaly chart'); }
function loadInsightsData() { console.log('Loading insights'); }
function loadAnalyticsData() { console.log('Loading analytics'); }
function loadSettings() { console.log('Loading settings'); }
function setupWeatherPage() { console.log('Weather page setup'); }
function setupAnomalyDetection() { console.log('Anomaly detection setup'); }
function setupHistoryPage() { console.log('History page setup'); }
function setupAnalyticsPage() { console.log('Analytics page setup'); }
function getWeatherData() { console.log('Getting weather data'); }
function loadWeatherHistory() { console.log('Loading weather history'); }
function detectAnomalies() { console.log('Detecting anomalies'); }