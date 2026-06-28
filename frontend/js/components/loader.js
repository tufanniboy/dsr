/**
 * DSR Petrol — Loader Component
 */

export function showLoader(container, message = 'Loading...') {
    if (typeof container === 'string') {
        container = document.querySelector(container);
    }
    if (!container) return;

    container.innerHTML = `
        <div class="processing-container" style="padding: 40px; text-align: center;">
            <div class="processing-spinner"></div>
            <p style="color:var(--text-tertiary); margin-top: 16px;">${message}</p>
        </div>
    `;
}

export function showFullScreenLoader(message = 'Processing...') {
    let loader = document.getElementById('fs-loader');
    if (!loader) {
        loader = document.createElement('div');
        loader.id = 'fs-loader';
        loader.style.cssText = `
            position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 9999;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
        `;
        document.body.appendChild(loader);
    }
    loader.innerHTML = `
        <div class="processing-spinner"></div>
        <h3 style="color:white; margin-top:20px; font-weight:600">${message}</h3>
    `;
    loader.style.display = 'flex';
}

export function hideFullScreenLoader() {
    const loader = document.getElementById('fs-loader');
    if (loader) loader.style.display = 'none';
}
