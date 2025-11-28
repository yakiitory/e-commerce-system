document.addEventListener('DOMContentLoaded', function () {
    const stars = document.querySelectorAll('.star-rating-input .star');
    const ratingInput = document.getElementById('rating-value');

    const starFilledSVG = document.getElementById('star-filled-template')?.innerHTML;
    const starNofillSVG = document.getElementById('star-nofill-template')?.innerHTML;

    stars.forEach(star => {
        star.addEventListener('click', function () {
            const value = this.getAttribute('data-value');
            ratingInput.value = value;
            updateStars(value);
        });

        star.addEventListener('mouseover', function () {
            const value = this.getAttribute('data-value');
            updateStars(value, true);
        });

        star.addEventListener('mouseout', function () {
            updateStars(ratingInput.value);
        });
    });

    function updateStars(value, isHover = false) {
        stars.forEach(star => {
            if (!starFilledSVG || !starNofillSVG) return;

            const starValue = star.getAttribute('data-value');
            star.innerHTML = starValue <= value ? starFilledSVG : starNofillSVG;
        });
    }
});