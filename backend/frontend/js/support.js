// ============ HELP & SUPPORT PAGE ============

// Main initialization function
function setupSupport() {
    console.log('📞 Setting up Help & Support page...');
    
    const sendSupportBtn = document.getElementById('send-support-btn');
    if (sendSupportBtn) {
        // Remove any existing listeners to prevent duplicates
        sendSupportBtn.removeEventListener('click', sendSupportMessage);
        sendSupportBtn.addEventListener('click', sendSupportMessage);
        console.log('✅ Support button listener attached');
    } else {
        console.warn('⚠️ Support button not found in DOM');
    }

    // Setup form validation
    setupSupportFormValidation();
    
    // Load FAQ data if needed
    loadFAQs();
}

// Form validation
function setupSupportFormValidation() {
    const emailInput = document.getElementById('support-email');
    const subjectInput = document.getElementById('support-subject');
    const messageInput = document.getElementById('support-message');
    
    if (emailInput) {
        emailInput.addEventListener('input', function() {
            validateEmailField(this);
        });
    }
    
    if (subjectInput) {
        subjectInput.addEventListener('input', function() {
            validateSubjectField(this);
        });
    }
    
    if (messageInput) {
        messageInput.addEventListener('input', function() {
            validateMessageField(this);
        });
    }
}

function validateEmailField(field) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = emailRegex.test(field.value.trim());
    
    if (field.value.trim() && !isValid) {
        field.style.borderColor = '#ef4444';
        showFieldError(field, 'Please enter a valid email address');
        return false;
    } else if (field.value.trim() && isValid) {
        field.style.borderColor = '#10b981';
        hideFieldError(field);
        return true;
    } else {
        field.style.borderColor = '';
        hideFieldError(field);
        return false;
    }
}

function validateSubjectField(field) {
    const value = field.value.trim();
    const isValid = value.length >= 3;
    
    if (value && !isValid) {
        field.style.borderColor = '#ef4444';
        showFieldError(field, 'Subject must be at least 3 characters');
        return false;
    } else if (value && isValid) {
        field.style.borderColor = '#10b981';
        hideFieldError(field);
        return true;
    } else {
        field.style.borderColor = '';
        hideFieldError(field);
        return false;
    }
}

function validateMessageField(field) {
    const value = field.value.trim();
    const isValid = value.length >= 10;
    
    if (value && !isValid) {
        field.style.borderColor = '#ef4444';
        showFieldError(field, 'Message must be at least 10 characters');
        return false;
    } else if (value && isValid) {
        field.style.borderColor = '#10b981';
        hideFieldError(field);
        return true;
    } else {
        field.style.borderColor = '';
        hideFieldError(field);
        return false;
    }
}

function showFieldError(field, message) {
    // Remove existing error message if any
    hideFieldError(field);
    
    // Create error message element
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error-message';
    errorDiv.style.cssText = `
        color: #ef4444;
        font-size: 12px;
        margin-top: 5px;
        display: flex;
        align-items: center;
        gap: 5px;
    `;
    errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    
    // Insert after the field
    field.parentNode.appendChild(errorDiv);
}

function hideFieldError(field) {
    const existingError = field.parentNode.querySelector('.field-error-message');
    if (existingError) {
        existingError.remove();
    }
}

// Main function to send support message
async function sendSupportMessage() {
    console.log('📤 Sending support message...');
    
    // Get form elements
    const emailInput = document.getElementById('support-email');
    const subjectInput = document.getElementById('support-subject');
    const messageInput = document.getElementById('support-message');
    
    // Get values
    const email = emailInput ? emailInput.value.trim() : '';
    const subject = subjectInput ? subjectInput.value.trim() : '';
    const message = messageInput ? messageInput.value.trim() : '';
    
    // Validate all fields
    const isEmailValid = email && validateEmailField(emailInput);
    const isSubjectValid = subject && validateSubjectField(subjectInput);
    const isMessageValid = message && validateMessageField(messageInput);
    
    if (!isEmailValid || !isSubjectValid || !isMessageValid) {
        showAlert('Please fill in all fields correctly', 'error');
        
        // Highlight empty fields
        if (!email) {
            emailInput.style.borderColor = '#ef4444';
            showFieldError(emailInput, 'Email is required');
        }
        if (!subject) {
            subjectInput.style.borderColor = '#ef4444';
            showFieldError(subjectInput, 'Subject is required');
        }
        if (!message) {
            messageInput.style.borderColor = '#ef4444';
            showFieldError(messageInput, 'Message is required');
        }
        return;
    }
    
    // Show loading state
    const sendBtn = document.getElementById('send-support-btn');
    const originalText = sendBtn.innerHTML;
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    
    try {
        // Prepare form data for API
        const formData = {
            first_name: currentUser?.full_name?.split(' ')[0] || 'User',
            last_name: currentUser?.full_name?.split(' ').slice(1).join(' ') || 'Name',
            email: email,
            phone: '',
            company: '',
            inquiry_type: 'General Inquiry',
            message: `Subject: ${subject}\n\n${message}`,
            newsletter: false
        };
        
        // Send to backend API
        const response = await fetch(`${API_BASE_URL}/api/contact/send`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            // Show success message
            showAlert(result.message || 'Support message sent successfully! We\'ll get back to you soon.', 'success');
            
            // Clear form
            if (emailInput) emailInput.value = '';
            if (subjectInput) subjectInput.value = '';
            if (messageInput) messageInput.value = '';
            
            // Reset field styles
            [emailInput, subjectInput, messageInput].forEach(field => {
                if (field) {
                    field.style.borderColor = '';
                    hideFieldError(field);
                }
            });
            
            // Log to console for debugging
            console.log('✅ Support message sent successfully:', result);
            
            // Optionally show a thank you modal or additional info
            showSupportConfirmation();
        } else {
            throw new Error(result.detail || 'Failed to send message');
        }
        
    } catch (error) {
        console.error('❌ Error sending support message:', error);
        showAlert('Failed to send message. Please try again or email us directly at saadyousafzai420@gmail.com', 'error');
    } finally {
        // Reset button state
        sendBtn.disabled = false;
        sendBtn.innerHTML = originalText;
    }
}

