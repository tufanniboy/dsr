/**
 * DSR Petrol — Modal Component
 */

let modalContainer = null;
let backdrop = null;

function getModalRoot() {
    if (!backdrop) {
        backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop';
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) closeModal();
        });
        document.body.appendChild(backdrop);
    }
    
    if (!modalContainer) {
        modalContainer = document.createElement('div');
        modalContainer.className = 'modal';
        document.body.appendChild(modalContainer);
    }
    
    return { backdrop, modalContainer };
}

export function showModal(title, content, footer = '') {
    const { backdrop, modalContainer } = getModalRoot();
    
    modalContainer.innerHTML = `
        <div class="modal-header">
            <h3 class="modal-title">${title}</h3>
            <button class="modal-close" onclick="import('./components/modal.js').then(m => m.closeModal())">×</button>
        </div>
        <div class="modal-body">
            ${content}
        </div>
        ${footer ? `<div class="modal-footer">${footer}</div>` : ''}
    `;
    
    backdrop.classList.add('open');
    modalContainer.classList.add('open');
}

export function closeModal() {
    if (backdrop) backdrop.classList.remove('open');
    if (modalContainer) modalContainer.classList.remove('open');
}
