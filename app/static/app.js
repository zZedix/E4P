// E4P Application JavaScript

// Global state
let currentTaskId = null;
let progressInterval = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize dark mode
    initializeDarkMode();
    
    // Initialize file upload
    initializeFileUpload();
    
    // Initialize password toggle
    initializePasswordToggle();
    
    // Initialize forms
    initializeEncryptForm();
    initializeDecryptForm();
    
    // Set initial language
    const savedLang = localStorage.getItem('e4p_lang') || 'en';
    document.getElementById('language-selector').value = savedLang;
    switchLanguage(savedLang);
}

// Dark mode functionality
function initializeDarkMode() {
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const isDarkMode = localStorage.getItem('e4p_dark_mode') === 'true' || 
                      (!localStorage.getItem('e4p_dark_mode') && window.matchMedia('(prefers-color-scheme: dark)').matches);
    
    if (isDarkMode) {
        document.documentElement.classList.add('dark');
    }
    
    darkModeToggle.addEventListener('click', function() {
        const isDark = document.documentElement.classList.toggle('dark');
        localStorage.setItem('e4p_dark_mode', isDark);
    });
}

// File upload functionality
function initializeFileUpload() {
    const dropZones = document.querySelectorAll('#drop-zone');
    const fileInputs = document.querySelectorAll('#file-input');
    
    dropZones.forEach((dropZone, index) => {
        const fileInput = fileInputs[index];
        
        // Click to select files
        dropZone.addEventListener('click', () => {
            fileInput.click();
        });
        
        // Drag and drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFileSelection(fileInput);
            }
        });
        
        // File input change
        fileInput.addEventListener('change', () => {
            handleFileSelection(fileInput);
        });
    });
}

function handleFileSelection(fileInput) {
    const files = Array.from(fileInput.files);
    const fileList = document.getElementById('file-list');
    const fileInfo = document.getElementById('file-info');
    
    if (files.length === 0) {
        if (fileList) fileList.innerHTML = '';
        if (fileInfo) fileInfo.classList.add('hidden');
        return;
    }
    
    // For encrypt page
    if (fileList) {
        fileList.innerHTML = '';
        files.forEach((file, index) => {
            const fileItem = createFileItem(file, index);
            fileList.appendChild(fileItem);
        });
    }
    
    // For decrypt page
    if (fileInfo && files.length === 1) {
        const file = files[0];
        document.getElementById('file-name').textContent = file.name;
        document.getElementById('file-details').textContent = formatFileSize(file.size);
        fileInfo.classList.remove('hidden');
    }
}

function createFileItem(file, index) {
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item bg-gray-50 dark:bg-gray-700 rounded-lg p-3 flex items-center justify-between';
    
    fileItem.innerHTML = `
        <div class="flex items-center space-x-3 rtl:space-x-reverse">
            <svg class="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"></path>
            </svg>
            <div>
                <div class="text-sm font-medium text-gray-900 dark:text-white">${file.name}</div>
                <div class="text-sm text-gray-500 dark:text-gray-400">${formatFileSize(file.size)}</div>
            </div>
        </div>
        <button type="button" onclick="removeFile(${index})" class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300">
            <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
            </svg>
        </button>
    `;
    
    return fileItem;
}

function removeFile(index) {
    const fileInput = document.getElementById('file-input');
    const dt = new DataTransfer();
    const files = Array.from(fileInput.files);
    
    files.forEach((file, i) => {
        if (i !== index) {
            dt.items.add(file);
        }
    });
    
    fileInput.files = dt.files;
    handleFileSelection(fileInput);
}

// Password toggle functionality
function initializePasswordToggle() {
    const toggleButtons = document.querySelectorAll('#toggle-password, #toggle-confirm-password');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const passwordInput = this.parentElement.querySelector('input');
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
        });
    });
}

// Password validation
function validatePasswordMatch() {
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm-password');
    const errorDiv = document.getElementById('password-match-error');
    
    if (!password || !confirmPassword || !errorDiv) return true;
    
    if (password.value !== confirmPassword.value) {
        errorDiv.classList.remove('hidden');
        password.classList.add('error');
        confirmPassword.classList.add('error');
        return false;
    } else {
        errorDiv.classList.add('hidden');
        password.classList.remove('error');
        confirmPassword.classList.remove('error');
        return true;
    }
}

// Encrypt form functionality
function initializeEncryptForm() {
    const form = document.getElementById('encrypt-form');
    if (!form) return;
    
    // Add real-time password validation
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm-password');
    
    if (password && confirmPassword) {
        password.addEventListener('input', validatePasswordMatch);
        confirmPassword.addEventListener('input', validatePasswordMatch);
    }
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const files = formData.getAll('files');
        
        if (files.length === 0) {
            showError('Please select at least one file');
            return;
        }
        
        const password = formData.get('password');
        if (!password) {
            showError('Please enter a password');
            return;
        }
        
        // Validate password match
        if (!validatePasswordMatch()) {
            showError('Passwords do not match');
            return;
        }
        
        const algorithm = formData.get('algorithm');
        
        try {
            await encryptFiles(files, password, algorithm);
        } catch (error) {
            showError('Encryption failed: ' + error.message);
        }
    });
}

