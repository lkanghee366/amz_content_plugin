-- ============================================
-- Supabase Database Schema for Auto-Post WordPress
-- ============================================

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- Table: websites
-- Stores WordPress site information
-- ============================================
CREATE TABLE IF NOT EXISTS websites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    url VARCHAR(500) NOT NULL,
    username VARCHAR(100) NOT NULL,
    app_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    post_count INTEGER DEFAULT 0,
    last_post_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add index for active websites
CREATE INDEX IF NOT EXISTS idx_websites_is_active ON websites(is_active);

-- Add comment
COMMENT ON TABLE websites IS 'WordPress sites for auto-posting';

-- ============================================
-- Table: posts
-- Stores content to be posted
-- ============================================
CREATE TABLE IF NOT EXISTS posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    website_id UUID REFERENCES websites(id) ON DELETE CASCADE,
    keyword VARCHAR(500) NOT NULL,
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(500) NOT NULL,
    content_html TEXT NOT NULL,
    intro TEXT,
    categories TEXT[], -- Array of category names
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'posted', 'failed')),
    wp_post_id INTEGER, -- WordPress post ID after posting
    error_message TEXT,
    posted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_website_id ON posts(website_id);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at DESC);

-- Add comment
COMMENT ON TABLE posts IS 'Content waiting to be posted to WordPress';

-- ============================================
-- Table: settings
-- System settings for auto-posting
-- ============================================
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    is_paused BOOLEAN DEFAULT false,
    current_website_index INTEGER DEFAULT 0,
    last_run_at TIMESTAMP WITH TIME ZONE,
    total_posts_today INTEGER DEFAULT 0,
    last_reset_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT single_row CHECK (id = 1)
);

-- Insert default settings (only allow 1 row)
INSERT INTO settings (id) VALUES (1)
ON CONFLICT (id) DO NOTHING;

-- Add comment
COMMENT ON TABLE settings IS 'System configuration and state';

-- ============================================
-- Table: post_logs
-- Logs for debugging and monitoring
-- ============================================
CREATE TABLE IF NOT EXISTS post_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    website_id UUID REFERENCES websites(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL, -- 'posted', 'failed', 'retried'
    message TEXT,
    error_details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add index for querying logs
CREATE INDEX IF NOT EXISTS idx_post_logs_created_at ON post_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_post_logs_post_id ON post_logs(post_id);

-- Add comment
COMMENT ON TABLE post_logs IS 'Activity logs for monitoring';

-- ============================================
-- Function: Update updated_at timestamp automatically
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for auto-updating updated_at
CREATE TRIGGER update_websites_updated_at
    BEFORE UPDATE ON websites
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_posts_updated_at
    BEFORE UPDATE ON posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_settings_updated_at
    BEFORE UPDATE ON settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Function: Reset daily post counter
-- ============================================
CREATE OR REPLACE FUNCTION reset_daily_counter()
RETURNS void AS $$
BEGIN
    UPDATE settings
    SET total_posts_today = 0,
        last_reset_date = CURRENT_DATE
    WHERE last_reset_date < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Sample Data (Optional - for testing)
-- ============================================

-- Insert sample website
-- INSERT INTO websites (name, url, username, app_password) VALUES
-- ('ProKitchenReview', 'https://prokitchenreview.com', 'admin', 'your-app-password-here');

-- Insert sample post
-- INSERT INTO posts (website_id, keyword, title, slug, content_html, categories) VALUES
-- (
--     (SELECT id FROM websites WHERE name = 'ProKitchenReview' LIMIT 1),
--     'best air fryer 2024',
--     'Best Air Fryer 2024: Top 10 Reviews & Buying Guide',
--     'best-air-fryer-2024',
--     '<h2>Introduction</h2><p>Looking for the best air fryer...</p>',
--     ARRAY['Kitchen Appliances', 'Air Fryers']
-- );

-- ============================================
-- Verify Tables Created
-- ============================================
SELECT 
    tablename,
    schemaname
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('websites', 'posts', 'settings', 'post_logs')
ORDER BY tablename;

-- ============================================
-- End of Schema
-- ============================================
