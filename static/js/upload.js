document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, starting script');

    const fileDrop = document.getElementById('file-drop');
    const fileInput = document.getElementById('file-input');
    const selectFileButton = document.getElementById('select-file-button');
    const uploadForm = document.getElementById('upload-form');
    const uploadStatus = document.getElementById('upload-status');
    const emailInput = document.getElementById('email-input');
    const uploadButton = document.getElementById('upload-button');
    const emailError = document.getElementById('email-error');

    // Debug: Check if elements are found
    console.log('fileDrop:', fileDrop);
    console.log('fileInput:', fileInput);
    console.log('selectFileButton:', selectFileButton);
    console.log('emailInput:', emailInput);
    console.log('uploadButton:', uploadButton);

    if (!fileDrop || !fileInput || !selectFileButton || !emailInput || !uploadButton) {
        console.error('Some elements not found!');
        return;
    }

    // Cookie utility functions
    function setCookie(name, value, days) {
        let expires = "";
        if (days) {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = "; expires=" + date.toUTCString();
        }
        document.cookie = name + "=" + encodeURIComponent(value) + expires + "; path=/; SameSite=Lax";
    }

    function getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for(let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return decodeURIComponent(c.substring(nameEQ.length, c.length));
        } 
        return null;
    }

    // Load saved email on page load
    function loadSavedEmail() {
        const savedEmail = getCookie('userEmail');
        if (savedEmail && isValidEmail(savedEmail)) {
            emailInput.value = savedEmail;
            validateEmailAndUpdateButton();
            console.log('Loaded saved email:', savedEmail);
        }
    }

    // Save email to cookie when valid
    function saveEmailToCookie(email) {
        if (email && isValidEmail(email)) {
            setCookie('userEmail', email, 30); // Save for 30 days
            console.log('Saved email to cookie:', email);
        }
    }

    // Load saved email when page loads
    loadSavedEmail();

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

    // Event delegation for file remove buttons (this must come first!)
    fileDrop.addEventListener('click', function(e) {
        const removeButton = e.target.closest('.file-remove');
        if (removeButton) {
            e.preventDefault();
            e.stopPropagation();
            const index = parseInt(removeButton.getAttribute('data-file-index'));
            removeFileByIndex(index);
            return; // Exit early to prevent file dialog
        }
        
        // Only open file dialog if we didn't click on a remove button
        console.log('Drop area clicked');
        e.preventDefault();
        e.stopPropagation();
        openFileDialog();
    });

    // When files are selected, update the drop area and prepare for upload
    fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0) {
            updateFileDisplay(fileInput.files);
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

    // Email validation
    emailInput.addEventListener('input', validateEmailAndUpdateButton);
    emailInput.addEventListener('blur', validateEmailAndUpdateButton);

    // Handle form submit
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        if (!isValidEmail(emailInput.value)) {
            showEmailError('Please enter a valid email address');
            return;
        }
        if (fileInput.files.length > 0) {
            uploadMultipleFiles(Array.from(fileInput.files));
        } else {
            uploadStatus.textContent = 'Please select files first.';
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
            // Create a DataTransfer to set fileInput.files
            const dataTransfer = new DataTransfer();
            Array.from(files).forEach(file => {
                dataTransfer.items.add(file);
            });
            fileInput.files = dataTransfer.files;
            updateFileDisplay(files);
        }
    }


    function updateFileDisplay(files) {
        if (files.length === 0) {
            // Reset to original state
            fileDrop.innerHTML = `
                <div style="display: flex; justify-content: center; gap: 18px; margin-bottom: 18px;">
                    <!-- PDF Icon -->
                    <svg width="38" height="54" viewBox="0 0 48 62" fill="none">
                        <rect width="48" height="62" rx="8" fill="#E53935"/>
                        <text x="24" y="44" text-anchor="middle" font-size="14" font-family="Arial" fill="#fff" font-weight="bold">.pdf</text>
                    </svg>
                    <!-- DOCX Icon -->
                    <svg width="38" height="54" viewBox="0 0 48 62" fill="none">
                        <rect width="48" height="62" rx="8" fill="#1976D2"/>
                        <text x="24" y="44" text-anchor="middle" font-size="14" font-family="Arial" fill="#fff" font-weight="bold">.docx</text>
                    </svg>
                    <!-- PPTX Icon -->
                    <svg width="38" height="54" viewBox="0 0 48 62" fill="none">
                        <rect width="48" height="62" rx="8" fill="#FF7043"/>
                        <text x="24" y="44" text-anchor="middle" font-size="14" font-family="Arial" fill="#fff" font-weight="bold">.pptx</text>
                    </svg>
                    <!-- TXT Icon -->
                    <svg width="38" height="54" viewBox="0 0 48 62" fill="none">
                        <rect width="48" height="62" rx="8" fill="#616161"/>
                        <text x="24" y="44" text-anchor="middle" font-size="14" font-family="Arial" fill="#fff" font-weight="bold">.txt</text>
                    </svg>
                    <!-- MD Icon -->
                    <svg width="38" height="54" viewBox="0 0 48 62" fill="none">
                        <rect width="48" height="62" rx="8" fill="#43A047"/>
                        <text x="24" y="44" text-anchor="middle" font-size="14" font-family="Arial" fill="#fff" font-weight="bold">...</text>
                    </svg>
                </div>
                <p>Click here to select files or drag and drop your files here</p>
                <p><small>Supported formats: pdf, doc, docx, txt, pptx, md</small></p>
            `;
            return;
        }

        // Create file list display
        let html = '<p><strong>Selected ' + files.length + ' file(s):</strong></p>';
        html += '<div class="file-list">';
        
        Array.from(files).forEach((file, index) => {
            const extension = getFileExtension(file.name);
            const fileType = getFileTypeClass(extension);
            const icon = getFileIcon(extension);
            
            html += `
                <div class="file-row ${fileType}">
                    <div class="file-icon">${icon}</div>
                    <div class="file-name">${file.name}</div>
                    <div class="file-remove" data-file-index="${index}" title="Remove file">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3,6 5,6 21,6"></polyline>
                            <path d="m19,6v14a2,2 0 0,1 -2,2H7a2,2 0 0,1 -2,-2V6m3,0V4a2,2 0 0,1 2,-2h4a2,2 0 0,1 2,2v2"></path>
                            <line x1="10" y1="11" x2="10" y2="17"></line>
                            <line x1="14" y1="11" x2="14" y2="17"></line>
                        </svg>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        html += '<p><small>Click to select different files</small></p>';
        
        fileDrop.innerHTML = html;
    }

    function getFileExtension(filename) {
        return filename.split('.').pop().toLowerCase();
    }

    function getFileTypeClass(extension) {
        switch(extension) {
            case 'pdf': return 'pdf';
            case 'doc':
            case 'docx': return 'docx';
            case 'ppt':
            case 'pptx': return 'pptx';
            case 'txt': return 'txt';
            default: return 'other';
        }
    }

    function getFileIcon(extension) {
        switch(extension) {
            case 'pdf':
                return `<svg width="24" height="32" viewBox="0 0 48 62" fill="none">
                    <rect width="48" height="62" rx="8" fill="#E53935"/>
                    <text x="24" y="44" text-anchor="middle" font-size="14" font-family="Arial" fill="#fff" font-weight="bold">.pdf</text>
                </svg>`;
            case 'doc':
            case 'docx':
                return `<svg width="24" height="32" viewBox="0 0 48 62" fill="none">
                    <rect width="48" height="62" rx="8" fill="#1976D2"/>
                    <text x="24" y="44" text-anchor="middle" font-size="14" font-family="Arial" fill="#fff" font-weight="bold">.docx</text>
                </svg>`;
            case 'ppt':
            case 'pptx':
                return `<svg width="24" height="32" viewBox="0 0 48 62" fill="none">
                    <rect width="48" height="62" rx="8" fill="#FF7043"/>
                    <text x="24" y="44" text-anchor="middle" font-size="14" font-family="Arial" fill="#fff" font-weight="bold">.pptx</text>
                </svg>`;
            case 'txt':
                return `<svg width="24" height="32" viewBox="0 0 48 62" fill="none">
                    <rect width="48" height="62" rx="8" fill="#616161"/>
                    <text x="24" y="44" text-anchor="middle" font-size="14" font-family="Arial" fill="#fff" font-weight="bold">.txt</text>
                </svg>`;
            case 'md':
                return `<svg width="24" height="32" viewBox="0 0 48 62" fill="none">
                    <rect width="48" height="62" rx="8" fill="#43A047"/>
                    <text x="24" y="44" text-anchor="middle" font-size="14" font-family="Arial" fill="#fff" font-weight="bold">.md</text>
                </svg>`;
            default:
                return `<svg width="24" height="32" viewBox="0 0 48 62" fill="none">
                    <rect width="48" height="62" rx="8" fill="#43A047"/>
                    <text x="24" y="44" text-anchor="middle" font-size="14" font-family="Arial" fill="#fff" font-weight="bold">...</text>
                </svg>`;
        }
    }

    // Function to remove file from selection by index
    function removeFileByIndex(index) {
        console.log('removeFileByIndex called with index:', index, 'total files:', fileInput.files.length);
        
        if (fileInput.files && fileInput.files.length > 0) {
            const dataTransfer = new DataTransfer();
            const filesArray = Array.from(fileInput.files);
            
            console.log('Files before removal:', filesArray.map(f => f.name));
            console.log('Removing file at index:', index, 'which is:', filesArray[index]?.name);
            
            // Add all files except the one at the specified index
            filesArray.forEach((file, i) => {
                if (i !== index) {
                    dataTransfer.items.add(file);
                }
            });
            
            // Update the file input with the new file list
            fileInput.files = dataTransfer.files;
            
            console.log('Files after removal:', fileInput.files.length);
            
            // Update the display
            updateFileDisplay(fileInput.files);
        }
    }

    // Global function to remove file from selection (keeping for backwards compatibility)
    window.removeFile = function(event, index) {
        // Prevent the event from bubbling up to parent elements
        event.preventDefault();
        event.stopPropagation();
        removeFileByIndex(index);
    }

    function uploadMultipleFiles(files) {
        uploadStatus.innerHTML = '<p>Uploading ' + files.length + ' file(s)...</p><div id="upload-progress"></div>';
        const progressDiv = document.getElementById('upload-progress');
        let completedUploads = 0;
        let totalFiles = files.length;
        let uploadResults = [];

        files.forEach((file, index) => {
            uploadFile(file, index + 1, totalFiles)
                .then(result => {
                    completedUploads++;
                    uploadResults.push({file: file.name, success: result.success, message: result.message});
                    
                    // Update progress
                    progressDiv.innerHTML = `<p>Progress: ${completedUploads}/${totalFiles} files uploaded</p>`;
                    
                    // If all uploads are complete, show final results
                    if (completedUploads === totalFiles) {
                        showUploadResults(uploadResults);
                    }
                })
                .catch(error => {
                    completedUploads++;
                    uploadResults.push({file: file.name, success: false, message: 'Upload failed: ' + error.message});
                    
                    // Update progress
                    progressDiv.innerHTML = `<p>Progress: ${completedUploads}/${totalFiles} files processed</p>`;
                    
                    // If all uploads are complete, show final results
                    if (completedUploads === totalFiles) {
                        showUploadResults(uploadResults);
                    }
                });
        });
    }

    function showUploadResults(results) {
        const successful = results.filter(r => r.success).length;
        const failed = results.filter(r => r.success === false).length;
        
        let html = `<h4>Upload Complete!</h4>`;
        html += `<p>Successful: ${successful}, Failed: ${failed}</p>`;
        
        if (failed > 0) {
            html += `<details><summary>Show failed uploads</summary><ul>`;
            results.filter(r => r.success === false).forEach(r => {
                html += `<li>${r.file}: ${r.message}</li>`;
            });
            html += `</ul></details>`;
        }
        
        if (successful > 0) {
            html += `<details><summary>Show successful uploads</summary><ul>`;
            results.filter(r => r.success).forEach(r => {
                html += `<li>${r.file}: ${r.message}</li>`;
            });
            html += `</ul></details>`;
        }
        
        uploadStatus.innerHTML = html;
    }


    function uploadFile(file, fileNumber, totalFiles) {
        const url = '/upload/';
        const formData = new FormData();
        formData.append('file', file);
        formData.append('email', emailInput.value.trim());

        return fetch(url, {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (response.ok) {
                return response.json().then(data => ({
                    success: true,
                    message: data.message || 'Upload successful!'
                }));
            } else {
                return response.json().then(data => ({
                    success: false,
                    message: data.error || 'Upload failed.'
                })).catch(() => ({
                    success: false,
                    message: 'Upload failed.'
                }));
            }
        })
        .catch(() => ({
            success: false,
            message: 'Network error during upload.'
        }));
    }

    // Email validation functions
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    function showEmailError(message) {
        emailError.textContent = message;
        emailInput.classList.add('invalid');
        emailInput.classList.remove('valid');
    }

    function clearEmailError() {
        emailError.textContent = '';
        emailInput.classList.remove('invalid');
        emailInput.classList.add('valid');
    }

    function validateEmailAndUpdateButton() {
        const email = emailInput.value.trim();
        
        if (email === '') {
            emailError.textContent = '';
            emailInput.classList.remove('invalid', 'valid');
            uploadButton.disabled = true;
            return false;
        }
        
        if (isValidEmail(email)) {
            clearEmailError();
            uploadButton.disabled = false;
            // Save valid email to cookie
            saveEmailToCookie(email);
            return true;
        } else {
            showEmailError('Please enter a valid email address');
            uploadButton.disabled = true;
            return false;
        }
    }
});