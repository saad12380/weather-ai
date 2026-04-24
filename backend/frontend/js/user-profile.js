// ============ USER PROFILE MANAGER ============
class UserProfileManager {
    constructor() {
        this.dropdown = document.getElementById('user-dropdown');
        this.dropdownAvatar = document.getElementById('dropdown-avatar');
        this.dropdownName = document.getElementById('dropdown-name');
        this.dropdownEmail = document.getElementById('dropdown-email');
        this.dropdownRole = document.getElementById('dropdown-role');
        this.dropdownStatus = document.getElementById('dropdown-status');
        this.userProfileBtn = document.getElementById('user-profile');
        this.userAvatar = document.getElementById('user-avatar');
        this.userName = document.getElementById('user-name');
        this.isDropdownOpen = false;
        this.userData = null;
        this.userPreferences = null;
        this.usageStats = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadUserProfile();
    }
    
    setupEventListeners() {
        if (this.userProfileBtn) {
            this.userProfileBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleDropdown();
            });
        }
        
        document.addEventListener('click', (e) => {
            if (this.userProfileBtn && !this.userProfileBtn.contains(e.target) && 
                this.dropdown && !this.dropdown.contains(e.target)) {
                this.closeDropdown();
            }
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isDropdownOpen) this.closeDropdown();
        });
        
        this.setupDropdownActions();
    }
    
    toggleDropdown() {
        this.isDropdownOpen = !this.isDropdownOpen;
        
        if (this.isDropdownOpen) {
            if (window.innerWidth <= 768) {
                this.openMobileDropdown();
            } else {
                this.dropdown.style.display = 'block';
            }
        } else {
            // ALWAYS clean up mobile overlay when closing
            this.cleanupMobileDropdown();
            this.dropdown.style.display = 'none';
        }
        
        this.updateDropdownChevron(this.isDropdownOpen);
    }

    openMobileDropdown() {
        // Remove any existing overlay first
        this.cleanupMobileDropdown();
        
        // Create new overlay
        const overlay = document.createElement('div');
        overlay.id = 'dropdown-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 9998;
        `;
        overlay.addEventListener('click', () => {
            this.closeDropdown();
        });
        document.body.appendChild(overlay);
        
        // Show dropdown as centered modal
        this.dropdown.style.display = 'block';
        this.dropdown.style.cssText = `
            position: fixed !important;
            top: 50% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            bottom: auto !important;
            right: auto !important;
            width: 90% !important;
            max-width: 340px !important;
            max-height: 80vh !important;
            border-radius: 16px !important;
            box-shadow: 0 20px 60px rgba(0,0,0,0.4) !important;
            z-index: 9999 !important;
        `;
        
        // Add animation if not exists
        if (!document.getElementById('modal-animation')) {
            const style = document.createElement('style');
            style.id = 'modal-animation';
            style.textContent = `
                @keyframes modalPopIn {
                    from { opacity: 0; transform: translate(-50%, -50%) scale(0.9); }
                    to { opacity: 1; transform: translate(-50%, -50%) scale(1); }
                }
            `;
            document.head.appendChild(style);
        }
    }

    cleanupMobileDropdown() {
        // Remove overlay
        const overlay = document.getElementById('dropdown-overlay');
        if (overlay) {
            overlay.remove();
        }
        // Reset dropdown inline styles
        if (this.dropdown) {
            this.dropdown.style.cssText = '';
        }
    }

    closeDropdown() {
        this.isDropdownOpen = false;
        // ALWAYS clean up mobile state
        this.cleanupMobileDropdown();
        this.dropdown.style.display = 'none';
        this.updateDropdownChevron(false);
    }
    
    updateDropdownChevron(isOpen) {
        const chevron = this.userProfileBtn?.querySelector('.fa-chevron-down');
        if (chevron) chevron.style.transform = isOpen ? 'rotate(180deg)' : 'rotate(0)';
    }
    async loadUserProfile() {
    try {
        const token = localStorage.getItem('weather_ai_token');
        if (!token) return;
        
        const response = await fetch(`${API_BASE_URL}/api/user/profile`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            this.userData = data.user;
            this.userPreferences = data.preferences || {};
            this.usageStats = data.usage_stats || {};
            
            // Make sure email_2fa_enabled is set
            if (this.userPreferences.email_2fa_enabled === undefined) {
                this.userPreferences.email_2fa_enabled = false;
            }
            
            // Try to get Gravatar image if no profile picture
            if (!this.userData.profile_picture && this.userData.email) {
                await this.fetchGravatarImage(this.userData.email);
            }
            
            this.updateUserDisplay();
            this.updateDropdownContent();
        } else {
            console.error('Failed to load user profile:', response.status);
            this.setFallbackUserData();
        }
    } catch (error) {
        console.error('Error loading user profile:', error);
        this.setFallbackUserData();
    }
}
    
    async fetchGravatarImage(email) {
    if (!email) return;
    
    const emailHash = this.md5(email.trim().toLowerCase());
    const gravatarUrl = `https://www.gravatar.com/avatar/${emailHash}?s=200&d=identicon`;
    
    return new Promise((resolve) => {
        const img = new Image();
        img.crossOrigin = 'anonymous'; // Add this line
        img.onload = () => {
            this.userData.profile_picture = gravatarUrl;
            this.updateUserDisplay();
            this.updateDropdownContent();
            resolve(gravatarUrl);
        };
        img.onerror = () => {
            resolve(null);
        };
        img.src = gravatarUrl;
    });
}
    
    // Simple MD5 hash function for Gravatar
    md5(string) {
        let hash = 0;
        for (let i = 0; i < string.length; i++) {
            const char = string.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return Math.abs(hash).toString(16).padStart(32, '0');
    }
    
    async uploadProfilePicture(file) {
        try {
            const token = localStorage.getItem('weather_ai_token');
            if (!token) {
                showAlert('Please login again', 'error');
                return;
            }

            const formData = new FormData();
            formData.append('profile_picture', file);

            const response = await fetch(`${API_BASE_URL}/api/user/profile/picture`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                this.userData.profile_picture = data.profile_picture_url;
                this.updateUserDisplay();
                this.updateDropdownContent();
                showAlert('Profile picture updated successfully!', 'success');
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to upload picture');
            }
        } catch (error) {
            console.error('Error uploading profile picture:', error);
            showAlert(error.message || 'Failed to upload profile picture', 'error');
        }
    }
    
  updateUserDisplay() {
    if (!this.userData) return;
    
    if (this.userName) {
        this.userName.textContent = this.userData.full_name || 'User';
    }
    
    if (this.userAvatar) {
        if (this.userData.profile_picture) {
            // Create an img element with crossorigin attribute
            const img = document.createElement('img');
            img.src = this.userData.profile_picture;
            img.alt = "Profile";
            img.style.width = "100%";
            img.style.height = "100%";
            img.style.borderRadius = "50%";
            img.style.objectFit = "cover";
            img.crossOrigin = "anonymous"; // Add this line
            
            // Handle loading errors
            img.onerror = () => {
                console.log('Failed to load profile image, using initials');
                this.userAvatar.innerHTML = this.getInitials(this.userData.full_name || 'User');
            };
            
            // Clear and append new image
            this.userAvatar.innerHTML = '';
            this.userAvatar.appendChild(img);
        } else {
            const initials = this.getInitials(this.userData.full_name || 'User');
            this.userAvatar.textContent = initials;
        }
    }
    
    this.updateDropdownContent();
}

updateDropdownContent() {
    if (!this.userData) return;
    
    if (this.dropdownAvatar) {
        if (this.userData.profile_picture) {
            const img = document.createElement('img');
            img.src = this.userData.profile_picture;
            img.alt = "Profile";
            img.style.width = "100%";
            img.style.height = "100%";
            img.style.borderRadius = "50%";
            img.style.objectFit = "cover";
            img.crossOrigin = "anonymous"; // Add this line
            
            img.onerror = () => {
                console.log('Failed to load profile image in dropdown, using initials');
                this.dropdownAvatar.innerHTML = this.getInitials(this.userData.full_name || 'User');
            };
            
            this.dropdownAvatar.innerHTML = '';
            this.dropdownAvatar.appendChild(img);
        } else {
            const initials = this.getInitials(this.userData.full_name || 'User');
            this.dropdownAvatar.textContent = initials;
        }
    }
    
    if (this.dropdownName) this.dropdownName.textContent = this.userData.full_name || 'User';
    if (this.dropdownEmail) this.dropdownEmail.textContent = this.userData.email || 'user@example.com';
    if (this.dropdownRole) this.dropdownRole.textContent = this.userData.account_type || 'User';
    
    if (this.dropdownStatus) {
        const lastLogin = this.userData.last_login ? new Date(this.userData.last_login) : new Date();
        const now = new Date();
        const hoursSinceLogin = (now - lastLogin) / (1000 * 60 * 60);
        
        if (hoursSinceLogin < 0.5) {
            this.dropdownStatus.innerHTML = '<span class="online-dot"></span> Online';
            this.dropdownStatus.className = 'status-indicator online';
        } else if (hoursSinceLogin < 24) {
            this.dropdownStatus.innerHTML = `<span class="away-dot"></span> Active ${Math.floor(hoursSinceLogin)}h ago`;
            this.dropdownStatus.className = 'status-indicator away';
        } else {
            this.dropdownStatus.innerHTML = '<span class="offline-dot"></span> Offline';
            this.dropdownStatus.className = 'status-indicator offline';
        }
    }
}
    
    setupDropdownActions() {
        const quickWeather = document.getElementById('quick-weather');
        if (quickWeather) {
            quickWeather.addEventListener('click', (e) => { 
                e.preventDefault(); 
                this.closeDropdown(); 
                if (typeof showSection === 'function') showSection('weather');
            });
        }
        
        const quickAnalytics = document.getElementById('quick-analytics');
        if (quickAnalytics) {
            quickAnalytics.addEventListener('click', (e) => { 
                e.preventDefault(); 
                this.closeDropdown(); 
                if (typeof showSection === 'function') showSection('analytics');
            });
        }
        
        const exportData = document.getElementById('export-data');
        if (exportData) {
            exportData.addEventListener('click', (e) => { 
                e.preventDefault(); 
                this.closeDropdown(); 
                this.exportUserData(); 
            });
        }
        
        document.querySelectorAll('.dropdown-item[data-section]').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const section = e.currentTarget.getAttribute('data-section');
                
                // Close dropdown completely first
                this.isDropdownOpen = false;
                this.dropdown.style.display = 'none';
                this.cleanupMobileDropdown();
                this.updateDropdownChevron(false);
                
                // Small delay to let DOM update, then open settings
                setTimeout(() => {
                    this.openSettingsPage(section);
                }, 200);
            });
        });
        
        const docsLink = document.getElementById('docs-link');
        if (docsLink) {
            docsLink.addEventListener('click', (e) => { 
                e.preventDefault(); 
                window.open('https://docs.weatherai.com', '_blank'); 
            });
        }
        
        const feedbackLink = document.getElementById('feedback-link');
        if (feedbackLink) {
            feedbackLink.addEventListener('click', (e) => { 
                e.preventDefault(); 
                this.openFeedbackModal(); 
            });
        }
        
        const switchAccount = document.getElementById('switch-account');
