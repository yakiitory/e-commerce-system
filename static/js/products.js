document.addEventListener('DOMContentLoaded', () => {
    const priceDropdown = document.querySelector('.price-dropdown-container');
    if (priceDropdown) {
        const trigger = priceDropdown.querySelector('.price-dropdown-trigger');
        
        trigger.addEventListener('click', (event) => {
            event.stopPropagation(); // Prevents the window click listener from firing immediately
            priceDropdown.classList.toggle('active');
        });

        window.addEventListener('click', () => {
            priceDropdown.classList.remove('active');
        });
    }
});
