// Authentication page functionality
document.addEventListener('DOMContentLoaded', function() {
    // Password strength indicator (for signup page)
    const passwordInput = document.getElementById('id_password1');
    const confirmPasswordInput = document.getElementById('id_password2');
    
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            checkPasswordStrength(this.value);
        });
    }
    
    if (passwordInput && confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            checkPasswordMatch();
        });
    }
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

function checkPasswordStrength(password) {
    const strengthIndicator = document.getElementById('password-strength');
    if (!strengthIndicator) return;
    
    let strength = 0;
    let feedback = '';
    
    if (password.length >= 8) strength++;
    if (password.match(/[a-z]/) && password.match(/[A-Z]/)) strength++;
    if (password.match(/\d/)) strength++;
    if (password.match(/[^a-zA-Z\d]/)) strength++;
    
    switch(strength) {
        case 0:
        case 1:
            feedback = 'Weak';
            strengthIndicator.className = 'password-strength weak';
            break;
        case 2:
            feedback = 'Fair';
            strengthIndicator.className = 'password-strength fair';
            break;
        case 3:
            feedback = 'Good';
            strengthIndicator.className = 'password-strength good';
            break;
        case 4:
            feedback = 'Strong';
            strengthIndicator.className = 'password-strength strong';
            break;
    }
    
    strengthIndicator.textContent = feedback;
}

function checkPasswordMatch() {
    const password = document.getElementById('id_password1').value;
    const confirmPassword = document.getElementById('id_password2').value;
    const matchIndicator = document.getElementById('password-match');
    
    if (!matchIndicator) return;
    
    if (confirmPassword === '') {
        matchIndicator.textContent = '';
        matchIndicator.className = 'password-match';
    } else if (password === confirmPassword) {
        matchIndicator.textContent = 'Passwords match';
        matchIndicator.className = 'password-match match';
    } else {
        matchIndicator.textContent = 'Passwords do not match';
        matchIndicator.className = 'password-match no-match';
    }
}

// Form submission enhancement
document.querySelectorAll('.auth-form').forEach(form => {
    form.addEventListener('submit', function(e) {
        const submitBtn = this.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
        }
    });
});