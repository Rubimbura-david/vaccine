document.addEventListener('DOMContentLoaded', function() {
    // Initialize Charts
    initializeCharts();
    
    // Initialize sidebar toggle for mobile
    initializeMobileSidebar();
    
    // Initialize real-time updates
    initializeRealTimeUpdates();
});

function initializeCharts() {
    // Patient Visits Chart
    const visitsCtx = document.getElementById('visitsChart').getContext('2d');
    const visitsChart = new Chart(visitsCtx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            datasets: [{
                label: 'Patient Visits',
                data: [65, 59, 80, 81, 56, 55, 70, 75, 82, 78, 85, 90],
                borderColor: '#4caf50',
                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            }, {
                label: 'Vaccinations',
                data: [28, 48, 40, 45, 36, 52, 45, 50, 55, 60, 58, 65],
                borderColor: '#2196f3',
                backgroundColor: 'rgba(33, 150, 243, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        drawBorder: false
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });

    // Vaccination Status Chart
    const vaccinationCtx = document.getElementById('vaccinationChart').getContext('2d');
    const vaccinationChart = new Chart(vaccinationCtx, {
        type: 'doughnut',
        data: {
            labels: ['Completed', 'Scheduled', 'Overdue', 'Pending'],
            datasets: [{
                data: [65, 20, 8, 7],
                backgroundColor: [
                    '#4caf50',
                    '#2196f3',
                    '#ff9800',
                    '#f44336'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    // Age Distribution Chart
    const ageCtx = document.getElementById('ageChart').getContext('2d');
    const ageChart = new Chart(ageCtx, {
        type: 'bar',
        data: {
            labels: ['0-2', '3-5', '6-12', '13-17', '18+'],
            datasets: [{
                label: 'Patients',
                data: [120, 180, 220, 150, 80],
                backgroundColor: [
                    'rgba(76, 175, 80, 0.8)',
                    'rgba(33, 150, 243, 0.8)',
                    'rgba(255, 152, 0, 0.8)',
                    'rgba(156, 39, 176, 0.8)',
                    'rgba(244, 67, 54, 0.8)'
                ],
                borderWidth: 0,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        drawBorder: false
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function initializeMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggleButton = document.createElement('button');
    toggleButton.className = 'btn btn-primary d-md-none position-fixed';
    toggleButton.style.cssText = 'bottom: 20px; right: 20px; z-index: 1050; width: 50px; height: 50px; border-radius: 50%;';
    toggleButton.innerHTML = '<i class="fas fa-bars"></i>';
    
    toggleButton.addEventListener('click', function() {
        sidebar.classList.toggle('show');
    });
    
    document.body.appendChild(toggleButton);
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        if (window.innerWidth < 768 && !sidebar.contains(event.target) && !toggleButton.contains(event.target)) {
            sidebar.classList.remove('show');
        }
    });
}

function initializeRealTimeUpdates() {
    // Simulate real-time updates
    setInterval(updateDashboardStats, 30000);
    
    // Initial update
    updateDashboardStats();
}

function updateDashboardStats() {
    // Simulate updating stats with random data
    const stats = {
        patients: Math.floor(1247 + Math.random() * 10),
        appointments: Math.floor(18 + Math.random() * 5),
        vaccinations: Math.floor(24 + Math.random() * 3),
        consultations: Math.floor(12 + Math.random() * 4)
    };
    
    // Update the numbers with animation
    animateValue('stat-card:nth-child(1) .card-number', stats.patients);
    animateValue('stat-card:nth-child(2) .card-number', stats.appointments);
    animateValue('stat-card:nth-child(3) .card-number', stats.vaccinations);
    animateValue('stat-card:nth-child(4) .card-number', stats.consultations);
}

function animateValue(selector, newValue) {
    const element = document.querySelector(selector);
    if (!element) return;
    
    const currentValue = parseInt(element.textContent.replace(/,/g, ''));
    const duration = 1000;
    const startTime = performance.now();
    
    function updateValue(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        
        const value = Math.floor(currentValue + (newValue - currentValue) * easeOutQuart);
        element.textContent = value.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(updateValue);
        }
    }
    
    requestAnimationFrame(updateValue);
}

// Export functionality
document.querySelector('.btn-primary[class*="download"]')?.addEventListener('click', function() {
    // Simulate export functionality
    const toast = document.createElement('div');
    toast.className = 'alert alert-success position-fixed';
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 1060;';
    toast.innerHTML = '<i class="fas fa-check me-2"></i>Report exported successfully!';
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
});

// Appointment action buttons
document.querySelectorAll('.appointment-actions .btn').forEach(button => {
    button.addEventListener('click', function() {
        const appointmentText = this.closest('.appointment-item').querySelector('h6').textContent;
        const action = this.textContent.trim();
        
        // Simulate action
        const toast = document.createElement('div');
        toast.className = 'alert alert-info position-fixed';
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 1060;';
        toast.innerHTML = `<i class="fas fa-info-circle me-2"></i>${action}ing appointment with ${appointmentText}`;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    });
});
// Add real-time stock level calculation
document.addEventListener('DOMContentLoaded', function() {
    const currentStockInput = document.getElementById('current_stock');
    const minStockInput = document.getElementById('min_stock_level');
    const stockAlert = document.getElementById('stockAlert');
    
    function updateStockIndicator() {
        const currentStock = parseInt(currentStockInput.value) || 0;
        const minStock = parseInt(minStockInput.value) || 1;
        
        let message = '';
        let alertClass = '';
        
        if (currentStock === 0) {
            message = 'Out of Stock';
            alertClass = 'danger';
        } else if (currentStock <= minStock * 0.2) {
            message = 'Critical Stock';
            alertClass = 'danger';
        } else if (currentStock <= minStock * 0.5) {
            message = 'Low Stock';
            alertClass = 'warning';
        } else if (currentStock <= minStock) {
            message = 'Approaching Minimum';
            alertClass = 'info';
        } else {
            message = 'Good Stock';
            alertClass = 'success';
        }
        
        stockAlert.className = `alert alert-${alertClass} mt-3`;
        stockAlert.innerHTML = `<strong>Stock Status:</strong> ${message} (${currentStock} / ${minStock} doses)`;
    }
    
    // Add event listeners
    if (currentStockInput && minStockInput && stockAlert) {
        currentStockInput.addEventListener('input', updateStockIndicator);
        minStockInput.addEventListener('input', updateStockIndicator);
        
        // Initial calculation
        updateStockIndicator();
    }
    
    // Filter functionality
    const filterButtons = document.querySelectorAll('[data-filter]');
    const vaccineRows = document.querySelectorAll('.vaccine-row');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filter = this.getAttribute('data-filter');
            
            // Update active button
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Filter rows
            vaccineRows.forEach(row => {
                const status = row.getAttribute('data-status');
                const expiry = row.getAttribute('data-expiry');
                const today = new Date().toISOString().split('T')[0];
                const thirtyDaysLater = new Date();
                thirtyDaysLater.setDate(thirtyDaysLater.getDate() + 30);
                const expiryDate = thirtyDaysLater.toISOString().split('T')[0];
                
                let showRow = true;
                
                if (filter === 'low_stock') {
                    showRow = status === 'low_stock' || status === 'critical';
                } else if (filter === 'expiring_soon') {
                    showRow = expiry <= expiryDate;
                }
                // 'all' filter shows all rows
                
                row.style.display = showRow ? '' : 'none';
            });
        });
    });
    
    // Search functionality
    const searchInput = document.getElementById('vaccineSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            
            vaccineRows.forEach(row => {
                const vaccineName = row.querySelector('td:first-child strong').textContent.toLowerCase();
                row.style.display = vaccineName.includes(searchTerm) ? '' : 'none';
            });
        });
    }
});