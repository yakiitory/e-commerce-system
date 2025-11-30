document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('file-input');
    const uploadArea = document.getElementById('upload-area');
    const browseBtn = document.querySelector('.browse-btn');
    const imagePreviewGrid = document.getElementById('image-preview-grid');
    const productForm = document.getElementById('product-form');
    const imagesHiddenInput = document.getElementById('images');

    let uploadedFiles = [];

    // --- Load existing images ---
    function loadInitialImages() {
        const existingImageUrls = imagesHiddenInput.value ? imagesHiddenInput.value.split(',') : [];
        uploadedFiles = existingImageUrls.map(url => ({
            id: Date.now() + Math.random(),
            url: url,
            name: url.split('/').pop() // Extract filename from URL
        }));
        renderPreviews();
    }

    // Trigger file input when browse button is clicked
    browseBtn.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('click', () => fileInput.click());

    // Drag and drop events
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.parentElement.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.parentElement.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.parentElement.classList.remove('dragover');
        const files = e.dataTransfer.files;
        handleFiles(files);
    });

    // Handle file selection from input
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    function handleFiles(files) {
        for (const file of files) {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const fileData = {
                        id: Date.now() + Math.random(),
                        url: e.target.result,
                        name: file.name,
                        isNewUpload: true // Mark as new upload
                    };
                    uploadedFiles.push(fileData);
                    renderPreviews();
                };
                reader.readAsDataURL(file);
            }
        }
    }

    function renderPreviews() {
        imagePreviewGrid.innerHTML = '';
        uploadedFiles.forEach((fileData, index) => {
            const card = document.createElement('div');
            card.classList.add('preview-card');
            if (index === 0) {
                card.classList.add('main-image');
            }

            const img = document.createElement('img');
            img.src = fileData.url;
            card.appendChild(img);

            const overlay = document.createElement('div');
            overlay.classList.add('image-overlay');

            if (index !== 0) {
                const makeMainBtn = document.createElement('button');
                makeMainBtn.type = 'button';
                makeMainBtn.classList.add('overlay-btn');
                makeMainBtn.textContent = 'Make Main';
                makeMainBtn.onclick = () => setAsMain(index);
                overlay.appendChild(makeMainBtn);
            } else {
                const mainBadge = document.createElement('div');
                mainBadge.classList.add('main-image-badge');
                mainBadge.textContent = 'MAIN';
                card.appendChild(mainBadge);
            }

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.classList.add('overlay-btn');
            removeBtn.textContent = 'Remove';
            removeBtn.onclick = () => removeImage(index);
            overlay.appendChild(removeBtn);

            card.appendChild(overlay);
            imagePreviewGrid.appendChild(card);
        });
    }

    function setAsMain(index) {
        const [mainImage] = uploadedFiles.splice(index, 1);
        uploadedFiles.unshift(mainImage);
        renderPreviews();
    }

    function removeImage(index) {
        uploadedFiles.splice(index, 1);
        renderPreviews();
    }

    productForm.addEventListener('submit', () => {
        // Get all existing images (non-data URLs) - these are already ordered correctly
        const existingImageUrls = uploadedFiles
            .filter(file => !file.url.startsWith('data:'))
            .map(file => file.url);
        
        // Update the hidden input with the reordered existing images
        imagesHiddenInput.value = existingImageUrls.join(',');
        
        
        // Create a new DataTransfer to reorder files
        const dt = new DataTransfer();
        const newFiles = uploadedFiles.filter(file => file.url.startsWith('data:'));
        
    });

    loadInitialImages();
});