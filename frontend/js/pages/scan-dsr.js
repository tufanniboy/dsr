/**
 * DSR Petrol — Scan DSR Page (Upload & Camera Capture)
 */
import api from '../api.js';
import { showToast } from '../components/toast.js';
import { getUser } from '../auth.js';

export async function renderScanDSR(container) {
    container.innerHTML = `
        <div class="page-header">
            <div>
                <h1 class="page-title">Scan DSR</h1>
                <p class="page-subtitle">Upload or photograph your Daily Sales Report sheet.</p>
            </div>
        </div>

        <div id="scan-content">
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: var(--space-4);">
                <!-- Upload Zone -->
                <div class="upload-zone" id="upload-zone">
                    <div class="upload-zone-icon">
                        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                    </div>
                    <h3>Upload DSR Image</h3>
                    <p>Drag and drop your DSR sheet photo here, or click to browse.</p>
                    <p style="margin-top:var(--space-2);font-size:var(--text-xs);color:var(--text-tertiary)">Supports JPG, PNG, HEIC • Max 10MB</p>
                    <button class="btn btn-primary" style="margin-top:var(--space-4)">Choose File</button>
                    <input type="file" id="file-input" accept="image/*" style="display:none" />
                </div>

                <!-- Camera Capture -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">📷 Camera Capture</h3>
                    </div>
                    <div class="card-body" style="text-align:center">
                        <div id="camera-preview" style="display:none">
                            <div class="camera-container">
                                <video id="camera-video" class="camera-video" autoplay playsinline></video>
                                <div class="camera-overlay">
                                    <div class="camera-frame"></div>
                                </div>
                            </div>
                            <div class="camera-controls">
                                <button class="btn btn-secondary" id="camera-cancel-btn">Cancel</button>
                                <button class="camera-capture-btn" id="camera-capture-btn"></button>
                                <button class="btn btn-secondary" id="camera-flip-btn">Flip</button>
                            </div>
                        </div>
                        <div id="camera-start">
                            <div style="padding:var(--space-8)">
                                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" stroke-width="1.5"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>
                                <h3 style="margin-top:var(--space-3)">Use Camera</h3>
                                <p style="color:var(--text-tertiary);font-size:var(--text-sm);margin-top:var(--space-2)">Take a photo of your DSR sheet directly.</p>
                                <button class="btn btn-secondary" id="start-camera-btn" style="margin-top:var(--space-4)">Open Camera</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Image Preview -->
            <div id="image-preview" class="card mt-6" style="display:none">
                <div class="card-header">
                    <h3 class="card-title">Preview</h3>
                    <div style="display:flex;gap:var(--space-2)">
                        <button class="btn btn-ghost btn-sm" id="preview-rotate">↻ Rotate</button>
                        <button class="btn btn-danger btn-sm" id="preview-cancel">✕ Remove</button>
                    </div>
                </div>
                <div class="card-body" style="text-align:center">
                    <img id="preview-img" style="max-height:400px;border-radius:var(--radius-md);margin:0 auto" />
                </div>
                <div class="card-footer" style="display:flex;justify-content:flex-end;gap:var(--space-3)">
                    <button class="btn btn-primary btn-lg" id="upload-btn">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7V5a2 2 0 012-2h2"/><path d="M17 3h2a2 2 0 012 2v2"/><path d="M21 17v2a2 2 0 01-2 2h-2"/><path d="M7 21H5a2 2 0 01-2-2v-2"/><line x1="7" y1="12" x2="17" y2="12"/></svg>
                        Process with OCR
                    </button>
                </div>
            </div>

            <!-- Processing Status -->
            <div id="processing-status" class="card mt-6" style="display:none">
                <div class="card-body">
                    <div class="processing-container">
                        <div class="processing-spinner"></div>
                        <h3>Processing DSR Sheet...</h3>
                        <p style="color:var(--text-tertiary);margin-top:var(--space-2)">This may take up to 10 seconds.</p>
                        <div class="processing-steps" id="processing-steps"></div>
                    </div>
                </div>
            </div>
        </div>
    `;

    initScanHandlers();
}

