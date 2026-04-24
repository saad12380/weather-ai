// navigation.js

// Navigation JavaScript for Weather AI Website

class NavigationManager {
    constructor() {
        this.currentPage = '';
        this.navLinks = [];
        this.mobileMenuOpen = false;
        this.init();
    }
    
    init() {
        this.cacheElements();
        this.setupEventListeners();
        this.updateCurrentPage();
        this.setupScrollToTop();
    }
    
    cacheElements() {
        this.navbar = document.querySelector('.navbar');
        this.navbarToggler = document.querySelector('.navbar-toggler');
        this.navbarCollapse = document.querySelector('.navbar-collapse');
        this.navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        this.scrollToTopBtn = document.querySelector('.scroll-to-top');
    }
    
    setupEventListeners() {
        // Navbar scroll effect
        window.addEventListener('scroll', () => this.handleScroll());
        
        // Mobile menu toggle
        if (this.navbarToggler) {
            this.navbarToggler.addEventListener('click', () => this.toggleMobileMenu());
        }
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => this.handleOutsideClick(e));
        
        // Nav link clicks
        this.navLinks.forEach(link => {
            link.addEventListener('click', (e) => this.handleNavLinkClick(e));
        });
        
        // Scroll to top button
        if (this.scrollToTopBtn) {
            this.scrollToTopBtn.addEventListener('click', () => this.scrollToTop());
        }
    }
    
    handleScroll() {
        // Navbar background on scroll
        if (window.scrollY > 50) {
            this.navbar.classList.add('navbar-scrolled');
        } else {
            this.navbar.classList.remove('navbar-scrolled');
        }
        
        // Show/hide scroll to top button
        if (this.scrollToTopBtn) {
            if (window.scrollY > 300) {
                this.scrollToTopBtn.classList.add('visible');
            } else {
                this.scrollToTopBtn.classList.remove('visible');
            }
        }
        
        // Update active nav link based on scroll position
        this.updateActiveNavLink();
    }
    
    toggleMobileMenu() {
        this.mobileMenuOpen = !this.mobileMenuOpen;
        this.navbarCollapse.classList.toggle('show');
        this.navbarToggler.setAttribute('aria-expanded', this.mobileMenuOpen);
        
        // Add animation class
        if (this.mobileMenuOpen) {
            this.navbarCollapse.classList.add('fade-in-down');
        }
    }
    
    handleOutsideClick(event) {
        if (!this.navbar.contains(event.target) && this.mobileMenuOpen) {
            this.closeMobileMenu();
        }
    }
    
    closeMobileMenu() {
        this.mobileMenuOpen = false;
        this.navbarCollapse.classList.remove('show');
        this.navbarToggler.setAttribute('aria-expanded', 'false');
    }
    
    handleNavLinkClick(event) {
        const link = event.currentTarget;
        const href = link.getAttribute('href');
        
        // Handle internal anchor links
        if (href.startsWith('#')) {
            event.preventDefault();
            this.scrollToSection(href);
        }
        
        // Close mobile menu after click
        if (this.mobileMenuOpen) {
            this.closeMobileMenu();
        }
        
        // Update active state
        this.setActiveNavLink(link);
    }
    
    scrollToSection(sectionId) {
        const section = document.querySelector(sectionId);
        if (section) {
            const headerHeight = this.navbar.offsetHeight;
            const sectionPosition = section.offsetTop - headerHeight;
            
            window.scrollTo({
                top: sectionPosition,
                behavior: 'smooth'
            });
        }
    }
    
    updateCurrentPage() {
        const path = window.location.pathname;
        this.currentPage = path.split('/').pop() || 'index.html';
        
        // Set active nav link based on current page
        this.setActiveNavLinkByPage();
    }
    
    setActiveNavLinkByPage() {
        this.navLinks.forEach(link => {
            const linkHref = link.getAttribute('href');
            if (linkHref === this.currentPage || 
                (this.currentPage === '' && linkHref === 'index.html')) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }
    
    setActiveNavLink(link) {
        this.navLinks.forEach(l => l.classList.remove('active'));
        link.classList.add('active');
    }
    
    updateActiveNavLink() {
        const sections = document.querySelectorAll('section[id]');
        let current = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            const headerHeight = this.navbar.offsetHeight;
            
            if (window.scrollY >= sectionTop - headerHeight - 50) {
                current = section.getAttribute('id');
            }
        });
        
        this.navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    }
    
    setupScrollToTop() {
        // Create scroll to top button if it doesn't exist
        if (!this.scrollToTopBtn) {
            this.scrollToTopBtn = document.createElement('button');
            this.scrollToTopBtn.className = 'scroll-to-top';
            this.scrollToTopBtn.innerHTML = '<i class="fas fa-chevron-up"></i>';
            this.scrollToTopBtn.setAttribute('aria-label', 'Scroll to top');
            document.body.appendChild(this.scrollToTopBtn);
            
            // Style the button
            Object.assign(this.scrollToTopBtn.style, {
                position: 'fixed',
                bottom: '30px',
                right: '30px',
                width: '50px',
                height: '50px',
                borderRadius: '50%',
                backgroundColor: '#4361ee',
                color: 'white',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.2rem',
                boxShadow: '0 4px 20px rgba(67, 97, 238, 0.3)',
                opacity: '0',
                transform: 'translateY(20px)',
                transition: 'all 0.3s ease',
                zIndex: '999'
            });
            
            this.scrollToTopBtn.addEventListener('click', () => this.scrollToTop());
        }
    }
    
    scrollToTop() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }
    
    // Breadcrumb Navigation
    generateBreadcrumbs() {
        const path = window.location.pathname;
        const paths = path.split('/').filter(p => p);
        
        const breadcrumbContainer = document.querySelector('.breadcrumb');
        if (!breadcrumbContainer) return;
        
        let breadcrumbHTML = '<nav aria-label="breadcrumb"><ol class="breadcrumb">';
        breadcrumbHTML += '<li class="breadcrumb-item"><a href="/">Home</a></li>';
        
        let accumulatedPath = '';
        paths.forEach((segment, index) => {
            accumulatedPath += '/' + segment;
            const pageName = this.formatPageName(segment);
            
            if (index === paths.length - 1) {
                // Current page
                breadcrumbHTML += `<li class="breadcrumb-item active" aria-current="page">${pageName}</li>`;
            } else {
                breadcrumbHTML += `<li class="breadcrumb-item"><a href="${accumulatedPath}">${pageName}</a></li>`;
            }
        });
        
        breadcrumbHTML += '</ol></nav>';
        breadcrumbContainer.innerHTML = breadcrumbHTML;
    }
    
    formatPageName(filename) {
        // Remove file extension and replace hyphens with spaces
        let name = filename.replace('.html', '');
        name = name.replace(/-/g, ' ');
        
        // Capitalize first letter of each word
        return name.split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
    
    // Responsive Navigation
    setupResponsiveNav() {
        const navbar = this.navbar;
        const navLinks = this.navLinks;
        
        // Add dropdown for mobile if many items
        if (window.innerWidth < 992 && navLinks.length > 5) {
            this.createMobileDropdown();
        }
        
        // Window resize handler
        window.addEventListener('resize', () => {
            if (window.innerWidth >= 992) {
                this.removeMobileDropdown();
            } else if (navLinks.length > 5) {
                this.createMobileDropdown();
            }
        });
    }
    
    createMobileDropdown() {
        if (document.querySelector('.nav-dropdown-mobile')) return;
        
        const navItems = Array.from(this.navLinks).slice(3); // Keep first 3 items visible
        if (navItems.length === 0) return;
        
        const dropdownContainer = document.createElement('li');
        dropdownContainer.className = 'nav-item dropdown nav-dropdown-mobile';
        
        const dropdownToggle = document.createElement('a');
        dropdownToggle.className = 'nav-link dropdown-toggle';
        dropdownToggle.href = '#';
        dropdownToggle.setAttribute('role', 'button');
        dropdownToggle.setAttribute('data-bs-toggle', 'dropdown');
        dropdownToggle.innerHTML = '<i class="fas fa-ellipsis-h"></i> More';
        
        const dropdownMenu = document.createElement('div');
        dropdownMenu.className = 'dropdown-menu dropdown-menu-end';
        
        navItems.forEach(item => {
            const dropdownItem = item.cloneNode(true);
            dropdownItem.classList.remove('nav-link');
            dropdownItem.classList.add('dropdown-item');
            dropdownMenu.appendChild(dropdownItem);
            
            // Hide original item
            item.parentElement.style.display = 'none';
        });
        
        dropdownContainer.appendChild(dropdownToggle);
        dropdownContainer.appendChild(dropdownMenu);
        
        // Find nav ul and insert dropdown before end
        const navUl = this.navbar.querySelector('.navbar-nav');
        if (navUl) {
            navUl.appendChild(dropdownContainer);
        }
    }
    
    removeMobileDropdown() {
        const dropdown = document.querySelector('.nav-dropdown-mobile');
        if (dropdown) {
            dropdown.remove();
            
            // Show all hidden nav items
            this.navLinks.forEach(link => {
                link.parentElement.style.display = '';
            });
        }
    }
    
    // Sticky Navigation
    setupStickyNav() {
        const stickyClass = 'navbar-sticky';
        const offset = 100;
        
        window.addEventListener('scroll', () => {
            if (window.scrollY > offset) {
                this.navbar.classList.add(stickyClass);
            } else {
                this.navbar.classList.remove(stickyClass);
            }
        });
    }
    
    // Page Transition
    setupPageTransitions() {
        const links = document.querySelectorAll('a:not([href^="#"])');
        
        links.forEach(link => {
            link.addEventListener('click', (e) => {
                const href = link.getAttribute('href');
                
                // Only handle internal links
                if (href && href.includes('.html') && !href.startsWith('http')) {
                    e.preventDefault();
                    this.animatePageTransition(href);
                }
            });
        });
    }
    
    animatePageTransition(newUrl) {
        const overlay = document.createElement('div');
        overlay.className = 'page-transition-overlay';
        
        Object.assign(overlay.style, {
            position: 'fixed',
            top: '0',
            left: '0',
            right: '0',
            bottom: '0',
            backgroundColor: 'white',
            zIndex: '9999',
            opacity: '0',
            transition: 'opacity 0.3s ease'
        });
        
        document.body.appendChild(overlay);
        
        // Fade in
        setTimeout(() => {
            overlay.style.opacity = '1';
        }, 10);
        
        // Navigate after animation
        setTimeout(() => {
            window.location.href = newUrl;
        }, 300);
    }
}

// Initialize Navigation Manager
let navigationManager;

document.addEventListener('DOMContentLoaded', () => {
    navigationManager = new NavigationManager();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NavigationManager;
}