if (switchAccount) {
    switchAccount.addEventListener('click', (e) => { 
        e.preventDefault(); 
        this.showAccountSwitcher(); 
    });
}
        
        const dropdownLogout = document.getElementById('dropdown-logout');
        if (dropdownLogout) {
            dropdownLogout.addEventListener('click', (e) => { 
                e.preventDefault(); 
                this.closeDropdown(); 
                if (typeof logoutUser === 'function') logoutUser(); 
            });
        }
    }
    
    async openSettingsPage(section) {
        // FORCE close dropdown - reset everything
        this.isDropdownOpen = false;
        
        // Remove overlay
        const overlay = document.getElementById('dropdown-overlay');
        if (overlay) overlay.remove();
        
        // Force reset dropdown completely
        if (this.dropdown) {
            this.dropdown.style.display = 'none';
            this.dropdown.style.cssText = '';
            this.dropdown.removeAttribute('style');
            this.dropdown.style.display = 'none';
        }
        
        this.updateDropdownChevron(false);
        
        // Add settings-open class
        document.body.classList.add('settings-open');
        
        // Hide ONLY page-content sections
        document.querySelectorAll('.page-content').forEach(page => {
            page.style.display = 'none';
        });
        
        // Show settings container
        const settingsContainer = document.getElementById('settings-container');
        if (settingsContainer) {
            settingsContainer.style.display = 'block';
            settingsContainer.style.marginTop = '0';
            settingsContainer.style.paddingTop = '10px';
        }
        
        // Load settings page
        await this.loadSettingsPage(section);
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
        
        // Update nav
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        const dashboardNav = document.querySelector('.nav-item[data-section="dashboard"]');
        if (dashboardNav) {
            dashboardNav.classList.add('active');
        }
    }
        
    
   async loadSettingsPage(section) {
        // Hide all settings pages first
        document.querySelectorAll('.settings-page').forEach(page => {
            page.style.display = 'none';
            page.classList.remove('active');
        });
        
        let pageContent = '';
        let pageTitle = '';
        
        switch(section) {
            case 'preferences':
                pageContent = await this.getPreferencesPageContent();
                pageTitle = 'Account Preferences';
                break;
            case 'profile':
                pageContent = await this.getProfilePageContent();
                pageTitle = 'Profile Settings';
                break;
            case 'units':
                pageContent = await this.getUnitsPageContent();
                pageTitle = 'Data Units';
                break;
            case 'notifications':
                pageContent = await this.getNotificationsPageContent();
                pageTitle = 'Notifications';
                break;
            case 'security':
                pageContent = await this.getSecurityPageContent();
                pageTitle = 'Security Settings';
                break;
            case 'api-keys':
                pageContent = await this.getApiKeysPageContent();
                pageTitle = 'API Keys';
                break;
            case 'usage':
                pageContent = await this.getUsagePageContent();
                pageTitle = 'Usage Statistics';
                break;
            case 'billing':
                pageContent = await this.getBillingPageContent();
                pageTitle = 'Billing & Subscription';
                break;
        }
        
        // Get or create the settings page container
        let pageContainer = document.getElementById(`${section}-page`);
        if (!pageContainer) {
            pageContainer = document.createElement('div');
            pageContainer.id = `${section}-page`;
            pageContainer.className = 'settings-page';
            document.getElementById('settings-container').appendChild(pageContainer);
        }
        
        // Build header HTML WITHOUT onclick - we'll use a class selector instead
        pageContainer.innerHTML = `
            <div class="settings-header" style="margin-bottom: 30px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h1 class="page-title" style="font-size: 28px; margin-bottom: 5px;">${pageTitle}</h1>
                        <p class="page-subtitle" style="color: var(--text-secondary);">Manage your ${pageTitle.toLowerCase()}</p>
                    </div>
                    <button class="btn btn-secondary back-to-dashboard-btn" style="display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-arrow-left"></i>
                        Back to Dashboard
                    </button>
                </div>
            </div>
            ${pageContent}
        `;
        
        // Show this page
        pageContainer.style.display = 'block';
        pageContainer.classList.add('active');
        
        // Use event delegation - attach ONE listener to the settings container
        this.setupBackButtonHandler();
        
        // Setup listeners for this specific page
        this.setupSettingsPageListeners(section);
    }
    

    setupBackButtonHandler() {
        const settingsContainer = document.getElementById('settings-container');
        if (!settingsContainer) return;
        
        // Remove old handler if exists
        if (this._backButtonHandler) {
            settingsContainer.removeEventListener('click', this._backButtonHandler);
        }
        
        // Create new handler
        this._backButtonHandler = (e) => {
            const backBtn = e.target.closest('.back-to-dashboard-btn');
            if (backBtn) {
                e.preventDefault();
                e.stopPropagation();
                this.closeSettings();
            }
        };
        
        // Attach to settings container (event delegation)
        settingsContainer.addEventListener('click', this._backButtonHandler);
    }
    async getProfilePageContent() {
        await this.loadUserProfile();
        
        return `
            <div class="settings-section">
                <h3 class="section-title"><i class="fas fa-user"></i> Personal Information</h3>
                
                <div class="profile-picture-section" style="text-align: center; margin-bottom: 30px;">
                    <div class="profile-picture-container" style="position: relative; display: inline-block;">
                        <div id="current-profile-pic" style="width: 120px; height: 120px; border-radius: 50%; background: var(--gradient-primary); display: flex; align-items: center; justify-content: center; font-size: 40px; color: white; margin: 0 auto; overflow: hidden; border: 4px solid var(--primary-color); box-shadow: 0 4px 15px rgba(26, 107, 179, 0.3);">
                            ${this.userData.profile_picture ? 
                                `<img src="${this.userData.profile_picture}" alt="Profile" style="width: 100%; height: 100%; object-fit: cover;">` : 
                                this.getInitials(this.userData.full_name || 'User')
                            }
                        </div>
                        <button class="btn btn-primary" id="upload-photo-btn" style="position: absolute; bottom: 0; right: 0; border-radius: 50%; width: 40px; height: 40px; padding: 0; display: flex; align-items: center; justify-content: center;">
                            <i class="fas fa-camera"></i>
                        </button>
                        <input type="file" id="profile-photo-input" accept="image/*" style="display: none;">
                    </div>
                    <p style="color: var(--text-muted); font-size: 13px; margin-top: 10px;">Click the camera icon to upload a photo (JPG, PNG, GIF, max 5MB)</p>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Full Name</label>
                    <input type="text" class="form-control" id="profile-full-name" value="${this.userData.full_name || ''}" placeholder="Enter your full name">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Email Address</label>
                    <input type="email" class="form-control" id="profile-email" value="${this.userData.email || ''}" readonly>
                    <small style="color: var(--text-muted);">Email cannot be changed. Contact support for email updates.</small>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Phone Number</label>
                    <input type="tel" class="form-control" id="profile-phone" value="${this.userData.phone_number || ''}" placeholder="Enter your phone number">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Location</label>
                    <input type="text" class="form-control" id="profile-location" value="${this.userData.location || ''}" placeholder="Enter your location">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Bio</label>
                    <textarea class="form-control" id="profile-bio" rows="3" placeholder="Tell us about yourself">${this.userData.bio || ''}</textarea>
                </div>
                
                <div class="form-group">
                    <button class="btn btn-primary" id="save-profile-btn"><i class="fas fa-save"></i> Save Changes</button>
                    <button class="btn btn-secondary" id="cancel-profile-btn">Cancel</button>
                </div>
            </div>
            
            <div class="settings-section">
                <h3 class="section-title"><i class="fas fa-history"></i> Account Information</h3>
                
                <div class="info-grid">
                    <div class="info-item">
                        <span class="info-label">Account Created</span>
                        <span class="info-value">${new Date(this.userData.created_at || Date.now()).toLocaleDateString()}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Last Login</span>
                        <span class="info-value">${new Date(this.userData.last_login || this.userData.created_at || Date.now()).toLocaleString()}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Account Type</span>
                        <span class="info-value"><span class="badge-personal">${this.userData.account_type || 'Personal'}</span></span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Account Status</span>
                        <span class="info-value"><span class="status-active">● Active</span></span>
                    </div>
                </div>
            </div>
        `;
    }


    // ============ ACCOUNT SWITCHING METHODS ============

async showAccountSwitcher() {
    try {
        const token = localStorage.getItem('weather_ai_token');
        const response = await fetch(`${API_BASE_URL}/api/accounts/list`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load accounts');
        }
        
        const data = await response.json();
        this.showAccountSwitcherModal(data.accounts, data.current_account);
        
    } catch (error) {
        console.error('Error loading accounts:', error);
        showAlert('Failed to load accounts', 'error');
    }
}

