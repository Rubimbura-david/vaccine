document.addEventListener('DOMContentLoaded', function() {
    const contactForm = document.getElementById('contactForm');
    const errorAlert = document.getElementById('errorAlert');
    
    contactForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Simple validation
        const fullName = document.getElementById('fullName').value;
        const email = document.getElementById('email').value;
        const subject = document.getElementById('subject').value;
        const message = document.getElementById('message').value;
        
        if (!fullName || !email || !subject || !message) {
            errorAlert.style.display = 'block';
            return;
        }
        
        // If validation passes, show success message
        errorAlert.style.display = 'none';
        alert('Message sent successfully!');
        contactForm.reset();
    });
});