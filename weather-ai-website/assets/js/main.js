// main.js

// Main JavaScript for Weather AI Website

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    initializeWebsite();
    setupEventListeners();
    initializeAnimations();
});

// Initialize Website
function initializeWebsite() {
    console.log('Weather AI Website Initialized');
    
    // Set current year in footer
    document.querySelectorAll('.current-year').forEach(el => {
        el.textContent = new Date().getFullYear();
    });
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize popovers
    initializePopovers();
    
    // Setup form validation
    setupFormValidation();
    
    // Setup scroll spy
    setupScrollSpy();
}

// Setup Event Listeners
function setupEventListeners() {
    // Demo video play button
    const playButton = document.querySelector('.play-button');
    if (playButton) {
        playButton.addEventListener('click', function() {
            playDemoVideo();
        });
    }
    
    // Newsletter subscription
    const newsletterForm = document.querySelector('.newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', handleNewsletterSubmit);
    }
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]:not([href="#"])').forEach(anchor => {
        anchor.addEventListener('click', smoothScroll);
    });
    
    // Navbar toggle on mobile
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            document.querySelector('.navbar-collapse').classList.toggle('show');
        });
    }
    
    // Close mobile menu on click
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        link.addEventListener('click', function() {
            const navbarCollapse = document.querySelector('.navbar-collapse');
            if (navbarCollapse.classList.contains('show')) {
                navbarCollapse.classList.remove('show');
            }
        });
    });
}

// Initialize Animations
function initializeAnimations() {
    // Lazy load images with intersection observer
    if ('IntersectionObserver' in window) {
        const lazyImageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.add('fade-in');
                    lazyImageObserver.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            lazyImageObserver.observe(img);
        });
    }
    
    // Animate counters
    const counters = document.querySelectorAll('.counter');
    if (counters.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounter(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });

        counters.forEach(counter => {
            observer.observe(counter);
        });
    }
}

// Play Demo Video
function playDemoVideo() {
    const videoPlaceholder = document.querySelector('.video-placeholder');
    if (videoPlaceholder) {
        videoPlaceholder.innerHTML = `
            <iframe 
                width="100%" 
                height="400" 
                src="https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1" 
                title="Weather AI Demo" 
                frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
            </iframe>
        `;
    }
}

// Handle Newsletter Subscription
async function handleNewsletterSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const email = form.querySelector('input[type="email"]').value;
    const submitBtn = form.querySelector('button[type="submit"]');
    
    if (!validateEmail(email)) {
        showAlert('Please enter a valid email address', 'error');
        return;
    }
    
    // Disable button and show loading
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Subscribing...';
    submitBtn.disabled = true;
    
    try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        showAlert('Successfully subscribed to our newsletter!', 'success');
        form.reset();
        
        // Track subscription
        trackEvent('newsletter_subscription', { email: email });
        
    } catch (error) {
        showAlert('Failed to subscribe. Please try again.', 'error');
    } finally {
        // Restore button
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// Animate Counter
function animateCounter(counter) {
    const target = parseInt(counter.dataset.target);
    const duration = parseInt(counter.dataset.duration) || 2000;
    const increment = target / (duration / 16); // 60fps
    
    let current = 0;
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        counter.textContent = Math.floor(current).toLocaleString();
    }, 16);
}

// Smooth Scroll
function smoothScroll(e) {
    e.preventDefault();
    const targetId = this.getAttribute('href');
    if (targetId === '#') return;
    
    const targetElement = document.querySelector(targetId);
    if (targetElement) {
        const headerHeight = document.querySelector('.navbar').offsetHeight;
        const targetPosition = targetElement.offsetTop - headerHeight;
        
        window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
        });
    }
}

// Initialize Tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize Popovers
function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Setup Form Validation
function setupFormValidation() {
    // Add validation styles
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

// Setup Scroll Spy
function setupScrollSpy() {
    // Update active nav link on scroll
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (pageYOffset >= sectionTop - 100) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });
}