showAccountSwitcherModal(accounts, currentEmail) {
    const modalHtml = `
        <div class="modal fade show" id="accountSwitcherModal" style="display: block; background: rgba(0,0,0,0.5); position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 10000;">
            <div class="modal-dialog modal-dialog-centered" style="max-width: 500px; margin: 50px auto;">
                <div class="modal-content" style="background: white; border-radius: 16px; overflow: hidden;">
                    <div class="modal-header" style="padding: 20px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                        <h5 class="modal-title" style="margin: 0;">
                            <i class="fas fa-exchange-alt" style="color: var(--primary-color); margin-right: 8px;"></i>
                            Switch Account
                        </h5>
                        <button type="button" class="btn-close" onclick="document.getElementById('accountSwitcherModal').remove()" style="background: none; border: none; font-size: 20px; cursor: pointer;">×</button>
                    </div>
                    
                    <div class="modal-body" style="padding: 20px;">
                        <div class="current-account-section" style="margin-bottom: 20px;">
                            <h6 style="color: var(--text-muted); margin-bottom: 10px;">Current Account</h6>
                            ${accounts.filter(acc => acc.email === currentEmail).map(acc => `
                                <div style="display: flex; align-items: center; gap: 15px; padding: 15px; background: rgba(26, 107, 179, 0.05); border-radius: 12px;">
                                    <div style="width: 48px; height: 48px; background: var(--gradient-primary); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; color: white; overflow: hidden;">
                                        ${acc.profile_picture ? 
                                            `<img src="${acc.profile_picture}" style="width: 100%; height: 100%; object-fit: cover;">` : 
                                            this.getInitials(acc.name)
                                        }
                                    </div>
                                    <div style="flex: 1;">
                                        <div style="font-weight: 600;">${acc.name}</div>
                                        <div style="font-size: 13px; color: var(--text-muted);">${acc.email}</div>
                                    </div>
                                    <span style="background: #10b981; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px;">Active</span>
                                </div>
                            `).join('')}
                        </div>
                        
                        <div class="other-accounts-section">
                            <h6 style="color: var(--text-muted); margin-bottom: 10px;">Other Accounts</h6>
                            <div style="max-height: 300px; overflow-y: auto;">
                                ${accounts.filter(acc => acc.email !== currentEmail).length > 0 ?
                                    accounts.filter(acc => acc.email !== currentEmail).map(acc => `
                                                <div class="account-item" data-account-id="${acc.id}" data-account-name="${encodeURIComponent(acc.name)}" style="display: flex; align-items: center; gap: 15px; padding: 15px; border: 1px solid var(--border-color); border-radius: 12px; margin-bottom: 10px; cursor: pointer; transition: all 0.3s ease;">
                                            <div style="width: 48px; height: 48px; background: var(--gradient-primary); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; color: white; overflow: hidden;">
                                                ${acc.profile_picture ? 
                                                    `<img src="${acc.profile_picture}" style="width: 100%; height: 100%; object-fit: cover;">` : 
                                                    this.getInitials(acc.name)
                                                }
                                            </div>
                                            <div style="flex: 1;">
                                                <div style="font-weight: 600;">${acc.name}</div>
                                                <div style="font-size: 13px; color: var(--text-muted);">${acc.email}</div>
                                            </div>
                                            <i class="fas fa-chevron-right" style="color: var(--text-muted);"></i>
                                        </div>
                                    `).join('') :
                                    '<p style="text-align: center; color: var(--text-muted); padding: 20px;">No other accounts connected. Add an account to switch.</p>'
                                }
                            </div>
                        </div>
                        
                        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--border-color);">
                            <button class="btn btn-primary" id="add-account-btn" style="width: 100%; margin-bottom: 10px;" onclick="window.userProfileManager.showAddAccountModal()">
                                <i class="fas fa-plus"></i> Add Another Account
                            </button>
                            <button class="btn btn-secondary" id="manage-accounts-btn" style="width: 100%;" onclick="window.userProfileManager.showManageAccounts()">
                                <i class="fas fa-cog"></i> Manage Connected Accounts
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove any existing modal
    const existingModal = document.getElementById('accountSwitcherModal');
    if (existingModal) existingModal.remove();
    
    const modalDiv = document.createElement('div');
    modalDiv.innerHTML = modalHtml;
    document.body.appendChild(modalDiv);
    this.attachAccountSwitcherListeners();
}

attachAccountSwitcherListeners() {
    document.querySelectorAll('#accountSwitcherModal .account-item').forEach(item => {
        item.addEventListener('click', () => {
            const accountId = item.dataset.accountId;
            const accountName = decodeURIComponent(item.dataset.accountName || '');
            if (accountId) {
                this.prepareSwitchAccount(accountId, accountName);
            }
        });
    });
}

prepareSwitchAccount(accountId, accountName) {
    this.showSwitchAccountPasswordModal(accountId, accountName);
}

showSwitchAccountPasswordModal(accountId, accountName) {
    const modalHtml = `
        <div class="modal fade show" id="switchAccountModal" style="display: block; background: rgba(0,0,0,0.5); position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 10000;">
            <div class="modal-dialog modal-dialog-centered" style="max-width: 400px; margin: 50px auto;">
                <div class="modal-content" style="background: white; border-radius: 16px; overflow: hidden;">
                    <div class="modal-header" style="padding: 20px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                        <h5 class="modal-title" style="margin: 0; font-weight: 700;">
                            <i class="fas fa-exchange-alt" style="color: var(--primary-color); margin-right: 8px;"></i>
                            Switch to ${accountName}
                        </h5>
                        <button type="button" class="btn-close" onclick="document.getElementById('switchAccountModal')?.remove()" style="background: none; border: none; font-size: 20px; cursor: pointer;">×</button>
                    </div>
                    <div class="modal-body" style="padding: 20px;">
                        <div class="alert alert-warning" style="background: rgba(247, 183, 51, 0.1); padding: 12px; border-radius: 10px; font-size: 13px; margin-bottom: 15px;">
                            <i class="fas fa-shield-alt" style="color: #f7b733;"></i> For security, please enter <strong>YOUR CURRENT PASSWORD</strong> to switch accounts.
                        </div>
                        <div class="form-group" style="margin-bottom: 15px;">
                            <label class="form-label">Your Current Password</label>
                            <input type="password" class="form-control" id="switch-account-password" placeholder="Enter your password">
                        </div>
                    </div>
                    <div class="modal-footer" style="padding: 20px; border-top: 1px solid var(--border-color); display: flex; justify-content: flex-end; gap: 10px;">
                        <button class="btn btn-secondary" type="button" onclick="document.getElementById('switchAccountModal')?.remove()">Cancel</button>
                        <button class="btn btn-primary" type="button" id="confirm-switch-account-btn">Switch Account</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    const existingModal = document.getElementById('switchAccountModal');
    if (existingModal) existingModal.remove();

    const modalDiv = document.createElement('div');
    modalDiv.innerHTML = modalHtml;
    document.body.appendChild(modalDiv);

    document.getElementById('confirm-switch-account-btn')?.addEventListener('click', async () => {
        const password = document.getElementById('switch-account-password')?.value.trim();
        if (!password) {
            showAlert('Please enter your password', 'error');
            return;
        }
        document.getElementById('switchAccountModal')?.remove();
        await this.switchToAccount(accountId, password);
    });
}

async switchToAccount(accountId, password) {
    try {
        const token = localStorage.getItem('weather_ai_token');
        console.log('Switching to account:', accountId);
        
        const response = await fetch(`${API_BASE_URL}/api/accounts/switch`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ account_id: accountId, password })
        });
        
        const data = await response.json();
        console.log('Switch response:', data);
        
        if (response.ok) {
            showAlert(`Switched to ${data.account.name}'s account`, 'success');
            
            // IMPORTANT: Clear ALL old data first
            localStorage.removeItem('weather_ai_token');
            localStorage.removeItem('weather_ai_user');
            localStorage.removeItem('switched_account');
            localStorage.removeItem('account_session_token');
            localStorage.removeItem('user_preferences');
            
            // Store the NEW session token
            localStorage.setItem('weather_ai_token', data.session_token);
            
            // Store the switched account info
            const switchedUser = {
                email: data.account.email,
                full_name: data.account.name,
                account_type: data.account.type,
                is_switched: true,
                account_id: data.account.id
            };
            localStorage.setItem('switched_account', JSON.stringify(switchedUser));
            localStorage.setItem('weather_ai_user', JSON.stringify(switchedUser));
            
            // Also set cookie for server-side access
            document.cookie = `weather_ai_token=${data.session_token}; path=/; max-age=${60*60*24}`;
            
            // Close modal
            document.getElementById('accountSwitcherModal')?.remove();
            
            // Force a hard reload to ensure everything is fresh
            window.location.href = '/dashboard';
            
        } else {
            console.error('Switch failed:', data);
            showAlert(data.detail || 'Failed to switch account. Please check your password.', 'error');
        }
    } catch (error) {
        console.error('Switch error:', error);
        showAlert('Network error: ' + error.message, 'error');
    }
}

showAddAccountModal() {
    const modalHtml = `
        <div class="modal fade show" id="addAccountModal" style="display: block; background: rgba(0,0,0,0.5); position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 10000;">
            <div class="modal-dialog modal-dialog-centered" style="max-width: 400px; margin: 50px auto;">
                <div class="modal-content" style="background: white; border-radius: 16px; overflow: hidden;">
                    <div class="modal-header" style="padding: 20px; border-bottom: 1px solid var(--border-color);">
                        <h5 class="modal-title">
                            <i class="fas fa-user-plus" style="color: var(--primary-color); margin-right: 8px;"></i>
                            Add Account
                        </h5>
                        <button type="button" class="btn-close" onclick="document.getElementById('addAccountModal').remove()">×</button>
                    </div>
                    
                    <div class="modal-body" style="padding: 20px;">
                        <p style="color: var(--text-muted); margin-bottom: 20px;">Add another Weather AI account to switch between them easily.</p>
                        
                        <div class="form-group" style="margin-bottom: 15px;">
                            <label class="form-label">Account Email</label>
                            <input type="email" class="form-control" id="add-account-email" placeholder="Enter account email">
                        </div>
                        
                        <div class="form-group" style="margin-bottom: 15px;">
                            <label class="form-label">Account Password</label>
                            <input type="password" class="form-control" id="add-account-password" placeholder="Enter account password">
                        </div>
                        
                        <div class="form-group" style="margin-bottom: 15px;">
                            <label class="form-label">Display Name (Optional)</label>
                            <input type="text" class="form-control" id="add-account-name" placeholder="e.g., Work Account">
                        </div>
                        
                        <div class="alert alert-info" style="background: rgba(26, 107, 179, 0.1); padding: 10px; border-radius: 8px; font-size: 13px;">
                            <i class="fas fa-info-circle"></i> You'll need the password for the account you're adding.
                        </div>
                    </div>
                    
                    <div class="modal-footer" style="padding: 20px; border-top: 1px solid var(--border-color);">
                        <button class="btn btn-secondary" onclick="document.getElementById('addAccountModal').remove()">Cancel</button>
                        <button class="btn btn-primary" id="confirm-add-account-btn">Add Account</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const modalDiv = document.createElement('div');
    modalDiv.innerHTML = modalHtml;
    document.body.appendChild(modalDiv);
    
    document.getElementById('confirm-add-account-btn').addEventListener('click', async () => {
        await this.addConnectedAccount();
    });
}

async addConnectedAccount() {
    const email = document.getElementById('add-account-email')?.value;
    const password = document.getElementById('add-account-password')?.value;
    const accountName = document.getElementById('add-account-name')?.value;
    
    if (!email || !password) {
        showAlert('Please enter email and password', 'error');
        return;
    }
    
    try {
        const token = localStorage.getItem('weather_ai_token');
        const response = await fetch(`${API_BASE_URL}/api/accounts/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ email, password, account_name: accountName })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert(data.message, 'success');
            document.getElementById('addAccountModal')?.remove();
            // Refresh account switcher
            this.showAccountSwitcher();
        } else {
            throw new Error(data.detail || 'Failed to add account');
        }
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