// Show confirmation dialog
function showSupportConfirmation() {
    // Create modal if it doesn't exist
    if (!document.getElementById('support-confirmation-modal')) {
        const modal = document.createElement('div');
        modal.id = 'support-confirmation-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-check-circle" style="color: #10b981;"></i>
                            Message Sent Successfully!
                        </h5>
                        <button type="button" class="btn-close" data-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Thank you for contacting Weather AI support. Our team has received your message and will respond within 24 hours.</p>
                        
                        <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin: 15px 0;">
                            <h6 style="margin-bottom: 10px; color: #1a6bb3;">What happens next?</h6>
                            <ul style="list-style: none; padding: 0; margin: 0;">
                                <li style="margin-bottom: 8px;">
                                    <i class="fas fa-check-circle" style="color: #10b981; margin-right: 8px;"></i>
                                    You'll receive a confirmation email shortly
                                </li>
                                <li style="margin-bottom: 8px;">
                                    <i class="fas fa-check-circle" style="color: #10b981; margin-right: 8px;"></i>
                                    Our support team will review your inquiry
                                </li>
                                <li style="margin-bottom: 8px;">
                                    <i class="fas fa-check-circle" style="color: #10b981; margin-right: 8px;"></i>
                                    We'll respond via email within 24 hours
                                </li>
                            </ul>
                        </div>
                        
                        <p style="color: #64748b; font-size: 14px;">
                            <i class="fas fa-info-circle"></i>
                            For urgent matters, you can also email us directly at <strong>saadyousafzai420@gmail.com</strong>
                        </p>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-primary" onclick="document.getElementById('support-confirmation-modal').style.display='none'">
                            <i class="fas fa-check"></i>
                            Got it
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Add close functionality
        const closeBtn = modal.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                modal.style.display = 'none';
            });
        }
    }
    
    // Show modal
    const modal = document.getElementById('support-confirmation-modal');
    modal.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (modal.style.display === 'block') {
            modal.style.display = 'none';
        }
    }, 5000);
}

// Load FAQ data
async function loadFAQs() {
    // You can fetch FAQs from an API or use static data
    const faqData = [
        {
            question: "How does the anomaly detection work?",
            answer: "Our system uses ensemble machine learning including Isolation Forest, Autoencoder, LSTM, Prophet, ARIMA, and Z-Score analysis to detect weather anomalies with high accuracy."
        },
        {
            question: "What data sources do you use?",
            answer: "We primarily use OpenWeatherMap API for real-time weather data, combined with historical patterns and machine learning models for predictions."
        },
        {
            question: "How accurate are the predictions?",
            answer: "Our ensemble model typically achieves 94-96% accuracy for anomaly detection, with confidence scores provided for each prediction."
        },
        {
            question: "Can I use the API for my own applications?",
            answer: "Yes! You can generate API keys from your account settings page to integrate our weather anomaly detection into your own applications."
        }
    ];
    
    // Create FAQ section if it doesn't exist
    const supportPage = document.getElementById('help-page');
    if (supportPage && !document.getElementById('faq-section')) {
        const faqSection = document.createElement('div');
        faqSection.id = 'faq-section';
        faqSection.className = 'settings-section';
        faqSection.innerHTML = `
            <h3 class="section-title"><i class="fas fa-question-circle"></i> Frequently Asked Questions</h3>
            <div id="faq-container"></div>
        `;
        
        // Insert after contact form
        const contactSection = supportPage.querySelector('.settings-section');
        if (contactSection) {
            contactSection.parentNode.insertBefore(faqSection, contactSection.nextSibling);
        }
        
        const faqContainer = document.getElementById('faq-container');
        if (faqContainer) {
            faqData.forEach(faq => {
                const faqItem = document.createElement('div');
                faqItem.className = 'faq-item';
                faqItem.style.cssText = `
                    margin-bottom: 15px;
                    padding: 15px;
                    background: #f8fafc;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                `;
                faqItem.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong>${faq.question}</strong>
                        <i class="fas fa-chevron-down"></i>
                    </div>
                    <div class="faq-answer" style="display: none; margin-top: 10px; color: #64748b;">
                        ${faq.answer}
                    </div>
                `;
                
                faqItem.addEventListener('click', function() {
                    const answer = this.querySelector('.faq-answer');
                    const icon = this.querySelector('i');
                    
                    if (answer.style.display === 'none') {
                        answer.style.display = 'block';
                        icon.classList.remove('fa-chevron-down');
                        icon.classList.add('fa-chevron-up');
                    } else {
                        answer.style.display = 'none';
                        icon.classList.remove('fa-chevron-up');
                        icon.classList.add('fa-chevron-down');
                    }
                });
                
                faqContainer.appendChild(faqItem);
            });
        }
    }
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        setupSupport,
        sendSupportMessage,
        loadFAQs
    };
}