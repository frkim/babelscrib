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
                <div class="file-row ${fileType}" data-file-index="${index}">
                    <div class="file-icon">${icon}</div>
                    <div class="file-name">${file.name}</div>
                    <div class="file-status">
                        <div class="file-progress" id="progress-${index}">
                            <div class="file-progress-bar"></div>
                        </div>
                        <svg class="file-tick" id="tick-${index}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <polyline points="9,11 12,14 22,4"></polyline>
                        </svg>
                    </div>
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

    // Helper functions to control file progress indicators
    function showFileProgress(fileIndex) {
        const progressElement = document.getElementById(`progress-${fileIndex}`);
        if (progressElement) {
            progressElement.classList.add('show');
        }
    }

    function hideFileProgress(fileIndex) {
        const progressElement = document.getElementById(`progress-${fileIndex}`);
        if (progressElement) {
            progressElement.classList.remove('show');
        }
    }

    function showFileTick(fileIndex) {
        const tickElement = document.getElementById(`tick-${fileIndex}`);
        if (tickElement) {
            tickElement.classList.add('show');
        }
    }

    function hideFileTick(fileIndex) {
        const tickElement = document.getElementById(`tick-${fileIndex}`);
        if (tickElement) {
            tickElement.classList.remove('show');
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
            // Show progress indicator for this file
            showFileProgress(index);
            
            uploadFile(file, index + 1, totalFiles)
                .then(result => {
                    completedUploads++;
                    uploadResults.push({file: file.name, success: result.success, message: result.message});
                    
                    // Hide progress and show tick for this file
                    hideFileProgress(index);
                    if (result.success) {
                        showFileTick(index);
                    }
                    
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
                    
                    // Hide progress for this file (no tick for failed uploads)
                    hideFileProgress(index);
                    
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
            
            // Show translation controls if there are successful uploads
            showTranslationControls();
        }
        
        uploadStatus.innerHTML = html;
    }

    // Function to show translation controls
    function showTranslationControls() {
        const translateControls = document.getElementById('translate-controls');
        if (translateControls) {
            translateControls.classList.add('show');
            setupTranslationHandlers();
        }
    }

    // Function to setup translation event handlers
    function setupTranslationHandlers() {
        const launchTranslationBtn = document.getElementById('launch-translation-btn');
        const translationStatus = document.getElementById('translation-status');
        const targetLanguageSelect = document.getElementById('target-language');
        const sourceLanguageSelect = document.getElementById('source-language');

        if (launchTranslationBtn && !launchTranslationBtn.hasAttribute('data-handler-attached')) {
            launchTranslationBtn.setAttribute('data-handler-attached', 'true');
            launchTranslationBtn.addEventListener('click', function() {
                const targetLanguage = targetLanguageSelect.value;
                const sourceLanguage = sourceLanguageSelect.value;
                const email = emailInput.value.trim();

                if (!email) {
                    showTranslationStatus('Please enter your email address.', 'error');
                    return;
                }

                if (!targetLanguage) {
                    showTranslationStatus('Please select a target language.', 'error');
                    return;
                }

                // Disable button and show loading status
                launchTranslationBtn.disabled = true;
                launchTranslationBtn.textContent = 'Translation in Progress...';
                showTranslationStatus('Starting translation process...', 'loading');

                // Prepare request data
                const requestData = {
                    target_language: targetLanguage,
                    email: email,
                    clear_target: true  // Always clear target files to prevent conflicts
                };

                if (sourceLanguage) {
                    requestData.source_language = sourceLanguage;
                }

                // Make translation request
                fetch('/translate/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                })
                .then(response => {
                    if (response.status === 409) {
                        // Handle conflict (target files already exist)
                        return response.json().then(data => {
                            throw new Error(data.error || 'Translation conflict occurred');
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        showTranslationStatus(
                            `Translation completed successfully! Status: ${data.data.status}. ` +
                            `Total documents: ${data.data.total_documents}, ` +
                            `Succeeded: ${data.data.succeeded_documents}, ` +
                            `Failed: ${data.data.failed_documents}`,
                            'success'
                        );
                        
                        // Show detailed results if available
                        if (data.data.documents && data.data.documents.length > 0) {
                            let detailsHtml = '<br><details><summary>View translation details</summary><ul>';
                            data.data.documents.forEach(doc => {
                                // Debug logging
                                console.log('Document data:', doc);
                                console.log('Source filename:', doc.source_filename);
                                console.log('Translated filename:', doc.translated_filename);
                                console.log('Document ID:', doc.id);
                                
                                if (doc.status === 'Succeeded') {
                                    // Use translated filename if available, otherwise use source filename, fallback to ID
                                    const displayName = doc.translated_filename || doc.source_filename || doc.id;
                                    console.log('Display name for success:', displayName);
                                    detailsHtml += `<li>✅ ${displayName}: Translated to ${doc.translated_to}</li>`;
                                } else {
                                    // Use source filename if available, fallback to ID
                                    const displayName = doc.source_filename || doc.id;
                                    console.log('Display name for failure:', displayName);
                                    detailsHtml += `<li>❌ ${displayName}: ${doc.error ? doc.error.message : 'Failed'}</li>`;
                                }
                            });
                            detailsHtml += '</ul></details>';
                            
                            const currentStatus = translationStatus.innerHTML;
                            translationStatus.innerHTML = currentStatus + detailsHtml;
                        }
                    } else {
                        showTranslationStatus(`Translation failed: ${data.error}`, 'error');
                    }
                })
                .catch(error => {
                    console.error('Translation error:', error);
                    const errorMessage = error.message || 'Translation request failed. Please try again.';
                    
                    if (errorMessage.includes('Target files already exist') || errorMessage.includes('TargetFileAlreadyExists')) {
                        showTranslationStatus(
                            'Previous translation files were found and cleared automatically. Please try the translation again.',
                            'error'
                        );
                    } else {
                        showTranslationStatus(`Translation failed: ${errorMessage}`, 'error');
                    }
                })
                .finally(() => {
                    // Re-enable button
                    launchTranslationBtn.disabled = false;
                    launchTranslationBtn.textContent = 'Launch Translation Process';
                });
            });
        }
    }

    // Function to show translation status messages
    function showTranslationStatus(message, type) {
        const translationStatus = document.getElementById('translation-status');
        const progressContainer = document.getElementById('progress-container');
        
        if (translationStatus) {
            translationStatus.innerHTML = message;
            translationStatus.className = `translation-status show ${type}`;
        }
        
        // Show/hide progress bar based on type
        if (progressContainer) {
            if (type === 'loading') {
                progressContainer.classList.add('show');
            } else {
                progressContainer.classList.remove('show');
            }
        }
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