showManageAccounts() {
    this.showAccountSwitcher();
}

    async getPreferencesPageContent() {
        await this.loadUserProfile();
        
        return `
            <div class="settings-section">
                <h3 class="section-title"><i class="fas fa-globe"></i> Language & Region</h3>
                
                <div class="form-group">
                    <label class="form-label">Language</label>
                    <select class="form-select" id="pref-language">
                        <option value="en" ${this.userPreferences.language === 'en' ? 'selected' : ''}>English</option>
                        <option value="es" ${this.userPreferences.language === 'es' ? 'selected' : ''}>Spanish</option>
                        <option value="fr" ${this.userPreferences.language === 'fr' ? 'selected' : ''}>French</option>
                        <option value="de" ${this.userPreferences.language === 'de' ? 'selected' : ''}>German</option>
                        <option value="zh" ${this.userPreferences.language === 'zh' ? 'selected' : ''}>Chinese</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Timezone</label>
                    <select class="form-select" id="pref-timezone">
                        <option value="UTC" ${this.userPreferences.timezone === 'UTC' ? 'selected' : ''}>UTC (Coordinated Universal Time)</option>
                        <option value="EST" ${this.userPreferences.timezone === 'EST' ? 'selected' : ''}>EST (Eastern Time)</option>
                        <option value="PST" ${this.userPreferences.timezone === 'PST' ? 'selected' : ''}>PST (Pacific Time)</option>
                        <option value="GMT" ${this.userPreferences.timezone === 'GMT' ? 'selected' : ''}>GMT (Greenwich Mean Time)</option>
                        <option value="CET" ${this.userPreferences.timezone === 'CET' ? 'selected' : ''}>CET (Central European Time)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Date Format</label>
                    <select class="form-select" id="pref-date-format">
                        <option value="MM/DD/YYYY" ${this.userPreferences.date_format === 'MM/DD/YYYY' ? 'selected' : ''}>MM/DD/YYYY</option>
                        <option value="DD/MM/YYYY" ${this.userPreferences.date_format === 'DD/MM/YYYY' ? 'selected' : ''}>DD/MM/YYYY</option>
                        <option value="YYYY-MM-DD" ${this.userPreferences.date_format === 'YYYY-MM-DD' ? 'selected' : ''}>YYYY-MM-DD</option>
                    </select>
                </div>
            </div>
            
            <div class="settings-section">
                <h3 class="section-title"><i class="fas fa-palette"></i> Appearance</h3>
                
                <div class="form-group">
                    <label class="form-label">Theme</label>
                    <div style="display: flex; gap: 15px; margin-top: 10px; flex-wrap: wrap;">
                        <div class="theme-option ${this.userPreferences.theme === 'light' ? 'active' : ''}" data-theme="light">
                            <div class="theme-preview light"></div>
                            <span>Light</span>
                        </div>
                        <div class="theme-option ${this.userPreferences.theme === 'dark' ? 'active' : ''}" data-theme="dark">
                            <div class="theme-preview dark"></div>
                            <span>Dark</span>
                        </div>
                        <div class="theme-option ${this.userPreferences.theme === 'auto' ? 'active' : ''}" data-theme="auto">
                            <div class="theme-preview auto"></div>
                            <span>Auto</span>
                        </div>
                    </div>
                </div>
                
                <div class="form-group">
                    <button class="btn btn-primary" id="save-prefs-btn"><i class="fas fa-save"></i> Save Preferences</button>
                </div>
            </div>
        `;
    }
    
    async getUnitsPageContent() {
        await this.loadUserProfile();
        
        return `
            <div class="settings-section">
                <h3 class="section-title"><i class="fas fa-thermometer-half"></i> Temperature Units</h3>
                
                <div style="display: flex; gap: 15px; margin-top: 10px; flex-wrap: wrap;">
                    <div class="unit-option ${this.userPreferences.temperature_unit === 'celsius' ? 'active' : ''}" data-unit="celsius" data-type="temperature">
                        <div class="unit-preview">°C</div>
                        <span>Celsius</span>
                    </div>
                    <div class="unit-option ${this.userPreferences.temperature_unit === 'fahrenheit' ? 'active' : ''}" data-unit="fahrenheit" data-type="temperature">
                        <div class="unit-preview">°F</div>
                        <span>Fahrenheit</span>
                    </div>
                </div>
            </div>
            
            <div class="settings-section">
                <h3 class="section-title"><i class="fas fa-wind"></i> Wind Speed Units</h3>
                
                <div style="display: flex; gap: 15px; margin-top: 10px; flex-wrap: wrap;">
                    <div class="unit-option ${this.userPreferences.wind_speed_unit === 'kmh' ? 'active' : ''}" data-unit="kmh" data-type="wind">
                        <div class="unit-preview">km/h</div>
                        <span>Kilometers per hour</span>
                    </div>
                    <div class="unit-option ${this.userPreferences.wind_speed_unit === 'mph' ? 'active' : ''}" data-unit="mph" data-type="wind">
                        <div class="unit-preview">mph</div>
                        <span>Miles per hour</span>
                    </div>
                    <div class="unit-option ${this.userPreferences.wind_speed_unit === 'ms' ? 'active' : ''}" data-unit="ms" data-type="wind">
                        <div class="unit-preview">m/s</div>
                        <span>Meters per second</span>
                    </div>
                </div>
            </div>
            
            <div class="settings-section">
                <h3 class="section-title"><i class="fas fa-compress-alt"></i> Pressure Units</h3>
                
                <div style="display: flex; gap: 15px; margin-top: 10px; flex-wrap: wrap;">
                    <div class="unit-option ${this.userPreferences.pressure_unit === 'hpa' ? 'active' : ''}" data-unit="hpa" data-type="pressure">
                        <div class="unit-preview">hPa</div>
                        <span>Hectopascals</span>
                    </div>
                    <div class="unit-option ${this.userPreferences.pressure_unit === 'inhg' ? 'active' : ''}" data-unit="inhg" data-type="pressure">
                        <div class="unit-preview">inHg</div>
                        <span>Inches of mercury</span>
                    </div>
                    <div class="unit-option ${this.userPreferences.pressure_unit === 'mmhg' ? 'active' : ''}" data-unit="mmhg" data-type="pressure">
                        <div class="unit-preview">mmHg</div>
                        <span>Millimeters of mercury</span>
                    </div>
                </div>
            </div>
            
            <div class="settings-section">
                <h3 class="section-title"><i class="fas fa-ruler"></i> Distance Units</h3>
                
                <div style="display: flex; gap: 15px; margin-top: 10px; flex-wrap: wrap;">
                    <div class="unit-option ${this.userPreferences.distance_unit === 'km' ? 'active' : ''}" data-unit="km" data-type="distance">
                        <div class="unit-preview">km</div>
                        <span>Kilometers</span>
                    </div>
                    <div class="unit-option ${this.userPreferences.distance_unit === 'miles' ? 'active' : ''}" data-unit="miles" data-type="distance">
                        <div class="unit-preview">miles</div>
                        <span>Miles</span>
                    </div>
                </div>
            </div>
            
            <div class="settings-section">
                <button class="btn btn-primary" id="save-units-btn"><i class="fas fa-save"></i> Save Unit Preferences</button>
                <button class="btn btn-secondary" id="reset-units-btn">Reset to Defaults</button>
            </div>
        `;
    }
    
    async getNotificationsPageContent() {
        return `
            <div class="settings-section">
                <h3 class="section-title"><i class="fas fa-bell"></i> Notification Settings</h3>
                
                <div class="settings-item">
                    <div class="setting-info">
                        <h4>Email Notifications</h4>
                        <p>Receive weather alerts and updates via email</p>
                    </div>
                    <label class="toggle-switch">
                        <input type="checkbox" id="email-notifications" ${this.userPreferences.notifications_email !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                
                <div class="settings-item">
                    <div class="setting-info">
                        <h4>Anomaly Alerts</h4>
                        <p>Get notified when anomalies are detected</p>
                    </div>
                    <label class="toggle-switch">
                        <input type="checkbox" id="anomaly-alerts" ${this.userPreferences.anomaly_alerts !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                
                <div class="settings-item">
                    <div class="setting-info">
                        <h4>Weekly Reports</h4>
                        <p>Receive weekly weather summary reports</p>
                    </div>
                    <label class="toggle-switch">
                        <input type="checkbox" id="weekly-reports" ${this.userPreferences.weekly_reports !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                
                <div class="settings-item">
                    <div class="setting-info">
                        <h4>System Updates</h4>
                        <p>Notifications about platform updates and maintenance</p>
                    </div>
                    <label class="toggle-switch">
                        <input type="checkbox" id="system-updates" ${this.userPreferences.system_updates !== false ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                
                <div class="form-group">
                    <button class="btn btn-primary" id="save-notifications-btn"><i class="fas fa-save"></i> Save Notification Settings</button>
                </div>
            </div>
        `;
    }
    
    async getSecurityPageContent() {
    return `
        <div class="settings-section">
            <h3 class="section-title"><i class="fas fa-shield-alt"></i> Security Settings</h3>
            
            <div class="form-group">
                <label class="form-label">Current Password</label>
                <input type="password" class="form-control" id="current-password" placeholder="Enter current password">
            </div>
            
            <div class="form-group">
                <label class="form-label">New Password</label>
                <input type="password" class="form-control" id="new-password" placeholder="Enter new password">
                <small style="color: var(--text-muted);">Minimum 8 characters with letters and numbers</small>
            </div>
            
            <div class="form-group">
                <label class="form-label">Confirm New Password</label>
                <input type="password" class="form-control" id="confirm-password" placeholder="Confirm new password">
            </div>
            
            <div class="form-group">
                <button class="btn btn-primary" id="change-password-btn"><i class="fas fa-key"></i> Change Password</button>
            </div>
        </div>
        
        <div class="settings-section">
            <h3 class="section-title"><i class="fas fa-user-shield"></i> Email Two-Factor Authentication</h3>
            
            <div class="settings-item">
                <div class="setting-info">
                    <h4>Enable Email 2FA</h4>
                    <p>Get a verification code via email when you log in</p>
                </div>
                <label class="toggle-switch">
                    <input type="checkbox" id="enable-email-2fa" ${this.userPreferences.email_2fa_enabled ? 'checked' : ''}>
                    <span class="toggle-slider"></span>
                </label>
            </div>
            
            ${this.userPreferences.email_2fa_enabled ? 
                `<div class="alert alert-success mt-3"><i class="fas fa-check-circle"></i> Email 2FA is currently enabled. You'll receive verification codes via email.</div>` : 
                `<div class="alert alert-info mt-3"><i class="fas fa-info-circle"></i> Enable email 2FA for enhanced security. A verification code will be sent to your email each time you log in.</div>`
            }
        </div>
    `;
}
    
    async getApiKeysPageContent() {
        return `
            <div class="settings-section">
                <h3 class="section-title"><i class="fas fa-key"></i> API Keys Management</h3>
                
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i> Your API keys allow you to access Weather AI data programmatically.
                </div>
                
                <div class="form-group">
                    <label class="form-label">Generate New API Key</label>
                    <select class="form-select" id="api-key-type">
                        <option value="read">Read-only Key</option>
                        <option value="write">Read/Write Key</option>
                        <option value="admin">Admin Key</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Key Name</label>
                    <input type="text" class="form-control" id="api-key-name" placeholder="e.g., Production Key, Development Key">
                </div>
                
                <div class="form-group">
                    <button class="btn btn-primary" id="generate-api-key-btn"><i class="fas fa-key"></i> Generate API Key</button>
                </div>
            </div>
            
            <div class="settings-section">
                <h3 class="section-title"><i class="fas fa-list"></i> Active API Keys</h3>
                
                <div class="recent-activity">
                    <table class="activity-table">
                        <thead>
                            <tr><th>Name</th><th>Key</th><th>Type</th><th>Created</th><th>Last Used</th><th>Actions</th></tr>
                        </thead>
                        <tbody id="api-keys-table">
                            <tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 40px;">No API keys generated yet.</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    async getUsagePageContent() {
        return `
            <div class="settings-section">
                <h3 class="section-title"><i class="fas fa-chart-bar"></i> Usage Statistics</h3>
                
                <div class="stats-grid">
                    <div class="stat-card fade-in-up">
                        <div class="stat-header"><div class="stat-icon"><i class="fas fa-cloud-sun"></i></div></div>
                        <div class="stat-value">${this.usageStats.weather_checks || 0}</div>
                        <div class="stat-label">Weather Checks</div>
                        <div class="stat-subtext">Total requests made</div>
                    </div>

                    <div class="stat-card warning fade-in-up">
                        <div class="stat-header"><div class="stat-icon"><i class="fas fa-exclamation-triangle"></i></div></div>
                        <div class="stat-value">${this.usageStats.anomaly_detections || 0}</div>
                        <div class="stat-label">Anomaly Detections</div>
                        <div class="stat-subtext">AI analyses performed</div>
                    </div>

                    <div class="stat-card success fade-in-up">
                        <div class="stat-header"><div class="stat-icon"><i class="fas fa-database"></i></div></div>
                        <div class="stat-value">${this.usageStats.api_calls || 0}</div>
                        <div class="stat-label">API Calls</div>
                        <div class="stat-subtext">Total API requests</div>
                    </div>

                    <div class="stat-card info fade-in-up">
                        <div class="stat-header"><div class="stat-icon"><i class="fas fa-calendar-alt"></i></div></div>
                        <div class="stat-value">${this.usageStats.active_days || 0}</div>
                        <div class="stat-label">Active Days</div>
                        <div class="stat-subtext">Days with activity</div>
                    </div>
                </div>
            </div>
            
            <div class="chart-container">
                <h3 class="section-title"><i class="fas fa-chart-line"></i> Usage Trends</h3>
                <canvas id="usageChart" width="400" height="200"></canvas>
            </div>
        `;
    }
    
    async getBillingPageContent() {
    try {
        const token = localStorage.getItem('weather_ai_token');
        const headers = { 'Authorization': `Bearer ${token}` };
        
        // Fetch current subscription and plans
        const [subscriptionRes, plansRes] = await Promise.all([
            fetch(`${API_BASE_URL}/api/billing/current`, { headers }),
            fetch(`${API_BASE_URL}/api/billing/plans`, { headers })
        ]);
        
        const subscriptionData = await subscriptionRes.json();
        const plansData = await plansRes.json();
        
        const currentSub = subscriptionData.subscription || {
            plan_id: 'free',
            plan_name: 'Free',
            status: 'active',
            features: ['Basic weather data', '50 API calls per day', '7-day weather history', 'Email support']
        };
        
        const plans = plansData.plans || [];
        
        return `
            <div class="settings-section">
                <h3 class="section-title"><i class="fas fa-crown"></i> Current Subscription</h3>
                
                <div class="current-plan-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 16px; margin-bottom: 30px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <div>
                            <h2 style="margin: 0; font-size: 32px; color: white;">${currentSub.plan_name} Plan</h2>
                            <p style="margin: 10px 0 0; opacity: 0.9;">
                                <i class="fas fa-circle" style="font-size: 10px; color: ${currentSub.status === 'active' ? '#10b981' : '#ef4444'}; margin-right: 8px;"></i>
                                ${currentSub.status === 'active' ? 'Active' : 'Inactive'}
                            </p>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 36px; font-weight: 700;">$${this.getPlanPrice(currentSub.plan_id, plans)}</div>
                            <div style="opacity: 0.9;">per month</div>
                        </div>
                    </div>
                    
                    <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2);">
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            ${currentSub.features.map(feature => `
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <i class="fas fa-check-circle" style="color: #10b981;"></i>
                                    <span>${feature}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
                
                <h3 class="section-title"><i class="fas fa-tags"></i> Available Plans</h3>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px;">
                    ${plans.map(plan => `
                        <div class="plan-card" style="border: 2px solid ${plan.plan_id === currentSub.plan_id ? '#667eea' : '#e2e8f0'}; border-radius: 12px; padding: 20px; position: relative; transition: all 0.3s ease;">
                            ${plan.plan_id === 'pro' ? '<div style="position: absolute; top: -12px; right: 20px; background: linear-gradient(135deg, #fbbf24, #f59e0b); color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">POPULAR</div>' : ''}
                            
                            <h4 style="font-size: 20px; margin-bottom: 10px;">${plan.plan_name}</h4>
                            <div style="font-size: 28px; font-weight: 700; margin-bottom: 15px;">
                                $${plan.price}
                                <span style="font-size: 14px; font-weight: normal; color: var(--text-muted);">/${plan.interval}</span>
                            </div>
                            
                            <ul style="list-style: none; padding: 0; margin: 20px 0; min-height: 200px;">
                                ${plan.features.map(feature => `
                                    <li style="margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
                                        <i class="fas fa-check" style="color: #10b981; font-size: 14px;"></i>
                                        <span style="font-size: 14px;">${feature}</span>
                                    </li>
                                `).join('')}
                            </ul>
                            
                            <button class="btn ${plan.plan_id === currentSub.plan_id ? 'btn-secondary' : 'btn-primary'}" 
                                    onclick="window.userProfileManager.changePlan('${plan.plan_id}')"
                                    style="width: 100%;"
                                    ${plan.plan_id === currentSub.plan_id ? 'disabled' : ''}>
                                ${plan.plan_id === currentSub.plan_id ? 'Current Plan' : 'Switch to ' + plan.plan_name}
                            </button>
                        </div>
                    `).join('')}
                </div>
                
                <h3 class="section-title"><i class="fas fa-credit-card"></i> Payment Methods</h3>
                
                <div id="payment-methods-container" style="margin-bottom: 30px;">
                    ${subscriptionData.payment_methods && subscriptionData.payment_methods.length > 0 ? 
                        subscriptionData.payment_methods.map(pm => `
                            <div style="display: flex; align-items: center; justify-content: space-between; padding: 15px; border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 10px;">
                                <div style="display: flex; align-items: center; gap: 15px;">
                                    <i class="fas fa-credit-card" style="font-size: 24px; color: var(--primary-color);"></i>
                                    <div>
                                        <strong>${pm.card_brand.toUpperCase()} •••• ${pm.card_last4}</strong>
                                        <div style="font-size: 13px; color: var(--text-muted);">
                                            Expires ${pm.expiry_month}/${pm.expiry_year}
                                            ${pm.is_default ? '<span style="margin-left: 10px; background: #10b981; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">DEFAULT</span>' : ''}
                                        </div>
                                    </div>
                                </div>
                                <button class="btn btn-sm btn-danger" onclick="window.userProfileManager.removePaymentMethod(${pm.id})">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        `).join('') : 
                        '<p style="color: var(--text-muted); text-align: center; padding: 20px;">No payment methods added yet.</p>'
                    }
                    
                    <button class="btn btn-secondary" id="add-payment-method-btn" style="margin-top: 10px;">
                        <i class="fas fa-plus"></i> Add Payment Method
                    </button>
                </div>
                
                <h3 class="section-title"><i class="fas fa-file-invoice"></i> Invoice History</h3>
                
                <div class="recent-activity">
                    <table class="activity-table">
                        <thead>
                            <tr>
                                <th>Invoice #</th>
                                <th>Date</th>
                                <th>Plan</th>
                                <th>Amount</th>
                                <th>Status</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody id="invoices-table-body">
                            ${subscriptionData.invoices && subscriptionData.invoices.length > 0 ?
                                subscriptionData.invoices.map(inv => `
                                    <tr>
                                        <td>${inv.invoice_number}</td>
                                        <td>${new Date(inv.paid_at).toLocaleDateString()}</td>
                                        <td>${inv.plan_id.charAt(0).toUpperCase() + inv.plan_id.slice(1)}</td>
                                        <td>$${inv.amount}</td>
                                        <td><span class="badge badge-success">${inv.status}</span></td>
                                        <td>
                                            <button class="btn btn-sm btn-primary" onclick="window.userProfileManager.downloadInvoice(${inv.id})">
                                                <i class="fas fa-download"></i>
                                            </button>
                                        </td>
                                    </tr>
                                `).join('') :
                                '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 40px;">No invoices yet.</td></tr>'
                            }
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading billing page:', error);
        return '<div class="alert alert-danger">Failed to load billing information. Please try again.</div>';
    }
}

