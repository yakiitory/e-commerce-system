document.addEventListener('DOMContentLoaded', () => {
    const categoryItems = document.querySelectorAll('.sidebar .has-submenu');

    categoryItems.forEach(item => {
        const categoryItemDiv = item.querySelector('.category-item');
        const submenu = item.querySelector('.submenu');

        categoryItemDiv.addEventListener('click', (e) => {
            e.preventDefault(); // Prevents navigation when clicking the toggle area
            categoryItemDiv.classList.toggle('active');
            submenu.classList.toggle('active');
        });
    });
});
