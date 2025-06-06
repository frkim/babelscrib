document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, starting script');

    const fileDrop = document.getElementById('file-drop');
    const fileInput = document.getElementById('file-input');
    const selectFileButton = document.getElementById('select-file-button');
    const uploadForm = document.getElementById('upload-form');
    const uploadStatus = document.getElementById('upload-status');

    // Debug: Check if elements are found
    console.log('fileDrop:', fileDrop);
    console.log('fileInput:', fileInput);
    console.log('selectFileButton:', selectFileButton);

    if (!fileDrop || !fileInput || !selectFileButton) {
        console.error('Some elements not found!');
        return;
    }

    // Simple function to open file dialog
    function openFileDialog() {
        console.log('Opening file dialog...');
        try {
            fileInput.click();
            console.log('fileInput.click() executed successfully');
        } catch (error) {
            console.error('Error calling fileInput.click():', error);
        }
    }

    // Show file dialog when select button is clicked
    selectFileButton.addEventListener('click', function(e) {
        console.log('Select Document button clicked');
        e.preventDefault();
        e.stopPropagation();
        openFileDialog();
    });

    // Also allow clicking the drop area to open file dialog
    fileDrop.addEventListener('click', function(e) {
        console.log('Drop area clicked');
        e.preventDefault();
        e.stopPropagation();
        openFileDialog();
    });

    // When a file is selected, update the drop area and prepare for upload
    fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0) {
            fileDrop.textContent = fileInput.files[0].name;
        }
    });

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileDrop.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        fileDrop.addEventListener(eventName, highlight, false);
    });

    // Remove highlight when item is dragged away
    ['dragleave', 'drop'].forEach(eventName => {
        fileDrop.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    fileDrop.addEventListener('drop', handleDrop, false);

    // Handle form submit
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        if (fileInput.files.length > 0) {
            uploadFile(fileInput.files[0]);
        } else {
            uploadStatus.textContent = 'Please select a file first.';
        }
    });


    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }


    function highlight() {
        fileDrop.classList.add('highlight');
    }


    function unhighlight() {
        fileDrop.classList.remove('highlight');
    }


    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            // Create a DataTransfer to set fileInput.files (not fully supported in all browsers)
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(files[0]);
            fileInput.files = dataTransfer.files;
            fileDrop.textContent = files[0].name;
        }
    }


    function uploadFile(file) {
        const url = '/upload/';
        const formData = new FormData();
        formData.append('file', file);

        fetch(url, {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (response.ok) {
                uploadStatus.textContent = 'Upload successful!';
            } else {
                uploadStatus.textContent = 'Upload failed.';
            }
        })
        .catch(() => {
            uploadStatus.textContent = 'Upload failed.';
        });
    }
});