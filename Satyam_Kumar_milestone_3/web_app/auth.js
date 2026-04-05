/**
 * Authentication JavaScript
 * Handles login, signup, validation, and API communication
 */

const API_BASE_URL = 'http://localhost:5000/api';

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastIcon = toast.querySelector('.toast-icon');
    const toastMessage = toast.querySelector('.toast-message');

    // Set icon based on type
    const icons = {
        success: '✓',
        error: '✗',
        warning: '⚠',
        info: 'ℹ'
    };

    toastIcon.textContent = icons[type] || icons.info;
    toastMessage.textContent = message;

    // Set class for styling
    toast.className = `toast ${type}`;
    toast.style.display = 'flex';

    // Auto-hide after 5 seconds
    setTimeout(() => {
        toast.style.display = 'none';
    }, 5000);
}

function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.add('show');
    }
}

function clearError(elementId) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = '';
        errorElement.classList.remove('show');
    }
}

function clearAllErrors() {
    const errorElements = document.querySelectorAll('.error-message');
    errorElements.forEach(el => {
        el.textContent = '';
        el.classList.remove('show');
    });
}

function validateEmail(email) {
    const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return re.test(email);
}

function validatePassword(password) {
    const requirements = {
        length: password.length >= 8,
        uppercase: /[A-Z]/.test(password),
        lowercase: /[a-z]/.test(password),
        number: /\d/.test(password),
        special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };

    const allMet = Object.values(requirements).every(req => req);

    return {
        valid: allMet,
        requirements: requirements
    };
}