// Show Alert
function showAlert(message, type = 'info') {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.custom-alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `custom-alert alert-${type} fade-in`;
    alertDiv.innerHTML = `
        <div class="alert-content">
            <i class="fas fa-${getAlertIcon(type)}"></i>
            <span>${message}</span>
            <button class="alert-close">&times;</button>
        </div>
    `;
    
    // Style alert
    Object.assign(alertDiv.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '15px 20px',
        borderRadius: '10px',
        boxShadow: '0 5px 15px rgba(0,0,0,0.1)',
        zIndex: '9999',
        minWidth: '300px',
        maxWidth: '400px',
        backgroundColor: getAlertColor(type),
        color: 'white',
        fontWeight: '500'
    });
    
    document.body.appendChild(alertDiv);
    
    // Add close functionality
    const closeBtn = alertDiv.querySelector('.alert-close');
    closeBtn.addEventListener('click', () => {
        alertDiv.remove();
    });
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function getAlertIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

function getAlertColor(type) {
    const colors = {
        success: '#4cc9f0',
        error: '#ff006e',
        warning: '#ff9e00',
        info: '#4361ee'
    };
    return colors[type] || '#4361ee';
}

// Validate Email
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Track Event (for analytics)
function trackEvent(eventName, data = {}) {
    // In production, you would send this to your analytics service
    console.log(`Event: ${eventName}`, data);
    
    // Example: Send to Google Analytics (if available)
    if (typeof gtag !== 'undefined') {
        gtag('event', eventName, data);
    }
}

// Cookie Consent
function setupCookieConsent() {
    if (!localStorage.getItem('cookie-consent')) {
        const consentDiv = document.createElement('div');
        consentDiv.className = 'cookie-consent fade-in-up';
        consentDiv.innerHTML = `
            <div class="cookie-content">
                <p>We use cookies to enhance your experience. By continuing to visit this site you agree to our use of cookies.</p>
                <div class="cookie-buttons">
                    <button class="btn btn-primary btn-sm" id="accept-cookies">Accept</button>
                    <button class="btn btn-outline-primary btn-sm" id="reject-cookies">Reject</button>
                </div>
            </div>
        `;
        
        // Style consent banner
        Object.assign(consentDiv.style, {
            position: 'fixed',
            bottom: '0',
            left: '0',
            right: '0',
            backgroundColor: 'white',
            padding: '20px',
            boxShadow: '0 -2px 20px rgba(0,0,0,0.1)',
            zIndex: '9998'
        });
        
        document.body.appendChild(consentDiv);
        
        // Add event listeners
        document.getElementById('accept-cookies').addEventListener('click', () => {
            localStorage.setItem('cookie-consent', 'accepted');
            consentDiv.remove();
            showAlert('Cookies accepted', 'success');
        });
        
        document.getElementById('reject-cookies').addEventListener('click', () => {
            localStorage.setItem('cookie-consent', 'rejected');
            consentDiv.remove();
        });
    }
}

// Theme Toggle (Dark/Light mode)
function setupThemeToggle() {
    const themeToggle = document.querySelector('#theme-toggle');
    if (themeToggle) {
        // Check for saved theme preference
        const currentTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', currentTheme);
        
        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Update icon
            const icon = themeToggle.querySelector('i');
            icon.className = newTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
            
            showAlert(`Switched to ${newTheme} mode`, 'info');
        });
    }
}

// Initialize on window load
window.addEventListener('load', function() {
    // Setup cookie consent
    setupCookieConsent();
    
    // Setup theme toggle
    setupThemeToggle();
    
    // Remove preloader if exists
    const preloader = document.querySelector('.preloader');
    if (preloader) {
        preloader.classList.add('fade-out');
        setTimeout(() => {
            preloader.remove();
        }, 500);
    }
});

// Export functions for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeWebsite,
        showAlert,
        validateEmail,
        trackEvent
    };
}