function initScanHandlers() {
    let selectedFile = null;
    let cameraStream = null;
    let rotation = 0;

    const fileInput = document.getElementById('file-input');
    const uploadZone = document.getElementById('upload-zone');
    const previewSection = document.getElementById('image-preview');
    const previewImg = document.getElementById('preview-img');

    // Upload zone click
    uploadZone?.addEventListener('click', () => fileInput?.click());

    // Drag & drop
    uploadZone?.addEventListener('dragover', (e) => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
    uploadZone?.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
    uploadZone?.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
    });

    // File input
    fileInput?.addEventListener('change', (e) => {
        if (e.target.files[0]) handleFile(e.target.files[0]);
    });

    function handleFile(file) {
        if (!file.type.startsWith('image/')) {
            showToast('error', 'Invalid File', 'Please select an image file.');
            return;
        }
        if (file.size > 10 * 1024 * 1024) {
            showToast('error', 'File Too Large', 'Maximum file size is 10MB.');
            return;
        }
        selectedFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            previewSection.style.display = 'block';
            rotation = 0;
        };
        reader.readAsDataURL(file);
    }

    // Camera
    document.getElementById('start-camera-btn')?.addEventListener('click', async () => {
        try {
            cameraStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } }
            });
            const video = document.getElementById('camera-video');
            video.srcObject = cameraStream;
            document.getElementById('camera-start').style.display = 'none';
            document.getElementById('camera-preview').style.display = 'block';
        } catch (e) {
            showToast('error', 'Camera Error', 'Could not access camera. Please use file upload instead.');
        }
    });

    // Capture
    document.getElementById('camera-capture-btn')?.addEventListener('click', () => {
        const video = document.getElementById('camera-video');
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        canvas.toBlob((blob) => {
            selectedFile = new File([blob], 'dsr-capture.jpg', { type: 'image/jpeg' });
            previewImg.src = canvas.toDataURL('image/jpeg');
            previewSection.style.display = 'block';
            stopCamera();
        }, 'image/jpeg', 0.9);
    });

    // Cancel camera
    document.getElementById('camera-cancel-btn')?.addEventListener('click', stopCamera);

    function stopCamera() {
        if (cameraStream) {
            cameraStream.getTracks().forEach(t => t.stop());
            cameraStream = null;
        }
        document.getElementById('camera-preview').style.display = 'none';
        document.getElementById('camera-start').style.display = 'block';
    }

    // Remove preview
    document.getElementById('preview-cancel')?.addEventListener('click', () => {
        selectedFile = null;
        previewSection.style.display = 'none';
    });

    // Rotate
    document.getElementById('preview-rotate')?.addEventListener('click', () => {
        rotation = (rotation + 90) % 360;
        previewImg.style.transform = `rotate(${rotation}deg)`;
    });

    // Upload & process
    document.getElementById('upload-btn')?.addEventListener('click', async () => {
        if (!selectedFile) {
            showToast('warning', 'No Image', 'Please select or capture an image first.');
            return;
        }

        const user = getUser();
        const pumpId = user?.pump_id || 'default';

        // Show processing
        document.getElementById('image-preview').style.display = 'none';
        const processingEl = document.getElementById('processing-status');
        processingEl.style.display = 'block';

        const steps = [
            'Uploading image...', 'Detecting document boundaries...', 'Applying perspective correction...',
            'Enhancing image quality...', 'Identifying template...', 'Extracting fields...',
            'Running OCR on each field...', 'Evaluating confidence...', 'AI fallback for low confidence...',
            'Validating data...', 'Preparing review...'
        ];

        const stepsEl = document.getElementById('processing-steps');
        stepsEl.innerHTML = steps.map((s, i) => `
            <div class="processing-step" id="step-${i}">
                <div class="processing-step-icon">${i + 1}</div>
                <span>${s}</span>
            </div>
        `).join('');

        // Animate steps
        let currentStep = 0;
        const stepInterval = setInterval(() => {
            if (currentStep > 0) {
                document.getElementById(`step-${currentStep - 1}`)?.classList.remove('active');
                document.getElementById(`step-${currentStep - 1}`)?.classList.add('done');
                const icon = document.querySelector(`#step-${currentStep - 1} .processing-step-icon`);
                if (icon) icon.textContent = '✓';
            }
            if (currentStep < steps.length) {
                document.getElementById(`step-${currentStep}`)?.classList.add('active');
                currentStep++;
            }
        }, 800);

        try {
            const result = await api.uploadDSR(selectedFile, pumpId);
            clearInterval(stepInterval);
            showToast('success', 'DSR Uploaded!', 'OCR processing has started.');
            // Navigate to review
            setTimeout(() => {
                window.location.hash = `#/review/${result.report_id}`;
            }, 1500);
        } catch (e) {
            clearInterval(stepInterval);
            processingEl.style.display = 'none';
            document.getElementById('image-preview').style.display = 'block';
            showToast('error', 'Upload Failed', e.message);
        }
    });
}
