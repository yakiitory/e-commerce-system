document.addEventListener('DOMContentLoaded', () => {
    const priceDropdown = document.querySelector('.price-dropdown-container');
    if (priceDropdown) {
        const trigger = priceDropdown.querySelector('.price-dropdown-trigger');
        
        trigger.addEventListener('click', (event) => {
            event.stopPropagation(); 
            priceDropdown.classList.toggle('active');
        });

        window.addEventListener('click', () => {
            priceDropdown.classList.remove('active');
        });
    }

    // Sidebar Search Suggestions
    const searchContainer = document.getElementById('sidebarSearchContainer');
    const searchInput = document.getElementById('sidebarSearchInput');
    const suggestionsContainer = document.getElementById('sidebarSuggestions');
    let debounceTimer;

    if (searchContainer && searchInput && suggestionsContainer) {
        searchInput.addEventListener('input', function() {
            const query = this.value;

            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                if (query.length < 2) {
                    suggestionsContainer.innerHTML = '';
                    suggestionsContainer.style.display = 'none';
                    return;
                }

                fetch(`/api/search-suggestions?query=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        suggestionsContainer.innerHTML = '';
                        if (data.length > 0) {
                            suggestionsContainer.style.display = 'block';
                            data.forEach(suggestion => {
                                const item = document.createElement('div');
                                item.className = 'suggestion-item';
                                item.textContent = suggestion;
                                item.addEventListener('click', () => {
                                    searchInput.value = suggestion;
                                    searchInput.closest('form').submit();
                                });
                                suggestionsContainer.appendChild(item);
                            });
                        } else {
                            suggestionsContainer.style.display = 'none';
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching search suggestions:', error);
                        suggestionsContainer.style.display = 'none';
                    });
            }, 250);
        });

        // Hide suggestions when clicking outside
        document.addEventListener('click', function(event) {
            if (!searchContainer.contains(event.target)) {
                suggestionsContainer.style.display = 'none';
            }
        });
    }
});