function calculatePasswordStrength(password) {
    let score = 0;

    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[a-z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score++;

    if (score <= 2) return 'weak';
    if (score <= 4) return 'medium';
    return 'strong';
}

// ============================================================================
// LOGIN PAGE
// ============================================================================

function initializeLoginPage() {
    const loginForm = document.getElementById('login-form');
    const togglePassword = document.getElementById('toggle-password');
    const passwordInput = document.getElementById('password');

    // Toggle password visibility
    if (togglePassword) {
        togglePassword.addEventListener('click', () => {
            const type = passwordInput.type === 'password' ? 'text' : 'password';
            passwordInput.type = type;
            togglePassword.querySelector('.eye-icon').textContent = type === 'password' ? '👁️' : '👁️‍🗨️';
        });
    }

    // Handle login form submission
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            clearAllErrors();

            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            const loginBtn = document.getElementById('login-btn');

            // Validation
            if (!validateEmail(email)) {
                showError('email-error', 'Please enter a valid email address');
                return;
            }

            if (password.length < 8) {
                showError('password-error', 'Password must be at least 8 characters');
                return;
            }

            // Show loading state
            const btnText = loginBtn.querySelector('.btn-text');
            const btnLoader = loginBtn.querySelector('.btn-loader');
            btnText.style.display = 'none';
            btnLoader.style.display = 'flex';
            loginBtn.disabled = true;

            try {
                const response = await fetch(`${API_BASE_URL}/auth/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify({ email, password })
                });

                const data = await response.json();

                if (data.success) {
                    showToast('Login successful! Redirecting...', 'success');
                    setTimeout(() => {
                        window.location.href = 'index.html';
                    }, 1000);
                } else {
                    showToast(data.error || 'Login failed', 'error');
                    showError('password-error', data.error || 'Invalid credentials');
                }
            } catch (error) {
                console.error('Login error:', error);
                showToast('Network error. Please try again.', 'error');
            } finally {
                btnText.style.display = 'block';
                btnLoader.style.display = 'none';
                loginBtn.disabled = false;
            }
        });
    }

    // Fetch and display live prices
    fetchLivePrices();
    setInterval(fetchLivePrices, 60000); // Update every minute
}

async function fetchLivePrices() {
    try {
        const response = await fetch(`${API_BASE_URL}/preview/prices`);
        const data = await response.json();

        if (data.success && data.prices) {
            data.prices.forEach(crypto => {
                const priceElement = document.getElementById(`${crypto.name.toLowerCase()}-price`);
                if (priceElement) {
                    priceElement.textContent = `$${crypto.price_usd.toLocaleString()}`;
                }
            });
        }
    } catch (error) {
        console.error('Error fetching prices:', error);
    }
}

// ============================================================================
// SIGNUP PAGE
// ============================================================================

let currentStep = 1;
const totalSteps = 3;

function initializeSignupPage() {
    const signupForm = document.getElementById('signup-form');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    const togglePassword = document.getElementById('toggle-password');

    // Initialize step navigation
    initializeStepNavigation();

    // Toggle password visibility
    if (togglePassword) {
        togglePassword.addEventListener('click', () => {
            const type = passwordInput.type === 'password' ? 'text' : 'password';
            passwordInput.type = type;
            togglePassword.querySelector('.eye-icon').textContent = type === 'password' ? '👁️' : '👁️‍🗨️';
        });
    }

    // Password strength meter
    if (passwordInput) {
        passwordInput.addEventListener('input', () => {
            updatePasswordStrength(passwordInput.value);
            updatePasswordRequirements(passwordInput.value);
        });
    }

    // Handle signup form submission
    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Validate all fields
            if (!validateSignupForm()) {
                return;
            }

            const formData = {
                name: document.getElementById('name').value.trim(),
                email: document.getElementById('email').value.trim(),
                password: document.getElementById('password').value,
                phone: document.getElementById('phone').value.trim() || null,
                birth_date: document.getElementById('birth-date').value || null
            };

            const signupBtn = document.getElementById('signup-btn');
            const btnText = signupBtn.querySelector('.btn-text');
            const btnLoader = signupBtn.querySelector('.btn-loader');

            // Show loading state
            btnText.style.display = 'none';
            btnLoader.style.display = 'flex';
            signupBtn.disabled = true;

            try {
                const response = await fetch(`${API_BASE_URL}/auth/register`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify(formData)
                });

                const data = await response.json();

                if (data.success) {
                    showToast('Account created successfully! Redirecting...', 'success');
                    setTimeout(() => {
                        window.location.href = 'index.html';
                    }, 1500);
                } else {
                    showToast(data.error || 'Registration failed', 'error');

                    // Show specific field errors if available
                    if (data.details) {
                        data.details.forEach(error => {
                            showToast(error, 'error');
                        });
                    }
                }
            } catch (error) {
                console.error('Signup error:', error);
                showToast('Network error. Please try again.', 'error');
            } finally {
                btnText.style.display = 'block';
                btnLoader.style.display = 'none';
                signupBtn.disabled = false;
            }
        });
    }
}

function initializeStepNavigation() {
    const nextButtons = document.querySelectorAll('.next-btn');
    const prevButtons = document.querySelectorAll('.prev-btn');

    nextButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const nextStep = parseInt(btn.dataset.next);
            if (validateCurrentStep()) {
                goToStep(nextStep);
            }
        });
    });

    prevButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const prevStep = parseInt(btn.dataset.prev);
            goToStep(prevStep);
        });
    });
}

function goToStep(step) {
    // Hide all steps
    document.querySelectorAll('.form-step').forEach(s => {
        s.classList.remove('active');
    });

    // Show target step
    const targetStep = document.querySelector(`.form-step[data-step="${step}"]`);
    if (targetStep) {
        targetStep.classList.add('active');
    }

    // Update progress indicator
    document.querySelectorAll('.progress-step').forEach((s, index) => {
        s.classList.remove('active', 'completed');
        if (index + 1 < step) {
            s.classList.add('completed');
        } else if (index + 1 === step) {
            s.classList.add('active');
        }
    });

    // Update form header
    const titles = {
        1: 'Create Your Account',
        2: 'Secure Your Account',
        3: 'Complete Your Profile'
    };

    const subtitles = {
        1: "Let's get started with your basic information",
        2: 'Choose a strong password to protect your account',
        3: 'Add optional details to personalize your experience'
    };

    document.getElementById('form-title').textContent = titles[step];
    document.getElementById('form-subtitle').textContent = subtitles[step];

    currentStep = step;
}

function validateCurrentStep() {
    clearAllErrors();

    if (currentStep === 1) {
        const name = document.getElementById('name').value.trim();
        const email = document.getElementById('email').value.trim();

        if (name.length < 2) {
            showError('name-error', 'Name must be at least 2 characters');
            return false;
        }

        if (!validateEmail(email)) {
            showError('email-error', 'Please enter a valid email address');
            return false;
        }

        return true;
    }

    if (currentStep === 2) {
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm-password').value;

        const validation = validatePassword(password);

        if (!validation.valid) {
            showError('password-error', 'Password does not meet all requirements');
            return false;
        }

        if (password !== confirmPassword) {
            showError('confirm-password-error', 'Passwords do not match');
            return false;
        }

        return true;
    }

    return true;
}

function validateSignupForm() {
    clearAllErrors();

    // Validate step 1
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();

    if (name.length < 2) {
        goToStep(1);
        showError('name-error', 'Name must be at least 2 characters');
        return false;
    }

    if (!validateEmail(email)) {
        goToStep(1);
        showError('email-error', 'Please enter a valid email address');
        return false;
    }

    // Validate step 2
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    const validation = validatePassword(password);

    if (!validation.valid) {
        goToStep(2);
        showError('password-error', 'Password does not meet all requirements');
        return false;
    }

    if (password !== confirmPassword) {
        goToStep(2);
        showError('confirm-password-error', 'Passwords do not match');
        return false;
    }

    // Validate step 3
    const phone = document.getElementById('phone').value.trim();
    if (phone && !/^\+?\d{10,15}$/.test(phone)) {
        showError('phone-error', 'Invalid phone number format');
        return false;
    }

    const terms = document.getElementById('terms');
    if (!terms.checked) {
        showError('terms-error', 'You must agree to the Terms of Service');
        return false;
    }

    return true;
}

function updatePasswordStrength(password) {
    const strengthFill = document.getElementById('strength-fill');
    const strengthText = document.getElementById('strength-text');

    if (!strengthFill || !strengthText) return;

    if (password.length === 0) {
        strengthFill.className = 'strength-fill';
        strengthText.textContent = 'Enter password';
        strengthText.className = 'strength-text';
        return;
    }

    const strength = calculatePasswordStrength(password);

    strengthFill.className = `strength-fill ${strength}`;
    strengthText.className = `strength-text ${strength}`;

    const strengthLabels = {
        weak: 'Weak',
        medium: 'Medium',
        strong: 'Strong'
    };

    strengthText.textContent = strengthLabels[strength];
}

function updatePasswordRequirements(password) {
    const validation = validatePassword(password);

    const requirements = {
        'req-length': validation.requirements.length,
        'req-uppercase': validation.requirements.uppercase,
        'req-lowercase': validation.requirements.lowercase,
        'req-number': validation.requirements.number,
        'req-special': validation.requirements.special
    };

    Object.entries(requirements).forEach(([id, met]) => {
        const element = document.getElementById(id);
        if (element) {
            if (met) {
                element.classList.add('met');
            } else {
                element.classList.remove('met');
            }
        }
    });
}

// ============================================================================
// EXPORT FUNCTIONS
// ============================================================================

window.initializeLoginPage = initializeLoginPage;
window.initializeSignupPage = initializeSignupPage;
window.showToast = showToast;