// Decrypt form functionality
function initializeDecryptForm() {
    const form = document.getElementById('decrypt-form');
    if (!form) return;
    
    // Add real-time password validation
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm-password');
    
    if (password && confirmPassword) {
        password.addEventListener('input', validatePasswordMatch);
        confirmPassword.addEventListener('input', validatePasswordMatch);
    }
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const file = formData.get('file');
        
        if (!file) {
            showError('Please select a .e4p file');
            return;
        }
        
        const password = formData.get('password');
        if (!password) {
            showError('Please enter a password');
            return;
        }
        
        // Validate password match
        if (!validatePasswordMatch()) {
            showError('Passwords do not match');
            return;
        }
        
        try {
            await decryptFile(file, password);
        } catch (error) {
            showError('Decryption failed: ' + error.message);
        }
    });
}

// Encryption process
async function encryptFiles(files, password, algorithm) {
    const formData = new FormData();
    
    files.forEach(file => {
        formData.append('files', file);
    });
    formData.append('password', password);
    formData.append('algorithm', algorithm);
    
    showProgress();
    hideError();
    hideResults();
    
    try {
        const response = await fetch('/api/encrypt', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Encryption failed');
        }
        
        const result = await response.json();
        currentTaskId = result.task_id;
        
        // Start polling for progress
        startProgressPolling();
        
    } catch (error) {
        hideProgress();
        showError(error.message);
    }
}

// Decryption process
async function decryptFile(file, password) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('password', password);
    
    showProgress();
    hideError();
    hideResults();
    
    try {
        const response = await fetch('/api/decrypt', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Decryption failed');
        }
        
        const result = await response.json();
        showDecryptResults(result);
        
    } catch (error) {
        hideProgress();
        showError(error.message);
    }
}

// Progress polling
function startProgressPolling() {
    if (progressInterval) {
        clearInterval(progressInterval);
    }
    
    progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${currentTaskId}`);
            const status = await response.json();
            
            updateProgress(status.progress);
            
            if (status.status === 'completed') {
                clearInterval(progressInterval);
                hideProgress();
                showEncryptResults(status);
            } else if (status.status === 'failed') {
                clearInterval(progressInterval);
                hideProgress();
                showError(status.error_message || 'Encryption failed');
            }
        } catch (error) {
            clearInterval(progressInterval);
            hideProgress();
            showError('Failed to check encryption status');
        }
    }, 1000);
}

// UI helper functions
function showProgress() {
    const progressSection = document.getElementById('progress-section');
    if (progressSection) {
        progressSection.classList.remove('hidden');
    }
}

function hideProgress() {
    const progressSection = document.getElementById('progress-section');
    if (progressSection) {
        progressSection.classList.add('hidden');
    }
}

function updateProgress(percent) {
    const progressBar = document.getElementById('progress-bar');
    const progressPercent = document.getElementById('progress-percent');
    
    if (progressBar) {
        progressBar.style.width = percent + '%';
    }
    if (progressPercent) {
        progressPercent.textContent = Math.round(percent) + '%';
    }
}

function showEncryptResults(status) {
    const resultsSection = document.getElementById('results-section');
    const downloadLinks = document.getElementById('download-links');
    
    if (resultsSection && downloadLinks) {
        downloadLinks.innerHTML = '';
        
        status.files.forEach(file => {
            const downloadLink = createDownloadLink(file);
            downloadLinks.appendChild(downloadLink);
        });
        
        resultsSection.classList.remove('hidden');
    }
}

function showDecryptResults(result) {
    const resultsSection = document.getElementById('results-section');
    const downloadBtn = document.getElementById('download-btn');
    
    if (resultsSection && downloadBtn) {
        downloadBtn.href = `/download/${result.download_token}`;
        resultsSection.classList.remove('hidden');
    }
    
    hideProgress();
}

function createDownloadLink(file) {
    const linkDiv = document.createElement('div');
    linkDiv.className = 'flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700';
    
    linkDiv.innerHTML = `
        <div class="flex items-center space-x-3 rtl:space-x-reverse">
            <svg class="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
            </svg>
            <div>
                <div class="text-sm font-medium text-gray-900 dark:text-white">${file.original_name}.e4p</div>
                <div class="text-sm text-gray-500 dark:text-gray-400">${formatFileSize(file.size || 0)} • ${file.algorithm || 'AES-256-GCM'}</div>
            </div>
        </div>
        <a href="/download/${file.download_token || 'placeholder'}" 
           class="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 download-btn">
            <svg class="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
            Download
        </a>
    `;
    
    return linkDiv;
}

function showError(message) {
    const errorSection = document.getElementById('error-section');
    const errorMessage = document.getElementById('error-message');
    
    if (errorSection && errorMessage) {
        errorMessage.textContent = message;
        errorSection.classList.remove('hidden');
    }
}

function hideError() {
    const errorSection = document.getElementById('error-section');
    if (errorSection) {
        errorSection.classList.add('hidden');
    }
}

function hideResults() {
    const resultsSection = document.getElementById('results-section');
    if (resultsSection) {
        resultsSection.classList.add('hidden');
    }
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Remove file functionality for decrypt page
document.addEventListener('click', function(e) {
    if (e.target && e.target.id === 'remove-file') {
        const fileInput = document.getElementById('file-input');
        fileInput.value = '';
        handleFileSelection(fileInput);
    }
});

// Language switching
function switchLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('e4p_lang', lang);
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'fa' ? 'rtl' : 'ltr';
    updateTranslations();
}

function updateTranslations() {
    const t = translations[currentLang];
    if (!t) return;
    
    document.title = t.title;
    
    // Update elements with data-translate attribute
    document.querySelectorAll('[data-translate]').forEach(el => {
        const key = el.getAttribute('data-translate');
        if (t[key]) {
            el.textContent = t[key];
        }
    });
}
