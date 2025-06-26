document.addEventListener('DOMContentLoaded', function() {
    console.log('Upload.js loaded - Version: 2025-06-25 23:30');
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

    // Store current files for accumulation
    let currentFiles = [];

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
        
        // Don't open dialog if clicking on the button (it has its own handler)
        if (e.target.closest('#select-file-button')) {
            return;
        }
        
        // Only open file dialog if we didn't click on a remove button or the select button
        console.log('Drop area clicked');
        e.preventDefault();
        e.stopPropagation();
        openFileDialog();
    });

    // When files are selected, update the drop area and prepare for upload
    fileInput.addEventListener('change', function() {
        console.log('fileInput change event triggered, files.length:', fileInput.files.length);
        if (fileInput.files.length > 0) {
            const newFiles = Array.from(fileInput.files);
            console.log('New files selected:', newFiles.map(f => f.name));
            
            // Add new files to current selection (avoid duplicates by name and size)
            newFiles.forEach(file => {
                if (!currentFiles.some(f => f.name === file.name && f.size === file.size)) {
                    currentFiles.push(file);
                }
            });
            
            console.log('Current files after merge:', currentFiles.map(f => f.name));
            
            // Update the file input with all accumulated files
            const dataTransfer = new DataTransfer();
            currentFiles.forEach(file => {
                dataTransfer.items.add(file);
            });
            fileInput.files = dataTransfer.files;
            
            console.log('Final fileInput.files.length:', fileInput.files.length);
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
            showEmailError(window.BabelScribI18n ? window.BabelScribI18n.t('please_enter_valid_email') : 'Please enter a valid email address');
            return;
        }
        if (fileInput.files.length > 0) {
            uploadMultipleFiles(Array.from(fileInput.files));
        } else {
            uploadStatus.textContent = window.BabelScribI18n ? window.BabelScribI18n.t('please_select_files_first') : 'Please select files first.';
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
            const newFiles = Array.from(files);
            
            // Add new files to current selection (avoid duplicates by name and size)
            newFiles.forEach(file => {
                if (!currentFiles.some(f => f.name === file.name && f.size === file.size)) {
                    currentFiles.push(file);
                }
            });
            
            // Update the file input with all accumulated files
            const dataTransfer = new DataTransfer();
            currentFiles.forEach(file => {
                dataTransfer.items.add(file);
            });
            fileInput.files = dataTransfer.files;
            
            updateFileDisplay(fileInput.files);
        }
    }

    function updateFileDisplay(files) {
        if (files.length === 0) {
            // Reset current files array
            currentFiles = [];
            
            // Reset to original state with complete content
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
                <p>Click here to select Documents button or drag and drop your files here</p>
                <p><small>Supported formats: pdf, doc, docx, txt, pptx, md</small></p>
                <p><small>Document size limit: ≤ 40MB per file • Up to 1000 files per batch • Total batch size ≤ 250MB</small></p>
                <p><small><a id="azure-ai-limits-link" href="https://learn.microsoft.com/en-us/azure/ai-services/translator/service-limits#asynchronous-batch-operation-limits" target="_blank" style="color: #007cba; text-decoration: none;">View all Azure AI Translator limits →</a></small></p>
                <div style="text-align: center; margin-top: 15px;">
                    <button type="button" class="btn" id="select-file-button" style="display: inline-block;">Select Documents</button>
                </div>
            `;
            
            // Re-attach event listener for the new select button
            const newSelectButton = document.getElementById('select-file-button');
            if (newSelectButton) {
                newSelectButton.addEventListener('click', function(e) {
                    console.log('Select Document button clicked');
                    e.preventDefault();
                    e.stopPropagation();
                    openFileDialog();
                });
            }
            
            // Re-attach event listener for the Azure AI limits link to prevent file dialog
            const newLink = document.getElementById('azure-ai-limits-link');
            if (newLink) {
                newLink.addEventListener('click', function(event) {
                    event.stopPropagation();
                });
            }
            
            // Update upload button state when files are cleared
            validateEmailAndUpdateButton();
            
            return;
        }

        // Create file list display
        let html = '<p><strong>' + (window.BabelScribI18n ? window.BabelScribI18n.t('selected_files', {count: files.length}) : 'Selected ' + files.length + ' file(s)') + ':</strong></p>';
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
        html += '<p><small>' + (window.BabelScribI18n ? window.BabelScribI18n.t('click_add_documents') : 'Click here to add other documents') + '</small></p>';
        
        fileDrop.innerHTML = html;
        
        // Update upload button state based on file selection and email validity
        console.log('updateFileDisplay: calling validateEmailAndUpdateButton');
        validateEmailAndUpdateButton();
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
            case 'xls':
            case 'xlsx': return 'xlsx';
            case 'txt': return 'txt';
            case 'csv': return 'csv';
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
            case 'xls':
            case 'xlsx':
                return `<svg width="24" height="32" viewBox="0 0 48 62" fill="none">
                    <rect width="48" height="62" rx="8" fill="#43A047"/>
                    <text x="24" y="44" text-anchor="middle" font-size="12" font-family="Arial" fill="#fff" font-weight="bold">.xlsx</text>
                </svg>`;
            case 'txt':
                return `<svg width="24" height="32" viewBox="0 0 48 62" fill="none">
                    <rect width="48" height="62" rx="8" fill="#616161"/>
                    <text x="24" y="44" text-anchor="middle" font-size="14" font-family="Arial" fill="#fff" font-weight="bold">.txt</text>
                </svg>`;
            case 'csv':
                return `<svg width="24" height="32" viewBox="0 0 48 62" fill="none">
                    <rect width="48" height="62" rx="8" fill="#9C27B0"/>
                    <text x="24" y="44" text-anchor="middle" font-size="14" font-family="Arial" fill="#fff" font-weight="bold">.csv</text>
                </svg>`;
            case 'md':
                return `<svg width="24" height="32" viewBox="0 0 48 62" fill="none">
                    <rect width="48" height="62" rx="8" fill="#9C27B0"/>
                    <text x="24" y="44" text-anchor="middle" font-size="14" font-family="Arial" fill="#fff" font-weight="bold">.md</text>
                </svg>`;
            default:
                return `<svg width="24" height="32" viewBox="0 0 48 62" fill="none">
                    <rect width="48" height="62" rx="8" fill="#9C27B0"/>
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
            const filesArray = Array.from(fileInput.files);
            
            console.log('Files before removal:', filesArray.map(f => f.name));
            console.log('Removing file at index:', index, 'which is:', filesArray[index]?.name);
            
            // Remove from currentFiles array
            currentFiles.splice(index, 1);
            
            // Create new DataTransfer with remaining files
            const dataTransfer = new DataTransfer();
            currentFiles.forEach(file => {
                dataTransfer.items.add(file);
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
        uploadStatus.innerHTML = '<p>' + (window.BabelScribI18n ? window.BabelScribI18n.t('uploading_files', {count: files.length}) : `Uploading ${files.length} file(s)...`) + '</p><div id="upload-progress"></div>';
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
                    uploadResults.push({file: file.name, success: false, message: (window.BabelScribI18n ? window.BabelScribI18n.t('upload_failed', {error: error.message}) : 'Upload failed: ' + error.message)});
                    
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
        
        let html = `<h4>${window.BabelScribI18n ? window.BabelScribI18n.t('upload_complete') : 'Upload Complete!'}</h4>`;
        html += `<p>${window.BabelScribI18n ? window.BabelScribI18n.t('successful_failed', {successful: successful, failed: failed}) : `Successful: ${successful}, Failed: ${failed}`}</p>`;
        
        if (failed > 0) {
            html += `<details><summary>Show failed uploads</summary><ul>`;
            results.filter(r => r.success === false).forEach(r => {
                html += `<li>${r.file}: ${r.message}</li>`;
            });
            html += `</ul></details>`;
        }
        
        if (successful > 0) {
            html += `<details><summary>${window.BabelScribI18n ? window.BabelScribI18n.t('show_successful_uploads') : 'Show successful uploads'}</summary><ul>`;
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
                    showTranslationStatus(window.BabelScribI18n ? window.BabelScribI18n.t('please_enter_email_address') : 'Please enter your email address.', 'error');
                    return;
                }

                if (!targetLanguage) {
                    showTranslationStatus(window.BabelScribI18n ? window.BabelScribI18n.t('please_select_target_language') : 'Please select a target language.', 'error');
                    return;
                }

                // Disable button and show loading status with enhanced progress
                launchTranslationBtn.disabled = true;
                launchTranslationBtn.textContent = window.BabelScribI18n ? window.BabelScribI18n.t('translation_in_progress') : 'Translation in Progress...';
                
                // Start elapsed time tracking
                const startTime = Date.now();
                let elapsedSeconds = 0;
                
                // Show initial progress with elapsed time
                showTranslationProgressWithTime('Starting translation process', elapsedSeconds);
                
                // Timer to update elapsed time every second
                const timeInterval = setInterval(() => {
                    elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
                    const currentMessage = getCurrentProgressMessage(elapsedSeconds);
                    showTranslationProgressWithTime(currentMessage, elapsedSeconds);
                }, 1000);
                
                // Simulate progress updates during translation
                let progressMessages = [
                    'Preparing documents for translation',
                    'Connecting to translation service',
                    'Processing documents',
                    'Translating content',
                    'Finalizing translation'
                ];
                
                let currentStep = 0;
                const progressInterval = setInterval(() => {
                    if (currentStep < progressMessages.length) {
                        // Don't call showTranslationProgress here anymore, let the timer handle it
                        currentStep++;
                    }
                }, 2000); // Update every 2 seconds
                
                // Helper function to get current progress message based on elapsed time
                function getCurrentProgressMessage(seconds) {
                    if (!window.BabelScribI18n) {
                        // Fallback to English if i18n not available
                        if (seconds < 2) return 'Starting translation process';
                        if (seconds < 4) return 'Starting translation process - Preparing documents for translation';
                        if (seconds < 6) return 'Starting translation process - Connecting to translation service';
                        if (seconds < 8) return 'Starting translation process - Processing documents';
                        if (seconds < 10) return 'Starting translation process - Translating content';
                        return 'Starting translation process - Finalizing translation';
                    }
                    
                    // Use i18n translations
                    const t = window.BabelScribI18n.t;
                    if (seconds < 2) return t('starting_translation_process');
                    if (seconds < 4) return t('preparing_documents');
                    if (seconds < 6) return t('connecting_service');
                    if (seconds < 8) return t('processing_documents');
                    if (seconds < 10) return t('translating_content');
                    return t('finalizing_translation');
                }

                // Prepare request data - email is now handled by session
                const requestData = {
                    target_language: targetLanguage,
                    clear_target: true,  // Always clear target files to prevent conflicts
                    cleanup_source: true  // Always clean up source files automatically
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
                        // Clear both intervals
                        clearInterval(progressInterval);
                        clearInterval(timeInterval);
                        
                        // Handle conflict (target files already exist)
                        return response.json().then(data => {
                            throw new Error(data.error || 'Translation conflict occurred');
                        });
                    }
                    
                    // Check for other error status codes
                    if (!response.ok) {
                        // Clear both intervals
                        clearInterval(progressInterval);
                        clearInterval(timeInterval);
                        
                        return response.json().then(data => {
                            throw new Error(data.error || `Translation failed with status ${response.status}`);
                        });
                    }
                    
                    return response.json();
                })
                .then(data => {
                    // Clear both intervals
                    clearInterval(progressInterval);
                    clearInterval(timeInterval);
                    
                    // Debug logging
                    console.log('Translation response received:', data);
                    console.log('Translation data.data:', data.data);
                    console.log('data.success:', data.success);
                    console.log('data.error:', data.error);
                    if (data.data) {
                        console.log('Total documents:', data.data.total_documents);
                        console.log('Succeeded documents:', data.data.succeeded_documents);
                        console.log('Failed documents:', data.data.failed_documents);
                        console.log('Documents array:', data.data.documents);
                        console.log('Documents array length:', data.data.documents ? data.data.documents.length : 'undefined');
                        if (data.data.documents && data.data.documents.length > 0) {
                            console.log('First document:', data.data.documents[0]);
                        }
                    }
                    
                    if (data.success) {
                        // Ensure we have valid counts, defaulting to 0 if undefined
                        const totalDocs = data.data.total_documents ?? 0;
                        const succeededDocs = data.data.succeeded_documents ?? 0;
                        const failedDocs = data.data.failed_documents ?? 0;
                        
                        // Determine the appropriate message based on the status and results
                        let mainMessage;
                        let statusType = 'success';
                        
                        if (data.data.status === 'Succeeded' && failedDocs === 0) {
                            // All documents succeeded
                            mainMessage = window.BabelScribI18n ? window.BabelScribI18n.t('translation_completed_successfully') : 'Translation completed successfully!';
                        } else if (data.data.status === 'Succeeded' && failedDocs > 0) {
                            // Some documents succeeded, some failed
                            mainMessage = window.BabelScribI18n ? window.BabelScribI18n.t('translation_completed_with_failures') : 'Translation completed with some failures.';
                            statusType = 'warning';
                        } else if (data.data.status === 'Failed' || (succeededDocs === 0 && failedDocs > 0)) {
                            // All documents failed
                            mainMessage = window.BabelScribI18n ? window.BabelScribI18n.t('translation_failed_completely') : 'Translation failed completely.';
                            statusType = 'error';
                        } else {
                            // Default fallback
                            mainMessage = (window.BabelScribI18n ? window.BabelScribI18n.t('translation_completed_successfully') : 'Translation completed successfully!');
                        }
                        
                        // Build main success message
                        let successMessage = mainMessage + ' ' +
                            (window.BabelScribI18n ? window.BabelScribI18n.t('status_label') : 'Status:') + ' ' + data.data.status + '. ' +
                            (window.BabelScribI18n ? window.BabelScribI18n.t('total_documents', {total: totalDocs}) : `Total documents: ${totalDocs}`) + ', ' +
                            (window.BabelScribI18n ? window.BabelScribI18n.t('succeeded_label', {count: succeededDocs}) : `Succeeded: ${succeededDocs}`) + ', ' +
                            (window.BabelScribI18n ? window.BabelScribI18n.t('failed_label', {count: failedDocs}) : `Failed: ${failedDocs}`);
                        
                        // Add source cleanup information if available
                        if (data.data.source_cleanup) {
                            const cleanup = data.data.source_cleanup;
                            if (cleanup.cleanup_attempted) {
                                if (cleanup.cleaned_files > 0) {
                                    successMessage += ' ' + (window.BabelScribI18n ? window.BabelScribI18n.t('automatically_removed_source_files', {count: cleanup.cleaned_files}) : `Automatically removed ${cleanup.cleaned_files} source files.`);
                                    if (cleanup.failed_cleanups > 0) {
                                        successMessage += ' ' + (window.BabelScribI18n ? window.BabelScribI18n.t('failed_cleanup_count', {count: cleanup.failed_cleanups}) : `(${cleanup.failed_cleanups} failed to clean)`);
                                    }
                                } else if (cleanup.failed_cleanups > 0) {
                                    successMessage += ' ' + (window.BabelScribI18n ? window.BabelScribI18n.t('failed_to_remove_source_files', {count: cleanup.failed_cleanups}) : `Failed to automatically remove ${cleanup.failed_cleanups} source files`);
                                } else {
                                    successMessage += ' ' + (window.BabelScribI18n ? window.BabelScribI18n.t('no_source_files_found') : 'No source files found to remove');
                                }
                            } else {
                                successMessage += ' ' + (window.BabelScribI18n ? window.BabelScribI18n.t('cleanup_not_performed', {reason: cleanup.reason}) : `Automatic source cleanup was not performed: ${cleanup.reason}`);
                            }
                        }
                        
                        showTranslationStatus(successMessage, statusType);
                        
                        // Show detailed results if available
                        if (data.data.documents && data.data.documents.length > 0) {
                            console.log('Processing documents for display:', data.data.documents);
                            let detailsHtml = '<br><details><summary>' + (window.BabelScribI18n ? window.BabelScribI18n.t('view_translation_details') : 'View translation details') + '</summary><ul>';
                            let downloadLinksHtml = '<br><div style="margin-top: 15px;"><h5>' + (window.BabelScribI18n ? window.BabelScribI18n.t('download_translated_documents') : 'Download Translated Documents:') + '</h5><ul style="list-style: none; padding-left: 0;">';
                            let hasSuccessfulTranslations = false;
                            
                            data.data.documents.forEach((doc, index) => {
                                // Debug logging
                                console.log(`Document ${index}:`, doc);
                                console.log(`Document ${index} status:`, doc.status);
                                console.log(`Document ${index} source filename:`, doc.source_filename);
                                console.log(`Document ${index} translated filename:`, doc.translated_filename);
                                console.log(`Document ${index} ID:`, doc.id);
                                
                                if (doc.status === 'Succeeded') {
                                    console.log(`Document ${index} is successful, adding to download links`);
                                    hasSuccessfulTranslations = true;
                                    // Use translated filename if available, otherwise use source filename, fallback to ID
                                    const displayName = doc.translated_filename || doc.source_filename || doc.id;
                                    console.log('Display name for success:', displayName);
                                    detailsHtml += `<li>✅ ${displayName}: ` + (window.BabelScribI18n ? window.BabelScribI18n.t('translated_to', {language: doc.translated_to}) : `Translated to ${doc.translated_to}`) + '</li>';
                                    
                                    // Add download link for successful translations
                                    // Use the translated filename for the download URL
                                    const fileName = doc.translated_filename || `translated_${doc.source_filename}` || `document_${doc.id}`;
                                    
                                    // Extract just the filename without any path for URLs
                                    // If fileName contains a path separator, take only the filename part
                                    const actualFileName = fileName.includes('/') ? fileName.split('/').pop() : fileName;
                                    const fullPath = fileName; // Keep the full path for internal operations
                                    
                                    const downloadUrl = `/download/${encodeURIComponent(actualFileName)}/`;
                                    const deleteUrl = `/delete-individual/${encodeURIComponent(actualFileName)}/`;
                                    downloadLinksHtml += `
                                        <li style="margin: 8px 0; padding: 8px; background-color: #e8f5e8; border-radius: 4px; border-left: 3px solid #43a047;">
                                            <strong>${actualFileName}</strong><br>
                                            <small>` + (window.BabelScribI18n ? window.BabelScribI18n.t('translated_to', {language: doc.translated_to}) : `Translated to: ${doc.translated_to}`) + `</small><br>
                                            <div style="margin-top: 8px; display: flex; align-items: center; gap: 15px;">
                                                <a href="${downloadUrl}" 
                                                   download="${actualFileName}" 
                                                   style="color: #2e7d32; text-decoration: none; font-weight: bold; display: inline-flex; align-items: center; gap: 5px;"
                                                   onmouseover="this.style.textDecoration='underline'" 
                                                   onmouseout="this.style.textDecoration='none'">
                                                    📥 ` + (window.BabelScribI18n ? window.BabelScribI18n.t('download_translated_document') : 'Download Translated Document') + `
                                                </a>
                                                <a href="#" 
                                                   data-filename="${actualFileName}"
                                                   data-delete-url="${deleteUrl}"
                                                   class="delete-individual-btn"
                                                   style="color: #d32f2f; text-decoration: none; font-weight: bold; display: inline-flex; align-items: center; gap: 5px;"
                                                   title="` + (window.BabelScribI18n ? window.BabelScribI18n.t('delete_translated_document_tooltip') : 'Delete the translated document from the server') + `"
                                                   onmouseover="this.style.textDecoration='underline'" 
                                                   onmouseout="this.style.textDecoration='none'">
                                                    🗑️ ` + (window.BabelScribI18n ? window.BabelScribI18n.t('delete') : 'Delete') + `
                                                </a>
                                            </div>
                                        </li>
                                    `;
                                } else {
                                    // Use source filename if available, fallback to ID
                                    const displayName = doc.source_filename || doc.id;
                                    console.log('Display name for failure:', displayName);
                                    detailsHtml += `<li>❌ ${displayName}: ${doc.error ? doc.error.message : (window.BabelScribI18n ? window.BabelScribI18n.t('translation_failed') : 'Failed')}</li>`;
                                }
                            });
                            
                            detailsHtml += '</ul></details>';
                            downloadLinksHtml += '</ul>';
                            
                            console.log('hasSuccessfulTranslations:', hasSuccessfulTranslations);
                            console.log('downloadLinksHtml:', downloadLinksHtml);
                            
                            // Add delete button if there are successful translations
                            if (hasSuccessfulTranslations) {
                                downloadLinksHtml += `
                                    <div style="margin-top: 15px; text-align: center;">
                                        <button id="delete-translated-btn" 
                                                style="background-color: #dc3545; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 14px; transition: background-color 0.2s;"
                                                onmouseover="this.style.backgroundColor='#c82333'" 
                                                onmouseout="this.style.backgroundColor='#dc3545'">
                                            🗑️ ` + (window.BabelScribI18n ? window.BabelScribI18n.t('delete_all_translated_documents') : 'Delete All Translated Documents') + `
                                        </button>
                                    </div>
                                `;
                            }
                            
                            downloadLinksHtml += '</div>';
                            
                            const currentStatus = translationStatus.innerHTML;
                            let finalHtml = currentStatus + detailsHtml;
                            
                            // Only add download links if there are successful translations
                            if (hasSuccessfulTranslations) {
                                finalHtml += downloadLinksHtml;
                                console.log('Adding download links to final HTML');
                            } else {
                                console.log('No successful translations found, not adding download links');
                            }
                            
                            console.log('Final HTML being set:', finalHtml);
                            translationStatus.innerHTML = finalHtml;
                            
                            // Add event listener for delete button if it exists
                            if (hasSuccessfulTranslations) {
                                const deleteBtn = document.getElementById('delete-translated-btn');
                                if (deleteBtn) {
                                    deleteBtn.addEventListener('click', function() {
                                        const confirmMessage = window.BabelScribI18n ? 
                                            window.BabelScribI18n.t('delete_confirm_message') : 
                                            'Are you sure you want to delete all translated documents? This action cannot be undone.';
                                            
                                        if (confirm(confirmMessage)) {
                                            deleteAllTranslatedDocuments();
                                        }
                                    });
                                }
                                
                                // Add event listeners for individual delete buttons
                                const individualDeleteBtns = document.querySelectorAll('.delete-individual-btn');
                                individualDeleteBtns.forEach(btn => {
                                    btn.addEventListener('click', function(e) {
                                        e.preventDefault();
                                        const filename = this.getAttribute('data-filename');
                                        const deleteUrl = this.getAttribute('data-delete-url');
                                        
                                        const confirmMessage = window.BabelScribI18n ? 
                                            window.BabelScribI18n.t('delete_individual_confirm_message', {filename: filename}) : 
                                            `Are you sure you want to delete "${filename}"? This action cannot be undone.`;
                                            
                                        if (confirm(confirmMessage)) {
                                            deleteIndividualTranslatedDocument(filename, deleteUrl);
                                        }
                                    });
                                });
                            }
                        }
                    } else {
                        showTranslationStatus((window.BabelScribI18n ? window.BabelScribI18n.t('translation_failed_error', {error: data.error}) : `Translation failed: ${data.error}`), 'error');
                    }
                })
                .catch(error => {
                    // Clear both intervals
                    clearInterval(progressInterval);
                    clearInterval(timeInterval);
                    
                    console.error('Translation error:', error);
                    const errorMessage = error.message || (window.BabelScribI18n ? window.BabelScribI18n.t('translation_request_failed') : 'Translation request failed. Please try again.');
                    
                    if (errorMessage.includes('No documents found for translation')) {
                        showTranslationStatus(
                            window.BabelScribI18n ? window.BabelScribI18n.t('no_documents_for_translation') : 'No documents found for translation. Please upload documents first.',
                            'error'
                        );
                    } else if (errorMessage.includes('Session error')) {
                        showTranslationStatus(
                            window.BabelScribI18n ? window.BabelScribI18n.t('session_error_translation') : 'Session error. Please refresh the page and try again.',
                            'error'
                        );
                    } else if (errorMessage.includes('Target files already exist') || errorMessage.includes('TargetFileAlreadyExists')) {
                        showTranslationStatus(
                            window.BabelScribI18n ? window.BabelScribI18n.t('previous_files_cleared') : 'Previous translation files were found and cleared automatically. Please try the translation again.',
                            'error'
                        );
                    } else {
                        showTranslationStatus((window.BabelScribI18n ? window.BabelScribI18n.t('translation_failed_error', {error: errorMessage}) : `Translation failed: ${errorMessage}`), 'error');
                    }
                })
                .finally(() => {
                    // Re-enable button
                    launchTranslationBtn.disabled = false;
                    launchTranslationBtn.textContent = window.BabelScribI18n ? window.BabelScribI18n.t('launch_translation_process') : 'Launch Translation Process';
                });
            });
        }
    }

    // Function to show translation status messages with enhanced progress bar
    function showTranslationStatus(message, type) {
        const translationStatus = document.getElementById('translation-status');
        const progressContainer = document.getElementById('progress-container');
        
        if (translationStatus) {
            if (type === 'loading') {
                // Create enhanced loading message with spinner
                const loadingHtml = `
                    <div class="translation-progress-text">
                        <div class="translation-spinner"></div>
                        <span>${message}</span>
                    </div>
                `;
                translationStatus.innerHTML = loadingHtml;
            } else {
                translationStatus.innerHTML = message;
            }
            translationStatus.className = `translation-status show ${type}`;
        }
        
        // Show/hide and animate progress bar based on type
        if (progressContainer) {
            if (type === 'loading') {
                progressContainer.classList.add('show');
                // Add pulsing effect to the progress container
                progressContainer.style.animation = 'pulseContainer 2s ease-in-out infinite';
            } else {
                progressContainer.classList.remove('show');
                progressContainer.style.animation = '';
            }
        }
    }

    // Add new function to show translation progress with elapsed time
    function showTranslationProgressWithTime(message, elapsedSeconds) {
        const translationStatus = document.getElementById('translation-status');
        const progressContainer = document.getElementById('progress-container');
        
        if (translationStatus) {
            // Format the message to always show "Starting translation process (X seconds)..."
            let displayMessage;
            
            if (!window.BabelScribI18n) {
                // Fallback without i18n
                if (message === 'Starting translation process') {
                    displayMessage = `Starting translation process (${elapsedSeconds} seconds)`;
                } else {
                    displayMessage = `${message} (${elapsedSeconds} seconds)`;
                }
            } else {
                // Use i18n translations
                const t = window.BabelScribI18n.t;
                if (message === 'Starting translation process' || message === t('starting_translation_process')) {
                    displayMessage = t('translation_process_seconds', {seconds: elapsedSeconds});
                } else if (message.includes('Connecting to translation service') || message === t('connecting_service')) {
                    displayMessage = t('connecting_service_seconds', {seconds: elapsedSeconds});
                } else if (message.includes('Translating content') || message === t('translating_content')) {
                    displayMessage = t('translating_content_seconds', {seconds: elapsedSeconds});
                } else {
                    // For other messages, keep the elapsed time format
                    const secondsWord = window.BabelScribI18n.t(elapsedSeconds === 1 ? 'second' : 'seconds');
                    displayMessage = `${message} (${elapsedSeconds} ${secondsWord})`;
                }
            }
            
            const progressHtml = `
                <div class="translation-progress-text">
                    <div class="translation-spinner"></div>
                    <span>${displayMessage}...</span>
                </div>
            `;
            translationStatus.innerHTML = progressHtml;
            translationStatus.className = 'translation-status show loading';
        }
        
        if (progressContainer) {
            progressContainer.classList.add('show');
            progressContainer.style.animation = 'pulseContainer 2s ease-in-out infinite';
        }
    }

    // Add new function to show translation progress with percentage (if available)
    function showTranslationProgress(message, percentage = null) {
        const translationStatus = document.getElementById('translation-status');
        const progressContainer = document.getElementById('progress-container');
        
        if (translationStatus) {
            let progressHtml = `
                <div class="translation-progress-text">
                    <div class="translation-spinner"></div>
                    <span>${message}</span>
            `;
            
            if (percentage !== null) {
                progressHtml += ` <span style="font-weight: bold; color: #43a047;">(${percentage}%)</span>`;
            }
            
            progressHtml += `</div>`;
            translationStatus.innerHTML = progressHtml;
            translationStatus.className = 'translation-status show loading';
        }
        
        if (progressContainer) {
            progressContainer.classList.add('show');
            progressContainer.style.animation = 'pulseContainer 2s ease-in-out infinite';
        }
    }

    function uploadFile(file, fileNumber, totalFiles) {
        const url = '/upload/';
        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_email', emailInput.value.trim());
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        formData.append('csrfmiddlewaretoken', csrfToken);

        return fetch(url, {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (response.ok) {
                return response.json().then(data => {
                    let message = data.message || 'Upload successful!';
                    
                    // Add information about deleted documents if any
                    if (data.previous_documents_deleted && data.previous_documents_deleted.count > 0) {
                        message += ` (${data.previous_documents_deleted.count} previous document(s) were automatically deleted)`;
                    }
                    
                    return ({
                        success: true,
                        message: message
                    });
                });
            } else {
                return response.json().then(data => ({
                    success: false,
                    message: data.error || (window.BabelScribI18n ? window.BabelScribI18n.t('upload_failed_generic') : 'Upload failed.')
                })).catch(() => ({
                    success: false,
                    message: window.BabelScribI18n ? window.BabelScribI18n.t('upload_failed_generic') : 'Upload failed.'
                }));
            }
        })
        .catch(() => ({
            success: false,
            message: window.BabelScribI18n ? window.BabelScribI18n.t('network_error_upload') : 'Network error during upload.'
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
        const hasFiles = fileInput.files && fileInput.files.length > 0;
        
        console.log('validateEmailAndUpdateButton called:');
        console.log('- Email:', email);
        console.log('- Email valid:', isValidEmail(email));
        console.log('- Has files:', hasFiles);
        console.log('- File count:', fileInput.files ? fileInput.files.length : 0);
        
        if (email === '') {
            emailError.textContent = '';
            emailInput.classList.remove('invalid', 'valid');
            uploadButton.disabled = true;
            console.log('- Button disabled: email empty');
            return false;
        }
        
        if (isValidEmail(email)) {
            clearEmailError();
            // Enable upload button only if email is valid AND files are selected
            uploadButton.disabled = !hasFiles;
            console.log('- Button disabled set to:', !hasFiles);
            // Save valid email to cookie
            saveEmailToCookie(email);
            return true;
        } else {
            showEmailError(window.BabelScribI18n ? window.BabelScribI18n.t('please_enter_valid_email') : 'Please enter a valid email address');
            uploadButton.disabled = true;
            console.log('- Button disabled: invalid email');
            return false;
        }
    }
    
    // Function to delete all translated documents
    function deleteAllTranslatedDocuments() {
        const translationStatus = document.getElementById('translation-status');
        
        // Show loading state
        if (translationStatus) {
            const loadingMessage = window.BabelScribI18n ? 
                window.BabelScribI18n.t('deleting_translated_documents') : 
                'Deleting translated documents...';
            translationStatus.innerHTML = `
                <div class="translation-progress-text">
                    <div class="translation-spinner"></div>
                    <span>${loadingMessage}</span>
                </div>
            `;
            translationStatus.className = 'translation-status show loading';
        }
        
        // Make delete request
        fetch('/delete-translated/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const successMessage = window.BabelScribI18n ? 
                    window.BabelScribI18n.t('deleted_translated_documents_success', {count: data.deleted_count}) : 
                    `Successfully deleted ${data.deleted_count} translated documents`;
                
                // Clear the translation status area completely
                if (translationStatus) {
                    translationStatus.innerHTML = successMessage;
                    translationStatus.className = 'translation-status show success';
                    
                    // Clear the status after a few seconds
                    setTimeout(() => {
                        translationStatus.innerHTML = '';
                        translationStatus.className = 'translation-status';
                    }, 3000);
                }
            } else {
                const errorMessage = window.BabelScribI18n ? 
                    window.BabelScribI18n.t('delete_translated_documents_error', {error: data.error}) : 
                    `Failed to delete translated documents: ${data.error}`;
                
                if (translationStatus) {
                    translationStatus.innerHTML = errorMessage;
                    translationStatus.className = 'translation-status show error';
                }
            }
        })
        .catch(error => {
            console.error('Delete error:', error);
            const errorMessage = window.BabelScribI18n ? 
                window.BabelScribI18n.t('delete_translated_documents_error', {error: error.message}) : 
                `Failed to delete translated documents: ${error.message}`;
            
            if (translationStatus) {
                translationStatus.innerHTML = errorMessage;
                translationStatus.className = 'translation-status show error';
            }
        });
    }
    
    function deleteIndividualTranslatedDocument(filename, deleteUrl) {
        const translationStatus = document.getElementById('translation-status');
        
        // Show loading state
        if (translationStatus) {
            const loadingMessage = window.BabelScribI18n ? 
                window.BabelScribI18n.t('deleting_individual_document', {filename: filename}) : 
                `Deleting ${filename}...`;
            translationStatus.innerHTML = `
                <div class="translation-progress-text">
                    <div class="translation-spinner"></div>
                    <span>${loadingMessage}</span>
                </div>
            `;
            translationStatus.className = 'translation-status show loading';
        }
        
        // Get CSRF token
        function getCsrfToken() {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            return csrfToken ? csrfToken.value : '';
        }
        
        // Make delete request
        const headers = {
            'Content-Type': 'application/json',
        };
        
        // Add CSRF token if available
        const csrfToken = getCsrfToken();
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
        
        fetch(deleteUrl, {
            method: 'POST',
            headers: headers
        })
        .then(response => {
            console.log('Delete response status:', response.status);
            console.log('Delete response headers:', response.headers);
            
            // Check if response is JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.error('Response is not JSON, content-type:', contentType);
                return response.text().then(text => {
                    console.error('Response text:', text);
                    throw new Error(`Server returned non-JSON response: ${text.substring(0, 200)}...`);
                });
            }
            
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const successMessage = window.BabelScribI18n ? 
                    window.BabelScribI18n.t('deleted_individual_document_success', {filename: filename}) : 
                    `Successfully deleted ${filename}`;
                
                // Remove the individual file from the download list 
                const deleteBtn = document.querySelector(`[data-filename="${filename}"]`);
                if (deleteBtn) {
                    const listItem = deleteBtn.closest('li');
                    if (listItem) {
                        listItem.remove();
                    }
                }
                
                // Show success message briefly
                if (translationStatus) {
                    translationStatus.innerHTML = successMessage;
                    translationStatus.className = 'translation-status show success';
                    
                    // Clear the status after a few seconds
                    setTimeout(() => {
                        translationStatus.innerHTML = '';
                        translationStatus.className = 'translation-status';
                    }, 2000);
                }
                
                // Check if there are any remaining download links
                const remainingDownloadLinks = document.querySelectorAll('.delete-individual-btn');
                if (remainingDownloadLinks.length === 0) {
                    // If no more files, remove the entire download section
                    const downloadSection = document.querySelector('div[style*="margin-top: 15px;"] h5');
                    if (downloadSection) {
                        const downloadContainer = downloadSection.closest('div');
                        if (downloadContainer) {
                            downloadContainer.remove();
                        }
                    }
                }
            } else {
                const errorMessage = window.BabelScribI18n ? 
                    window.BabelScribI18n.t('delete_individual_document_error', {filename: filename, error: data.error}) : 
                    `Failed to delete ${filename}: ${data.error}`;
                
                if (translationStatus) {
                    translationStatus.innerHTML = errorMessage;
                    translationStatus.className = 'translation-status show error';
                }
            }
        })
        .catch(error => {
            console.error('Delete error:', error);
            const errorMessage = window.BabelScribI18n ? 
                window.BabelScribI18n.t('delete_individual_document_error', {filename: filename, error: error.message}) : 
                `Failed to delete ${filename}: ${error.message}`;
            
            if (translationStatus) {
                translationStatus.innerHTML = errorMessage;
                translationStatus.className = 'translation-status show error';
            }
        });
    }
    
    // Make function globally accessible
    window.validateEmailAndUpdateButton = validateEmailAndUpdateButton;
    
    // Initial validation check on page load
    console.log('Running initial validation check...');
    validateEmailAndUpdateButton();
});