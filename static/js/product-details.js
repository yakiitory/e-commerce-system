document.addEventListener('DOMContentLoaded', function () {
    const mainImage = document.getElementById('main-product-image');
    const thumbnails = document.querySelectorAll('.thumbnail-image');

    thumbnails.forEach(thumbnail => {
        thumbnail.addEventListener('click', function () {
            mainImage.src = this.src;


            thumbnails.forEach(thumb => thumb.classList.remove('active-thumbnail'));
            this.classList.add('active-thumbnail');
        });
    });

    if (thumbnails.length > 0) {
        thumbnails[0].classList.add('active-thumbnail');
    }

    const stars = document.querySelectorAll('.star-rating-input .star');
    const ratingInput = document.getElementById('rating-value');
    const starFilled = document.getElementById('star-filled-template').innerHTML;
    const starNofill = document.getElementById('star-nofill-template').innerHTML;

    stars.forEach(star => {
        star.addEventListener('click', function () {
            const value = this.getAttribute('data-value');
            ratingInput.value = value;
            stars.forEach((s, index) => {
                s.innerHTML = index < value ? starFilled : starNofill;
            });
        });
    });
});