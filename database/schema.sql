-- ============================================================
-- PETROLEUM DSR OCR PLATFORM — DATABASE SCHEMA
-- Himmat Servo Petroleum Services
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE user_role AS ENUM ('super_admin', 'manager', 'staff');
CREATE TYPE dsr_status AS ENUM ('processing', 'draft', 'pending_review', 'approved', 'rejected');
CREATE TYPE confidence_level AS ENUM ('high', 'medium', 'low');
CREATE TYPE notification_type AS ENUM (
    'pending_approval', 'ocr_failure', 'validation_error',
    'short_amount', 'missing_submission', 'approval_complete',
    'system_alert'
);

-- ============================================================
-- 1. USERS (extends Supabase Auth)
-- ============================================================

CREATE TABLE users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    role user_role NOT NULL DEFAULT 'staff',
    phone TEXT,
    avatar_url TEXT,
    pump_id UUID,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_pump_id ON users(pump_id);
CREATE INDEX idx_users_email ON users(email);

-- ============================================================
-- 2. PETROL PUMPS
-- ============================================================

CREATE TABLE petrol_pumps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    code TEXT UNIQUE NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT,
    pincode TEXT,
    phone TEXT,
    email TEXT,
    gst_number TEXT,
    fuel_types TEXT[] NOT NULL DEFAULT ARRAY['petrol', 'diesel'],
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_pumps_code ON petrol_pumps(code);
CREATE INDEX idx_pumps_city ON petrol_pumps(city);

-- Add FK after petrol_pumps exists
ALTER TABLE users ADD CONSTRAINT fk_users_pump
    FOREIGN KEY (pump_id) REFERENCES petrol_pumps(id) ON DELETE SET NULL;

-- ============================================================
-- 3. TEMPLATES
-- ============================================================

CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT 'v1',
    description TEXT,
    pump_id UUID REFERENCES petrol_pumps(id) ON DELETE SET NULL,
    coordinates JSONB NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_templates_pump ON templates(pump_id);
CREATE INDEX idx_templates_default ON templates(is_default) WHERE is_default = true;

-- ============================================================
-- 4. DSR REPORTS (master record per sheet)
-- ============================================================

CREATE TABLE dsr_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pump_id UUID NOT NULL REFERENCES petrol_pumps(id),
    template_id UUID REFERENCES templates(id),
    manager_name TEXT,
    report_date DATE NOT NULL,
    status dsr_status NOT NULL DEFAULT 'processing',
    original_image_url TEXT,
    processed_image_url TEXT,
    uploaded_by UUID NOT NULL REFERENCES users(id),
    reviewed_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    rejected_at TIMESTAMPTZ,
    rejection_reason TEXT,
    notes TEXT,
    total_sales NUMERIC(12,2) DEFAULT 0,
    total_cash NUMERIC(12,2) DEFAULT 0,
    total_upi NUMERIC(12,2) DEFAULT 0,
    total_card NUMERIC(12,2) DEFAULT 0,
    total_credit NUMERIC(12,2) DEFAULT 0,
    total_expenses NUMERIC(12,2) DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_dsr_reports_pump ON dsr_reports(pump_id);
CREATE INDEX idx_dsr_reports_date ON dsr_reports(report_date);
CREATE INDEX idx_dsr_reports_status ON dsr_reports(status);
CREATE INDEX idx_dsr_reports_uploaded_by ON dsr_reports(uploaded_by);
CREATE INDEX idx_dsr_reports_pump_date ON dsr_reports(pump_id, report_date);

-- ============================================================
-- 5. DSR ENTRIES (one per duty/shift)
-- ============================================================

CREATE TABLE dsr_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES dsr_reports(id) ON DELETE CASCADE,
    duty_number INTEGER NOT NULL CHECK (duty_number BETWEEN 1 AND 6),
    duty_name TEXT,
    start_reading NUMERIC(12,2),
    end_reading NUMERIC(12,2),
    testing NUMERIC(10,2) DEFAULT 0,
    rate NUMERIC(8,2),
    total_amount NUMERIC(12,2),
    card NUMERIC(12,2) DEFAULT 0,
    upi NUMERIC(12,2) DEFAULT 0,
    expenses NUMERIC(12,2) DEFAULT 0,
    credit NUMERIC(12,2) DEFAULT 0,
    total_cash_in_hand NUMERIC(12,2) DEFAULT 0,
    short_amount NUMERIC(12,2) DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(report_id, duty_number)
);

CREATE INDEX idx_dsr_entries_report ON dsr_entries(report_id);

-- ============================================================
-- 6. OCR LOGS (one per processing run)
-- ============================================================

