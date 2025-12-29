// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const previewContainer = document.getElementById('previewContainer');
const preview = document.getElementById('preview');
const projectBtn = document.getElementById('projectBtn');
const newPhotoBtn = document.getElementById('newPhotoBtn');
const stopBtn = document.getElementById('stopBtn');
const loading = document.getElementById('loading');
const message = document.getElementById('message');
const rotationInput = document.getElementById('rotation');
const rotationValue = document.getElementById('rotationValue');

// State
let currentFile = null;

// Event Listeners
function initEventListeners() {
    // Click upload area
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // Drag & drop handlers
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    
    // File select
    fileInput.addEventListener('change', handleFileSelect);
    
    // Rotation slider
    rotationInput.addEventListener('input', handleRotation);
    
    // Button clicks
    projectBtn.addEventListener('click', handleProject);
    newPhotoBtn.addEventListener('click', handleNewPhoto);
    stopBtn.addEventListener('click', handleStop);
}

// Drag & Drop Handlers
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragging');
}

function handleDragLeave() {
    uploadArea.classList.remove('dragging');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragging');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

// File Select Handler
function handleFileSelect(e) {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
}

// Handle File
function handleFile(file) {
    // Validate file type
    if (!file.type.startsWith('image/')) {
        showMessage('❌ Alleen afbeeldingen zijn toegestaan!', 'error');
        return;
    }
    
    // Validate file size (16MB max)
    if (file.size > 16 * 1024 * 1024) {
        showMessage('❌ Bestand is te groot! Max 16MB.', 'error');
        return;
    }
    
    currentFile = file;
    
    // Read and display preview
    const reader = new FileReader();
    reader.onload = (e) => {
        preview.src = e.target.result;
        preview.style.transform = `rotate(${rotationInput.value}deg)`;
        uploadArea.style.display = 'none';
        previewContainer.classList.add('show');
    };
    reader.readAsDataURL(file);
}

// Rotation Handler
function handleRotation(e) {
    const degrees = e.target.value;
    rotationValue.textContent = degrees;
    
    if (currentFile) {
        preview.style.transform = `rotate(${degrees}deg)`;
    }
}

// Project Handler
async function handleProject() {
    if (!currentFile) {
        showMessage('❌ Geen foto geselecteerd', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('photo', currentFile);
    formData.append('rotation', rotationInput.value);
    
    showLoading(true);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('✅ Foto wordt geprojecteerd!', 'success');
        } else {
            showMessage('❌ ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('❌ Fout bij uploaden: ' + error.message, 'error');
        console.error('Upload error:', error);
    } finally {
        showLoading(false);
    }
}

// New Photo Handler
function handleNewPhoto() {
    currentFile = null;
    fileInput.value = '';
    rotationInput.value = 0;
    rotationValue.textContent = '0';
    preview.style.transform = 'rotate(0deg)';
    preview.src = '';
    previewContainer.classList.remove('show');
    uploadArea.style.display = 'block';
    message.classList.remove('show');
}

// Stop Handler
async function handleStop() {
    try {
        const response = await fetch('/stop', { 
            method: 'POST' 
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('⏹️ Projectie gestopt', 'success');
        } else {
            showMessage('❌ Kon projectie niet stoppen', 'error');
        }
    } catch (error) {
        showMessage('❌ Fout bij stoppen: ' + error.message, 'error');
        console.error('Stop error:', error);
    }
}

// UI Helper Functions
function showLoading(show) {
    loading.classList.toggle('show', show);
    projectBtn.disabled = show;
    newPhotoBtn.disabled = show;
    stopBtn.disabled = show;
}

function showMessage(text, type) {
    message.textContent = text;
    message.className = 'message show ' + type;
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        message.classList.remove('show');
    }, 5000);
}

// Initialize app
document.addEventListener('DOMContentLoaded', initEventListeners);

// Debug log
console.log('📷 Beamer Photo App geladen!');


function callEndpoint(url) {
    fetch(url)
        .then(() => alert('Actie uitgevoerd'))
        .catch(err => alert('Fout: ' + err));
}

function confirmAction(url, message) {
    if (confirm(message)) {
        callEndpoint(url);
    }
}