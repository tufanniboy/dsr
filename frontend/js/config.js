/**
 * DSR Petrol Platform — Configuration
 */
const CONFIG = {
    API_BASE_URL: 'https://dsr-backend-puoq.onrender.com/api/v1',
    SUPABASE_URL: '',       // Set from env
    SUPABASE_KEY: '',       // Set from env
    APP_NAME: 'DSR Petrol',
    APP_FULL_NAME: 'Himmat Servo Petroleum Services',
    VERSION: '1.0.0',
    CURRENCY: '₹',
    DATE_FORMAT: 'DD/MM/YYYY',
    MAX_UPLOAD_SIZE_MB: 10,
    OCR_CONFIDENCE: { HIGH: 95, LOW: 85 },
    REFRESH_INTERVAL_MS: 60000,
    ITEMS_PER_PAGE: 20,
};

// Allow runtime overrides
if (window.__DSR_CONFIG__) {
    Object.assign(CONFIG, window.__DSR_CONFIG__);
}

export default CONFIG;
