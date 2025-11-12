document.addEventListener('DOMContentLoaded', function() {
    // Vaccine Filter Functionality
    const vaccineTypeFilter = document.getElementById('vaccineType');
    const ageGroupFilter = document.getElementById('ageGroup');
    const searchInput = document.getElementById('searchVaccine');
    const filterBtn = document.getElementById('filterBtn');
    const resetBtn = document.getElementById('resetBtn');
    const vaccineCards = document.querySelectorAll('.vaccine-card');
    const vaccineCategories = document.querySelectorAll('.vaccine-category');

    function filterVaccines() {
        const selectedType = vaccineTypeFilter.value;
        const selectedAge = ageGroupFilter.value;
        const searchTerm = searchInput.value.toLowerCase();

        vaccineCards.forEach(card => {
            const vaccineType = card.closest('.vaccine-category').dataset.category;
            const ageGroups = card.dataset.age;
            const vaccineName = card.dataset.name;

            const typeMatch = selectedType === 'all' || vaccineType === selectedType;
            const ageMatch = selectedAge === 'all' || ageGroups.includes(selectedAge);
            const searchMatch = searchTerm === '' || vaccineName.includes(searchTerm);

            if (typeMatch && ageMatch && searchMatch) {
                card.style.display = 'block';
                card.closest('.vaccine-category').style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });

        // Hide empty categories
        vaccineCategories.forEach(category => {
            const visibleCards = category.querySelectorAll('.vaccine-card[style="display: block"]');
            if (visibleCards.length === 0) {
                category.style.display = 'none';
            } else {
                category.style.display = 'block';
            }
        });
    }

    filterBtn.addEventListener('click', filterVaccines);

    resetBtn.addEventListener('click', function() {
        vaccineTypeFilter.value = 'all';
        ageGroupFilter.value = 'all';
        searchInput.value = '';
        filterVaccines();
    });

    searchInput.addEventListener('keyup', filterVaccines);

    // Schedule vaccination buttons
    const scheduleButtons = document.querySelectorAll('.schedule-btn');
    scheduleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const vaccineName = this.closest('.vaccine-card').querySelector('h4').textContent;
            alert(`Redirecting to schedule ${vaccineName} vaccination...`);
            // In a real application, this would redirect to a scheduling page
            window.location.href = 'index.html#contact';
        });
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