getPlanPrice(planId, plans) {
    const plan = plans.find(p => p.plan_id === planId);
    return plan ? plan.price : 0;
}

async changePlan(planId) {
    if (!confirm(`Are you sure you want to switch to this plan?`)) {
        return;
    }
    
    try {
        const token = localStorage.getItem('weather_ai_token');
        const response = await fetch(`${API_BASE_URL}/api/billing/subscribe`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ plan_id: planId })
        });
        
        if (response.ok) {
            showAlert('Plan changed successfully!', 'success');
            // Reload the billing page
            await this.loadSettingsPage('billing');
        } else {
            const error = await response.json();
            let message = 'Failed to change plan';
            if (error.detail) {
                if (typeof error.detail === 'string') {
                    message = error.detail;
                } else if (Array.isArray(error.detail)) {
                    message = error.detail.map(item => item?.msg || JSON.stringify(item)).join('; ');
                }
            }
            throw new Error(message);
        }
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

async addPaymentMethod() {
    this.showAddPaymentMethodModal();
}

showAddPaymentMethodModal() {
    const modalHtml = `
        <div class="modal fade show" id="paymentMethodModal" style="display: block; background: rgba(0,0,0,0.5); position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 10000;">
            <div class="modal-dialog modal-dialog-centered" style="max-width: 480px; margin: 50px auto;">
                <div class="modal-content" style="background: white; border-radius: 16px; overflow: hidden;">
                    <div class="modal-header" style="padding: 20px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                        <h5 class="modal-title" style="margin: 0; font-weight: 700;">
                            <i class="fas fa-credit-card" style="color: var(--primary-color); margin-right: 8px;"></i>
                            Add Payment Method
                        </h5>
                        <button type="button" class="btn-close" onclick="document.getElementById('paymentMethodModal')?.remove()" style="background: none; border: none; font-size: 20px; cursor: pointer;">×</button>
                    </div>
                    <div class="modal-body" style="padding: 20px;">
                        <div class="form-group" style="margin-bottom: 15px;">
                            <label class="form-label">Card Number</label>
                            <input type="text" class="form-control" id="payment-card-number" placeholder="1234 5678 9012 3456">
                        </div>
                        <div class="form-group" style="margin-bottom: 15px;">
                            <label class="form-label">Card Holder</label>
                            <input type="text" class="form-control" id="payment-card-holder" placeholder="Cardholder Name">
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 15px; margin-bottom: 15px;">
                            <div class="form-group">
                                <label class="form-label">Expiry (MM/YY)</label>
                                <input type="text" class="form-control" id="payment-card-expiry" placeholder="MM/YY">
                            </div>
                            <div class="form-group">
                                <label class="form-label">CVV</label>
                                <input type="text" class="form-control" id="payment-card-cvv" placeholder="123">
                            </div>
                        </div>
                        <div class="form-check" style="margin-bottom: 10px;">
                            <input class="form-check-input" type="checkbox" value="" id="payment-card-default" checked>
                            <label class="form-check-label" for="payment-card-default">Set as default payment method</label>
                        </div>
                        <div class="alert alert-info" style="background: rgba(26, 107, 179, 0.1); padding: 12px; border-radius: 10px; font-size: 13px;">
                            <i class="fas fa-info-circle"></i> Payment details are submitted securely for billing.
                        </div>
                    </div>
                    <div class="modal-footer" style="padding: 20px; border-top: 1px solid var(--border-color); display: flex; justify-content: flex-end; gap: 10px;">
                        <button class="btn btn-secondary" type="button" onclick="document.getElementById('paymentMethodModal')?.remove()">Cancel</button>
                        <button class="btn btn-primary" type="button" id="confirm-add-payment-btn">Add Payment Method</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    const existingModal = document.getElementById('paymentMethodModal');
    if (existingModal) existingModal.remove();

    const modalDiv = document.createElement('div');
    modalDiv.innerHTML = modalHtml;
    document.body.appendChild(modalDiv);

    document.getElementById('confirm-add-payment-btn')?.addEventListener('click', async () => {
        await this.submitNewPaymentMethod();
    });
}

async submitNewPaymentMethod() {
    const cardNumber = document.getElementById('payment-card-number')?.value.trim();
    const cardHolder = document.getElementById('payment-card-holder')?.value.trim();
    const expiry = document.getElementById('payment-card-expiry')?.value.trim();
    const cvv = document.getElementById('payment-card-cvv')?.value.trim();
    const isDefault = document.getElementById('payment-card-default')?.checked;

    if (!cardNumber || !cardHolder || !expiry || !cvv) {
        showAlert('Please complete the payment method details.', 'error');
        return;
    }

    const [month, year] = expiry.split('/').map(item => item && item.trim());
    if (!month || !year || isNaN(month) || isNaN(year)) {
        showAlert('Please enter a valid expiry date in MM/YY format.', 'error');
        return;
    }

    try {
        const token = localStorage.getItem('weather_ai_token');
        if (!token) {
            showAlert('Please login again', 'error');
            return;
        }

        const response = await fetch(`${API_BASE_URL}/api/billing/payment-methods`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                card_number: cardNumber,
                card_holder: cardHolder,
                expiry_month: parseInt(month, 10),
                expiry_year: year.length === 2 ? parseInt('20' + year, 10) : parseInt(year, 10),
                cvv,
                is_default: Boolean(isDefault)
            })
        });

        const result = await response.json();
        if (response.ok) {
            showAlert(result.message || 'Payment method added successfully', 'success');
            document.getElementById('paymentMethodModal')?.remove();
            await this.loadSettingsPage('billing');
        } else {
            throw new Error(result.detail || 'Failed to add payment method');
        }
    } catch (error) {
        console.error('Error adding payment method:', error);
        showAlert(error.message || 'Failed to add payment method', 'error');
    }
}

async removePaymentMethod(methodId) {
    if (!confirm('Are you sure you want to remove this payment method?')) {
        return;
    }
    
    try {
        const token = localStorage.getItem('weather_ai_token');
        const response = await fetch(`${API_BASE_URL}/api/billing/payment-methods/${methodId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            showAlert('Payment method removed successfully', 'success');
            await this.loadSettingsPage('billing');
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to remove payment method');
        }
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

async downloadInvoice(invoiceId) {
    try {
        const token = localStorage.getItem('weather_ai_token');
        const response = await fetch(`${API_BASE_URL}/api/billing/invoices/${invoiceId}/pdf`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `invoice-${invoiceId}.pdf`;
            a.click();
        } else {
            showAlert('Invoice download not available yet', 'info');
        }
    } catch (error) {
        showAlert('Failed to download invoice', 'error');
    }
}
    
    setupSettingsPageListeners(section) {
    // Back button is already handled in loadSettingsPage, so skip here
    
        switch(section) {
            case 'profile':
                this.setupProfilePageListeners();
                break;
            case 'preferences':
                this.setupPreferencesPageListeners();
                break;
            case 'units':
                this.setupUnitsPageListeners();
                break;
            case 'notifications':
                this.setupNotificationsPageListeners();
                break;
            case 'security':
                this.setupSecurityPageListeners();
                break;
            case 'api-keys':
                this.setupApiKeysPageListeners();
                break;
            case 'usage':
                this.setupUsagePageListeners();
                break;
            case 'billing':
                this.setupBillingPageListeners();
                break;
        }
    }
    
    setupProfilePageListeners() {
        const uploadBtn = document.getElementById('upload-photo-btn');
        const photoInput = document.getElementById('profile-photo-input');
        
        if (uploadBtn && photoInput) {
            uploadBtn.addEventListener('click', () => photoInput.click());
            
            photoInput.addEventListener('change', async (e) => {
                const file = e.target.files[0];
                if (file) {
                    // Validate file size (max 5MB)
                    if (file.size > 5 * 1024 * 1024) {
                        showAlert('File size must be less than 5MB', 'error');
                        return;
                    }
                    
                    // Validate file type
                    if (!file.type.match('image.*')) {
                        showAlert('Please upload an image file', 'error');
                        return;
                    }
                    
                    // Show preview
                    const imageUrl = URL.createObjectURL(file);
                    const profilePic = document.getElementById('current-profile-pic');
                    if (profilePic) {
                        profilePic.innerHTML = `<img src="${imageUrl}" alt="Profile" style="width: 100%; height: 100%; object-fit: cover;">`;
                    }
                    
                    // Upload the file
                    await this.uploadProfilePicture(file);
                }
            });
        }
        
        const saveBtn = document.getElementById('save-profile-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', async () => await this.saveProfileSettings());
        }
        
        const cancelBtn = document.getElementById('cancel-profile-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.closeSettings());
        }
    }
    
    async saveProfileSettings() {
        try {
            const token = localStorage.getItem('weather_ai_token');
            if (!token) {
                showAlert('Please login again', 'error');
                return;
            }
            
            const profileData = {
                full_name: document.getElementById('profile-full-name')?.value || '',
                phone_number: document.getElementById('profile-phone')?.value || '',
                location: document.getElementById('profile-location')?.value || '',
                bio: document.getElementById('profile-bio')?.value || ''
            };
            
            const response = await fetch(`${API_BASE_URL}/api/user/profile`, {
                method: 'PUT',
                headers: { 
                    'Content-Type': 'application/json', 
                    'Authorization': `Bearer ${token}` 
                },
                body: JSON.stringify(profileData)
            });
            
            if (response.ok) {
                showAlert('Profile updated successfully!', 'success');
                await this.loadUserProfile();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to update profile');
            }
        } catch (error) {
            console.error('Error saving profile:', error);
            showAlert(error.message || 'Failed to update profile', 'error');
        }
    }
    
    setupPreferencesPageListeners() {
        document.querySelectorAll('.theme-option').forEach(option => {
            option.addEventListener('click', () => {
                document.querySelectorAll('.theme-option').forEach(opt => opt.classList.remove('active'));
                option.classList.add('active');
            });
        });
        
        const saveBtn = document.getElementById('save-prefs-btn');
        if (saveBtn) saveBtn.addEventListener('click', async () => await this.savePreferences());
    }
    
    async savePreferences() {
        try {
            const token = localStorage.getItem('weather_ai_token');
            if (!token) {
                showAlert('Please login again', 'error');
                return;
            }
            
            const selectedTheme = document.querySelector('.theme-option.active')?.dataset.theme || 'light';
            
            const preferences = {
                language: document.getElementById('pref-language')?.value || 'en',
                timezone: document.getElementById('pref-timezone')?.value || 'UTC',
                date_format: document.getElementById('pref-date-format')?.value || 'MM/DD/YYYY',
                theme: selectedTheme,
                temperature_unit: this.userPreferences.temperature_unit || 'celsius',
                wind_speed_unit: this.userPreferences.wind_speed_unit || 'kmh',
                pressure_unit: this.userPreferences.pressure_unit || 'hpa',
                distance_unit: this.userPreferences.distance_unit || 'km'
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
                await this.loadUserProfile();
                
                // Apply theme
                if (preferences.theme === 'dark') {
                    document.body.classList.add('dark-mode');
                } else if (preferences.theme === 'light') {
                    document.body.classList.remove('dark-mode');
                } else {
                    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
                        document.body.classList.add('dark-mode');
                    } else {
                        document.body.classList.remove('dark-mode');
                    }
                }
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save preferences');
            }
        } catch (error) {
            console.error('Error saving preferences:', error);
            showAlert(error.message || 'Failed to save preferences', 'error');
        }
    }
    
    setupUnitsPageListeners() {
        document.querySelectorAll('.unit-option').forEach(option => {
            option.addEventListener('click', () => {
                const type = option.dataset.type;
                document.querySelectorAll(`.unit-option[data-type="${type}"]`).forEach(opt => opt.classList.remove('active'));
                option.classList.add('active');
            });
        });
        
        const saveBtn = document.getElementById('save-units-btn');
        if (saveBtn) saveBtn.addEventListener('click', async () => await this.saveUnitPreferences());
        
        const resetBtn = document.getElementById('reset-units-btn');
        if (resetBtn) resetBtn.addEventListener('click', () => this.resetUnitPreferences());
    }
    
    async saveUnitPreferences() {
        try {
            const token = localStorage.getItem('weather_ai_token');
            if (!token) {
                showAlert('Please login again', 'error');
                return;
            }
            
            const temperatureUnit = document.querySelector('.unit-option.active[data-type="temperature"]')?.dataset.unit || 'celsius';
            const windUnit = document.querySelector('.unit-option.active[data-type="wind"]')?.dataset.unit || 'kmh';
            const pressureUnit = document.querySelector('.unit-option.active[data-type="pressure"]')?.dataset.unit || 'hpa';
            const distanceUnit = document.querySelector('.unit-option.active[data-type="distance"]')?.dataset.unit || 'km';
            
            const preferences = {
                ...this.userPreferences,
                temperature_unit: temperatureUnit,
                wind_speed_unit: windUnit,
                pressure_unit: pressureUnit,
                distance_unit: distanceUnit
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
                showAlert('Unit preferences saved successfully!', 'success');
                await this.loadUserProfile();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save unit preferences');
            }
        } catch (error) {
            console.error('Error saving unit preferences:', error);
            showAlert(error.message || 'Failed to save unit preferences', 'error');
        }
    }
    
    resetUnitPreferences() {
        document.querySelectorAll('.unit-option').forEach(option => option.classList.remove('active'));
        document.querySelector('.unit-option[data-unit="celsius"]')?.classList.add('active');
        document.querySelector('.unit-option[data-unit="kmh"]')?.classList.add('active');
        document.querySelector('.unit-option[data-unit="hpa"]')?.classList.add('active');
        document.querySelector('.unit-option[data-unit="km"]')?.classList.add('active');
    }
    
    setupNotificationsPageListeners() {
        const saveBtn = document.getElementById('save-notifications-btn');
        if (saveBtn) saveBtn.addEventListener('click', async () => await this.saveNotificationSettings());
    }
    
    async saveNotificationSettings() {
        try {
            const token = localStorage.getItem('weather_ai_token');
            if (!token) {
                showAlert('Please login again', 'error');
                return;
            }
            
            const preferences = {
                ...this.userPreferences,
                email_notifications: document.getElementById('email-notifications')?.checked || false,
                anomaly_alerts: document.getElementById('anomaly-alerts')?.checked || false,
                weekly_reports: document.getElementById('weekly-reports')?.checked || false,
                system_updates: document.getElementById('system-updates')?.checked || false
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
                showAlert('Notification settings saved successfully!', 'success');
                await this.loadUserProfile();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save notification settings');
            }
        } catch (error) {
            console.error('Error saving notification settings:', error);
            showAlert(error.message || 'Failed to save notification settings', 'error');
        }
    }
    
    setupSecurityPageListeners() {
    // Add back button listener
    const backBtn = document.getElementById('back-to-dashboard');
    if (backBtn) {
        backBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.closeSettings();
        });
    }
    
    const changePasswordBtn = document.getElementById('change-password-btn');
    if (changePasswordBtn) {
        changePasswordBtn.addEventListener('click', async () => await this.changePassword());
    }
    
    const enableEmail2fa = document.getElementById('enable-email-2fa');
    if (enableEmail2fa) {
        enableEmail2fa.addEventListener('change', async () => {
            const enabled = enableEmail2fa.checked;
            await this.toggleEmail2FA(enabled);
        });
    }
}
    
    async changePassword() {
        const currentPassword = document.getElementById('current-password')?.value;
        const newPassword = document.getElementById('new-password')?.value;
        const confirmPassword = document.getElementById('confirm-password')?.value;
        
        if (!currentPassword || !newPassword || !confirmPassword) {
            showAlert('Please fill in all password fields', 'error');
            return;
        }
        
        if (newPassword !== confirmPassword) {
            showAlert('New passwords do not match', 'error');
            return;
        }
        
        if (newPassword.length < 8) {
            showAlert('New password must be at least 8 characters', 'error');
            return;
        }
        
        try {
            const token = localStorage.getItem('weather_ai_token');
            if (!token) {
                showAlert('Please login again', 'error');
                return;
            }
            
            const response = await fetch(`${API_BASE_URL}/api/user/change-password`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json', 
                    'Authorization': `Bearer ${token}` 
                },
                body: JSON.stringify({ 
                    current_password: currentPassword, 
                    new_password: newPassword 
                })
            });
            
            if (response.ok) {
                showAlert('Password changed successfully!', 'success');
                document.getElementById('current-password').value = '';
                document.getElementById('new-password').value = '';
                document.getElementById('confirm-password').value = '';
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to change password');
            }
        } catch (error) {
            console.error('Error changing password:', error);
            showAlert(error.message || 'Failed to change password', 'error');
        }
    }

    async toggleEmail2FA(enabled) {
        this.show2FAPasswordModal(enabled ? 'enable' : 'disable');
    }

    show2FAPasswordModal(action) {
        const actionText = action === 'enable' ? 'Enable' : 'Disable';
        const actionDesc = action === 'enable' ? 'enabling' : 'disabling';

        const modalHtml = `
            <div class="modal fade show" id="twoFAModal" style="display: block; background: rgba(0,0,0,0.5); position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 10000;">
                <div class="modal-dialog modal-dialog-centered" style="max-width: 400px; margin: 50px auto;">
                    <div class="modal-content" style="background: white; border-radius: 16px; overflow: hidden;">
                        <div class="modal-header" style="padding: 20px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                            <h5 class="modal-title" style="margin: 0; font-weight: 700;">
                                <i class="fas fa-shield-alt" style="color: var(--primary-color); margin-right: 8px;"></i>
                                ${actionText} Email 2FA
                            </h5>
                            <button type="button" class="btn-close" onclick="document.getElementById('twoFAModal')?.remove()" style="background: none; border: none; font-size: 20px; cursor: pointer;">×</button>
                        </div>
                        <div class="modal-body" style="padding: 20px;">
                            <div class="alert alert-info" style="background: rgba(26, 107, 179, 0.1); padding: 12px; border-radius: 10px; font-size: 13px; margin-bottom: 15px;">
                                <i class="fas fa-info-circle"></i> Please enter your password to confirm ${actionDesc} email 2FA.
                            </div>
                            <div class="form-group" style="margin-bottom: 15px;">
                                <label class="form-label">Your Password</label>
                                <input type="password" class="form-control" id="twofa-password" placeholder="Enter your password">
                            </div>
                        </div>
                        <div class="modal-footer" style="padding: 20px; border-top: 1px solid var(--border-color); display: flex; justify-content: flex-end; gap: 10px;">
                            <button class="btn btn-secondary" type="button" onclick="document.getElementById('twoFAModal')?.remove()">Cancel</button>
                            <button class="btn btn-primary" type="button" id="confirm-twofa-btn">${actionText} 2FA</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const existingModal = document.getElementById('twoFAModal');
        if (existingModal) existingModal.remove();

        const modalDiv = document.createElement('div');
        modalDiv.innerHTML = modalHtml;
        document.body.appendChild(modalDiv);

        document.getElementById('confirm-twofa-btn')?.addEventListener('click', async () => {
            const password = document.getElementById('twofa-password')?.value.trim();
            if (!password) {
                showAlert('Please enter your password', 'error');
                return;
            }
            document.getElementById('twoFAModal')?.remove();
            await this.process2FAToggle(action, password);
        });
    }

    async process2FAToggle(action, password) {
        const isEnable = action === 'enable';
        const endpoint = isEnable ? 'enable' : 'disable';
        const successMessage = isEnable ?
            '✅ Email 2FA enabled successfully! You will now receive verification codes via email when logging in.' :
            'Email 2FA disabled successfully';

        try {
            const token = localStorage.getItem('weather_ai_token');
            const response = await fetch(`${API_BASE_URL}/api/user/email-2fa/${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ password })
            });

            const data = await response.json();

            if (response.ok) {
                showAlert(successMessage, 'success');
                await this.loadUserProfile();
            } else {
                // Revert the toggle
                document.getElementById('enable-email-2fa').checked = !isEnable;
                throw new Error(data.detail || `Failed to ${action} email 2FA`);
            }
        } catch (error) {
            showAlert(error.message, 'error');
            document.getElementById('enable-email-2fa').checked = !isEnable;
        }
    }
    


    setupApiKeysPageListeners() {
        const generateBtn = document.getElementById('generate-api-key-btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', async () => await this.generateApiKey());
        }
        
        // Load existing keys once the API keys page opens
        this.loadApiKeys().catch(error => console.error('Unable to load API keys:', error));
    }
    
    async generateApiKey() {
        const keyType = document.getElementById('api-key-type')?.value || 'read';
        const keyName = document.getElementById('api-key-name')?.value;
        
        if (!keyName || !keyName.trim()) {
            showAlert('Please enter a name for the API key', 'error');
            return;
        }
        
        try {
            const token = localStorage.getItem('weather_ai_token');
            if (!token) {
                showAlert('Please login again', 'error');
                return;
            }
            
            const response = await fetch(`${API_BASE_URL}/api/user/generate-api-key`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json', 
                    'Authorization': `Bearer ${token}` 
                },
                body: JSON.stringify({ name: keyName, type: keyType })
            });
            
            if (response.ok) {
                const result = await response.json();
                showAlert('API key generated successfully!', 'success');
                // Display the API key to the user (they should copy it now)
                showAlert(`Your new API key: ${result.api_key} - Please copy it now, it won't be shown again!`, 'info');
                await this.loadApiKeys();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to generate API key');
            }
        } catch (error) {
            console.error('Error generating API key:', error);
            showAlert(error.message || 'Failed to generate API key', 'error');
        }
    }
    
    async loadApiKeys() {
        try {
            const token = localStorage.getItem('weather_ai_token');
            if (!token) return;
            
            const response = await fetch(`${API_BASE_URL}/api/user/api-keys`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (response.ok) {
                const data = await response.json();
                const tableBody = document.getElementById('api-keys-table');
                
                if (tableBody) {
                    if (data.api_keys && data.api_keys.length > 0) {
                        tableBody.innerHTML = data.api_keys.map(key => `
                            <tr>
                                <td>${key.key_name}</td>
                                <td>${key.api_key.substring(0, 8)}...${key.api_key.substring(key.api_key.length - 4)}</td>
                                <td><span class="badge-${key.permissions}">${key.permissions}</span></td>
                                <td>${new Date(key.created_at).toLocaleDateString()}</td>
                                <td>${key.last_used ? new Date(key.last_used).toLocaleDateString() : 'Never'}</td>
                                <td>
                                    <button class="btn btn-sm btn-danger" onclick="window.userProfileManager?.revokeApiKey(${key.id})">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join('');
                    } else {
                        tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 40px;">No API keys generated yet.</td></tr>';
                    }
                }
            } else {
                console.error('Failed to load API keys:', response.status);
            }
        } catch (error) {
            console.error('Error loading API keys:', error);
        }
    }

    async revokeApiKey(apiKeyId) {
        if (!confirm('Are you sure you want to revoke this API key?')) {
            return;
        }

        try {
            const token = localStorage.getItem('weather_ai_token');
            if (!token) {
                showAlert('Please login again', 'error');
                return;
            }

            const response = await fetch(`${API_BASE_URL}/api/user/api-keys/${apiKeyId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                showAlert('API key revoked successfully.', 'success');
                await this.loadApiKeys();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to revoke API key');
            }
        } catch (error) {
            console.error('Error revoking API key:', error);
            showAlert(error.message || 'Failed to revoke API key', 'error');
        }
    }
    
    setupUsagePageListeners() {
        this.createUsageChart();
    }
    
    createUsageChart() {
        const ctx = document.getElementById('usageChart')?.getContext('2d');
        if (!ctx) return;
        
        // Get real usage data if available
        const weatherChecks = this.usageStats?.daily_weather_checks || [10, 15, 8, 12, 18, 5, 9];
        const anomalyDetections = this.usageStats?.daily_anomaly_detections || [2, 5, 3, 4, 6, 1, 3];
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [
                    { 
                        label: 'Weather Checks', 
                        data: weatherChecks, 
                        backgroundColor: 'rgba(26, 107, 179, 0.8)', 
                        borderColor: '#1a6bb3', 
                        borderWidth: 1 
                    },
                    { 
                        label: 'Anomaly Detections', 
                        data: anomalyDetections, 
                        backgroundColor: 'rgba(247, 37, 133, 0.8)', 
                        borderColor: '#f72585', 
                        borderWidth: 1 
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    title: { display: true, text: 'Weekly Usage Activity' }
                },
                scales: {
                    y: { 
                        beginAtZero: true, 
                        title: { display: true, text: 'Number of Requests' },
                        grid: { color: 'rgba(0,0,0,0.05)' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }
    
   setupBillingPageListeners() {
    // Add back button listener
    const backBtn = document.getElementById('back-to-dashboard');
    if (backBtn) {
        backBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.closeSettings();
        });
    }
    
    const addPaymentBtn = document.getElementById('add-payment-method-btn');
    if (addPaymentBtn) {
        addPaymentBtn.addEventListener('click', () => this.addPaymentMethod());
    }
}
    
  closeSettings() {
    document.body.classList.remove('settings-open');
    // Close dropdown if open
    if (this.isDropdownOpen) {
        this.isDropdownOpen = false;
        this.dropdown.style.display = 'none';
        this.cleanupMobileDropdown();
        this.updateDropdownChevron(false);
    }
    
    // Hide settings container
    const settingsContainer = document.getElementById('settings-container');
    if (settingsContainer) {
        settingsContainer.style.display = 'none';
        // Move it back to original position (after all page-content divs)
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.appendChild(settingsContainer);
        }
    }
    
    // Hide all settings pages
    document.querySelectorAll('.settings-page').forEach(page => {
        page.style.display = 'none';
        page.classList.remove('active');
    });
    
    // Show dashboard page ONLY - don't trigger showSection
    const dashboardPage = document.getElementById('dashboard-page');
    if (dashboardPage) {
        dashboardPage.style.display = 'block';
    }
    
    // Update navigation without triggering click events
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('data-section') === 'dashboard') {
            item.classList.add('active');
        }
    });
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
    
    
    getInitials(name) {
        if (!name) return 'U';
        return name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
    }
    
    setFallbackUserData() {
        this.userData = {
            full_name: 'Weather AI User',
            email: 'user@example.com',
            account_type: 'Administrator',
            created_at: new Date().toISOString(),
            last_login: new Date().toISOString()
        };
        
        this.userPreferences = {
            language: 'en',
            timezone: 'UTC',
            date_format: 'MM/DD/YYYY',
            temperature_unit: 'celsius',
            wind_speed_unit: 'kmh',
            pressure_unit: 'hpa',
            distance_unit: 'km',
            theme: 'light',
            notifications_email: true,
            anomaly_alerts: true,
            weekly_reports: false,
            system_updates: true,
            two_factor_auth: false
        };
        
        this.usageStats = { 
            weather_checks: 45, 
            anomaly_detections: 12, 
            api_calls: 89, 
            active_days: 7,
            daily_weather_checks: [10, 15, 8, 12, 18, 5, 9],
            daily_anomaly_detections: [2, 5, 3, 4, 6, 1, 3]
        };
        
        this.updateUserDisplay();
        this.updateDropdownContent();
    }
    
    async exportUserData() {
        try {
            const token = localStorage.getItem('weather_ai_token');
            if (!token) {
                showAlert('Please login again', 'error');
                return;
            }
            
            showAlert('Preparing your data export...', 'info');
            
            const userResponse = await fetch(`${API_BASE_URL}/api/user/profile`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!userResponse.ok) throw new Error('Failed to fetch user data');
            const userData = await userResponse.json();
            
            const activityResponse = await fetch(`${API_BASE_URL}/api/analytics/recent-activity?limit=1000`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const activityData = activityResponse.ok ? await activityResponse.json() : { activities: [] };
            
            const exportData = {
                user_profile: userData.user,
                preferences: userData.preferences,
                usage_stats: userData.usage_stats,
                activity_history: activityData.activities,
                export_date: new Date().toISOString(),
                export_format: 'JSON',
                app_version: '3.0.0'
            };
            
            const dataStr = JSON.stringify(exportData, null, 2);
            const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
            const exportFileName = `weather-ai-export-${new Date().toISOString().split('T')[0]}.json`;
            
            const linkElement = document.createElement('a');
            linkElement.setAttribute('href', dataUri);
            linkElement.setAttribute('download', exportFileName);
            linkElement.click();
            
            showAlert('Data exported successfully!', 'success');
        } catch (error) {
            console.error('Error exporting data:', error);
            showAlert('Failed to export data: ' + error.message, 'error');
        }
    }
    
    openFeedbackModal() {
        const modalHtml = `
            <div class="modal fade show" id="feedbackModal" style="display: block; background: rgba(0,0,0,0.5); position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 9999;">
                <div class="modal-dialog modal-dialog-centered" style="max-width: 500px; margin: 50px auto;">
                    <div class="modal-content" style="background: white; border-radius: 16px; overflow: hidden;">
                        <div class="modal-header" style="padding: 20px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                            <h5 class="modal-title" style="margin: 0;"><i class="fas fa-comment-alt" style="color: var(--primary-color); margin-right: 8px;"></i> Send Feedback</h5>
                            <button type="button" class="btn-close" id="close-feedback" style="background: none; border: none; font-size: 20px; cursor: pointer;">×</button>
                        </div>
                        <div class="modal-body" style="padding: 20px;">
                            <div class="form-group" style="margin-bottom: 15px;">
                                <label class="form-label" style="display: block; margin-bottom: 5px; font-weight: 500;">Feedback Type</label>
                                <select class="form-select" id="feedback-type" style="width: 100%; padding: 10px; border-radius: 8px; border: 1px solid var(--border-color);">
                                    <option value="bug">Bug Report</option>
                                    <option value="feature">Feature Request</option>
                                    <option value="improvement">Improvement Suggestion</option>
                                    <option value="general">General Feedback</option>
                                </select>
                            </div>
                            <div class="form-group" style="margin-bottom: 15px;">
                                <label class="form-label" style="display: block; margin-bottom: 5px; font-weight: 500;">Message</label>
                                <textarea class="form-control" id="feedback-message" rows="4" placeholder="Tell us what you think..." style="width: 100%; padding: 10px; border-radius: 8px; border: 1px solid var(--border-color);"></textarea>
                            </div>
                            <div class="form-group" style="margin-bottom: 15px;">
                                <label class="form-label" style="display: block; margin-bottom: 5px; font-weight: 500;">Email (for follow-up)</label>
                                <input type="email" class="form-control" id="feedback-email" value="${this.userData?.email || ''}" style="width: 100%; padding: 10px; border-radius: 8px; border: 1px solid var(--border-color);">
                            </div>
                        </div>
                        <div class="modal-footer" style="padding: 20px; border-top: 1px solid var(--border-color); display: flex; justify-content: flex-end; gap: 10px;">
                            <button type="button" class="btn btn-secondary" id="cancel-feedback" style="padding: 10px 20px; border-radius: 8px; border: none; background: var(--border-color); cursor: pointer;">Cancel</button>
                            <button type="button" class="btn btn-primary" id="submit-feedback" style="padding: 10px 20px; border-radius: 8px; border: none; background: var(--gradient-primary); color: white; cursor: pointer;"><i class="fas fa-paper-plane"></i> Send Feedback</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const modalDiv = document.createElement('div');
        modalDiv.innerHTML = modalHtml;
        document.body.appendChild(modalDiv);
        
        document.getElementById('close-feedback')?.addEventListener('click', () => document.body.removeChild(modalDiv));
        document.getElementById('cancel-feedback')?.addEventListener('click', () => document.body.removeChild(modalDiv));
        
        document.getElementById('submit-feedback')?.addEventListener('click', async () => {
            const message = document.getElementById('feedback-message')?.value;
            const type = document.getElementById('feedback-type')?.value;
            const email = document.getElementById('feedback-email')?.value;

            if (!message || !message.trim()) {
                showAlert('Please enter a feedback message', 'error');
                return;
            }

            if (!email || !email.trim()) {
                showAlert('Please enter your email address', 'error');
                return;
            }

            try {
                const token = localStorage.getItem('weather_ai_token');
                const response = await fetch(`${API_BASE_URL}/api/feedback`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': token ? `Bearer ${token}` : ''
                    },
                    body: JSON.stringify({
                        message: message.trim(),
                        type: type,
                        email: email.trim(),
                        user_agent: navigator.userAgent,
                        timestamp: new Date().toISOString()
                    })
                });

                if (response.ok) {
                    showAlert(`Thank you for your ${type} feedback! We'll review it shortly.`, 'success');
                    document.body.removeChild(modalDiv);
                } else {
                    const error = await response.json();
                    throw new Error(error.detail || 'Failed to send feedback');
                }
            } catch (error) {
                console.error('Error sending feedback:', error);
                showAlert(error.message || 'Failed to send feedback. Please try again.', 'error');
            }
        });
        
        modalDiv.addEventListener('click', (e) => {
            if (e.target === modalDiv) document.body.removeChild(modalDiv);
        });
    }
    
  
}