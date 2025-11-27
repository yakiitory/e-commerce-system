document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('address-modal');
    const form = document.getElementById('address-form');
    const modalTitle = document.getElementById('modal-title');

    window.openAddModal = function () {
        form.reset();
        form.action = '/add-address';
        modalTitle.textContent = 'Add New Address';
        modal.style.display = 'block';
    };

    window.openEditModal = function (address) {
        form.reset();
        form.action = `/edit-address/${address.id}`;
        modalTitle.textContent = 'Edit Address';

        form.querySelector('[name="house_no"]').value = address.house_no;
        form.querySelector('[name="street"]').value = address.street;
        form.querySelector('[name="city"]').value = address.city;
        form.querySelector('[name="postal_code"]').value = address.postal_code;
        form.querySelector('[name="additional_notes"]').value = address.additional_notes || '';

        modal.style.display = 'block';
    };

    window.closeModal = function () {
        modal.style.display = 'none';
    };

    // Close modal if user clicks outside of it
    window.onclick = function (event) {
        if (event.target == modal) {
            closeModal();
        }
    };
});