CREATE TABLE ocr_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES dsr_reports(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    processing_time_ms INTEGER,
    total_fields INTEGER DEFAULT 0,
    high_confidence_count INTEGER DEFAULT 0,
    medium_confidence_count INTEGER DEFAULT 0,
    low_confidence_count INTEGER DEFAULT 0,
    gemini_calls INTEGER DEFAULT 0,
    average_confidence NUMERIC(5,2),
    status TEXT NOT NULL DEFAULT 'processing',
    error_message TEXT,
    image_preprocessing_ms INTEGER,
    ocr_extraction_ms INTEGER,
    validation_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ocr_logs_report ON ocr_logs(report_id);
CREATE INDEX idx_ocr_logs_status ON ocr_logs(status);

-- ============================================================
-- 7. OCR FIELDS (per-field OCR result)
-- ============================================================

CREATE TABLE ocr_fields (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ocr_log_id UUID NOT NULL REFERENCES ocr_logs(id) ON DELETE CASCADE,
    report_id UUID NOT NULL REFERENCES dsr_reports(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    duty_number INTEGER,
    ocr_value TEXT,
    ocr_confidence NUMERIC(5,4),
    confidence_level confidence_level,
    gemini_value TEXT,
    gemini_used BOOLEAN NOT NULL DEFAULT false,
    final_value TEXT,
    manually_edited BOOLEAN NOT NULL DEFAULT false,
    edited_value TEXT,
    field_image_url TEXT,
    coordinates JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ocr_fields_log ON ocr_fields(ocr_log_id);
CREATE INDEX idx_ocr_fields_report ON ocr_fields(report_id);
CREATE INDEX idx_ocr_fields_confidence ON ocr_fields(confidence_level);

-- ============================================================
-- 8. VALIDATION LOGS
-- ============================================================

CREATE TABLE validation_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES dsr_reports(id) ON DELETE CASCADE,
    rule_id TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('error', 'warning', 'info')),
    field_name TEXT,
    duty_number INTEGER,
    message TEXT NOT NULL,
    expected_value TEXT,
    actual_value TEXT,
    is_resolved BOOLEAN NOT NULL DEFAULT false,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_validation_logs_report ON validation_logs(report_id);
CREATE INDEX idx_validation_logs_severity ON validation_logs(severity);

-- ============================================================
-- 9. AUDIT LOGS
-- ============================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);

-- ============================================================
-- 10. NOTIFICATIONS
-- ============================================================

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type notification_type NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    data JSONB,
    is_read BOOLEAN NOT NULL DEFAULT false,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = false;

-- ============================================================
-- 11. SETTINGS
-- ============================================================

CREATE TABLE settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pump_id UUID REFERENCES petrol_pumps(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(pump_id, key)
);

CREATE INDEX idx_settings_pump ON settings(pump_id);
CREATE INDEX idx_settings_key ON settings(key);

-- ============================================================
-- ROW LEVEL SECURITY POLICIES
-- ============================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE petrol_pumps ENABLE ROW LEVEL SECURITY;
ALTER TABLE dsr_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE dsr_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE ocr_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ocr_fields ENABLE ROW LEVEL SECURITY;
ALTER TABLE validation_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- Super admin can see everything
CREATE POLICY "Super admins full access" ON users
    FOR ALL USING (
        EXISTS (SELECT 1 FROM users u WHERE u.id = auth.uid() AND u.role = 'super_admin')
    );

-- Users can view their own profile
CREATE POLICY "Users view own profile" ON users
    FOR SELECT USING (id = auth.uid());

-- Users can view their own pump's reports
CREATE POLICY "Users view pump reports" ON dsr_reports
    FOR SELECT USING (
        pump_id IN (SELECT pump_id FROM users WHERE id = auth.uid())
        OR EXISTS (SELECT 1 FROM users u WHERE u.id = auth.uid() AND u.role = 'super_admin')
    );

-- Staff can only view their own uploads
CREATE POLICY "Staff view own uploads" ON dsr_reports
    FOR SELECT USING (
        uploaded_by = auth.uid()
        OR EXISTS (SELECT 1 FROM users u WHERE u.id = auth.uid() AND u.role IN ('manager', 'super_admin'))
    );

-- Users can view own notifications
CREATE POLICY "Users own notifications" ON notifications
    FOR ALL USING (user_id = auth.uid());

-- Service role bypass for backend
CREATE POLICY "Service role bypass users" ON users
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role bypass pumps" ON petrol_pumps
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role bypass reports" ON dsr_reports
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role bypass entries" ON dsr_entries
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role bypass ocr_logs" ON ocr_logs
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role bypass ocr_fields" ON ocr_fields
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role bypass validation" ON validation_logs
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role bypass audit" ON audit_logs
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role bypass templates" ON templates
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role bypass notifications" ON notifications
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role bypass settings" ON settings
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_pumps_updated_at BEFORE UPDATE ON petrol_pumps
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_reports_updated_at BEFORE UPDATE ON dsr_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_entries_updated_at BEFORE UPDATE ON dsr_entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_settings_updated_at BEFORE UPDATE ON settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- STORAGE BUCKETS (run via Supabase dashboard or API)
-- ============================================================
-- Create bucket: dsr-images (public: false)
-- Policies: authenticated users can upload, service role can read all
