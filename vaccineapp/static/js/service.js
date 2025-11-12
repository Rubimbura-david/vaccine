document.addEventListener('DOMContentLoaded', function() {
    // Symptom Form Handling
    const symptomForm = document.getElementById('symptomForm');
    if (symptomForm) {
        symptomForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const patientName = document.getElementById('patientName').value;
            const patientAge = document.getElementById('patientAge').value;
            const symptomDuration = document.getElementById('symptomDuration').value;
            
            // Get checked symptoms
            const checkedSymptoms = [];
            document.querySelectorAll('.symptoms-checklist input:checked').forEach(checkbox => {
                checkedSymptoms.push(checkbox.value);
            });
            
            if (checkedSymptoms.length === 0) {
                alert('Please select at least one symptom.');
                return;
            }
            
            // Show success message
            alert(`Thank you, ${patientName}. Your symptoms have been reported. Our medical team will contact you within 2 hours.`);
            symptomForm.reset();
        });
    }

    // Consultation Form Handling
    const consultationForm = document.getElementById('consultationForm');
    if (consultationForm) {
        consultationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const patientName = document.getElementById('consultPatientName').value;
            const reason = document.getElementById('consultReason').value;
            const urgency = document.getElementById('urgencyLevel').value;
            
            // Determine response time based on urgency
            let responseTime = '';
            switch(urgency) {
                case 'emergency':
                    responseTime = 'immediately';
                    break;
                case 'urgent':
                    responseTime = 'within 2 hours';
                    break;
                case 'soon':
                    responseTime = 'within 24 hours';
                    break;
                default:
                    responseTime = 'within 3 business days';
            }
            
            alert(`Thank you, ${patientName}. Your consultation request has been submitted. We will contact you ${responseTime} to schedule your appointment.`);
            consultationForm.reset();
        });
    }

    // Schedule Follow-up Button
    const scheduleFollowupBtn = document.getElementById('scheduleFollowup');
    if (scheduleFollowupBtn) {
        scheduleFollowupBtn.addEventListener('click', function() {
            alert('Redirecting to consultation scheduling...');
            document.getElementById('consultReason').value = 'followup';
            document.getElementById('consultationForm').scrollIntoView({ behavior: 'smooth' });
        });
    }

    // Emergency Call Button
    document.querySelector('.btn-danger')?.addEventListener('click', function() {
        if (confirm('Call emergency services? This will dial our emergency hotline.')) {
            window.location.href = 'tel:+1-800-HEALTH';
        }
    });

    // Smooth scrolling for navigation
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Navbar background change on scroll
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.navbar');
        if (window.scrollY > 100) {
            navbar.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
            navbar.style.backdropFilter = 'blur(10px)';
        } else {
            navbar.style.backgroundColor = 'white';
            navbar.style.backdropFilter = 'none';
        }
    });
});