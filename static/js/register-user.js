document.addEventListener('DOMContentLoaded', function() {

        const customSelects = document.querySelectorAll('.select-container');

        customSelects.forEach(selectContainer => {
            const trigger = selectContainer.querySelector('.select-trigger');
            const triggerText = selectContainer.querySelector('.trigger-text');
            const options = selectContainer.querySelectorAll('.select-options li');
            const hiddenInput = selectContainer.querySelector('input[type="hidden"]');
            const defaultText = triggerText.textContent;

            trigger.addEventListener('click', (e) => {
                 e.stopPropagation(); 
                 closeAllSelects(selectContainer);
                 selectContainer.classList.toggle('active');
            });

            options.forEach(option => {
                option.addEventListener('click', () => {
                    triggerText.textContent = option.textContent;
                    selectContainer.classList.add('has-value');
                    if(hiddenInput) {
                        hiddenInput.value = option.getAttribute('data-value');
                    }
                    selectContainer.classList.remove('active');
                });
            });
        });

        function closeAllSelects(exceptThisOne = null) {
            customSelects.forEach(select => {
                if (select !== exceptThisOne) {
                    select.classList.remove('active');
                }
            });
        }

        document.addEventListener('click', () => {
            closeAllSelects();
        });
    });