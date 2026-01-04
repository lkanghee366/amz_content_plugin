# 🚀 Auto-Post WordPress System - Implementation Plan

## 📋 Overview

Hệ thống tự động lấy bài viết từ Supabase database và post lên nhiều WordPress sites theo vòng lặp. Có thể pause/resume từ xa.

---

## 🎯 Goals

- ✅ Post tự động mỗi 5 phút
- ✅ Quản lý nhiều WordPress sites
- ✅ Pause/Resume từ xa qua Supabase
- ✅ Track status của từng bài
- ✅ Xoay vòng giữa các websites

---

## 📊 Database Schema (Supabase)

### Table: `websites`
```sql
CREATE TABLE websites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    url VARCHAR(500) NOT NULL,
    username VARCHAR(100) NOT NULL,
    app_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    post_count INTEGER DEFAULT 0,
    last_post_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Table: `posts`
```sql
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    website_id UUID REFERENCES websites(id),
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(500) NOT NULL,
    content_html TEXT NOT NULL,
    categories TEXT[], -- Array of category names
    status VARCHAR(50) DEFAULT 'pending', -- pending/posted/failed
    error_message TEXT,
    posted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_website_id ON posts(website_id);
```

### Table: `settings`
```sql
CREATE TABLE settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    is_paused BOOLEAN DEFAULT false,
    current_website_index INTEGER DEFAULT 0,
    last_run_at TIMESTAMP,
    total_posts_today INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert default settings
INSERT INTO settings (id) VALUES (1);
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         Supabase PostgreSQL                 │
│  ┌──────────┬──────────┬──────────────┐    │
│  │ websites │  posts   │  settings    │    │
│  └──────────┴──────────┴──────────────┘    │
└─────────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────────┐
│      Auto-Post Script (Python)              │
│  ┌──────────────────────────────────────┐   │
│  │  1. Check if paused                  │   │
│  │  2. Get current website              │   │
│  │  3. Get 1 pending post               │   │
│  │  4. Post to WordPress REST API       │   │
│  │  5. Update post status               │   │
│  │  6. Rotate to next website           │   │
│  │  7. Sleep 5 minutes                  │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────────┐
│       WordPress Sites (Multiple)            │
│  Site 1 → Site 2 → Site 3 → Site 1 ...     │
└─────────────────────────────────────────────┘
```

---

## 📁 File Structure

```
auto_post_wordpress/
├── main.py                 # Main loop script
├── supabase_client.py     # Supabase integration
├── wordpress_poster.py    # WordPress REST API client
├── config.py              # Configuration
├── requirements.txt       # Dependencies
├── .env.example          # Environment variables template
├── .env                  # Environment variables (gitignored)
└── README.md             # Documentation
```

---

## 🔧 Implementation Steps

### Phase 1: Setup & Database
- [ ] Create Supabase project
- [ ] Create database tables (websites, posts, settings)
- [ ] Insert sample data for testing
- [ ] Setup environment variables

### Phase 2: Core Components
- [ ] `supabase_client.py`: CRUD operations
  - [ ] Get settings (is_paused, current_website_index)
  - [ ] Get active websites
  - [ ] Get pending post by website_id
  - [ ] Update post status (posted/failed)
  - [ ] Update settings (rotate website)
  
- [ ] `wordpress_poster.py`: WordPress API
  - [ ] Post article (title, slug, content, categories)
  - [ ] Handle authentication (Application Password)
  - [ ] Error handling & retry logic
  - [ ] Get category IDs by name
  
- [ ] `config.py`: Configuration management
  - [ ] Supabase credentials
  - [ ] Posting interval (default 5 minutes)
  - [ ] Max retries
  - [ ] Logging setup

### Phase 3: Main Loop
- [ ] `main.py`: Main automation loop
  - [ ] Check if paused
  - [ ] Get current website
  - [ ] Get next pending post
  - [ ] Post to WordPress
  - [ ] Update database
  - [ ] Rotate to next website
  - [ ] Sleep interval
  - [ ] Graceful shutdown (Ctrl+C)

### Phase 4: Control Interface
- [ ] CLI commands
  - [ ] `python control.py pause` - Pause posting
  - [ ] `python control.py resume` - Resume posting
  - [ ] `python control.py status` - Show current status
  - [ ] `python control.py stats` - Show statistics

### Phase 5: Testing & Deployment
- [ ] Unit tests for each component
- [ ] Integration tests
- [ ] Error handling & edge cases
- [ ] Logging & monitoring
- [ ] Documentation
- [ ] Deployment guide (systemd service / Docker)

---

## 🔄 Main Loop Logic

```python
while True:
    # 1. Check if paused
    if is_paused():
        log("System is paused, waiting...")
        sleep(60)
        continue
    
    # 2. Get current website
    website = get_current_website()
    if not website or not website.is_active:
        rotate_to_next_website()
        continue
    
    # 3. Get pending post for this website
    post = get_pending_post(website.id)
    if not post:
        log(f"No pending posts for {website.name}, rotating...")
        rotate_to_next_website()
        continue
    
    # 4. Post to WordPress
    try:
        wp_post_id = post_to_wordpress(
            website.url,
            website.username,
            website.app_password,
            post.title,
            post.slug,
            post.content_html,
            post.categories
        )
        
        # 5. Update post status
        mark_as_posted(post.id, wp_post_id)
        log(f"✅ Posted: {post.title} to {website.name}")
        
    except Exception as e:
        mark_as_failed(post.id, str(e))
        log(f"❌ Failed: {post.title} - {e}")
    
    # 6. Rotate to next website
    rotate_to_next_website()
    
    # 7. Wait before next post
    log(f"Waiting {INTERVAL} minutes...")
    sleep(INTERVAL * 60)
```

---

## 🎮 Control Commands

### Pause System
```bash
python control.py pause
```
Updates `settings.is_paused = true`

### Resume System
```bash
python control.py resume
```
Updates `settings.is_paused = false`

### Check Status
```bash
python control.py status
```
Shows:
- Is paused?
- Current website
- Posts pending/posted/failed
- Last post time

### Statistics
```bash
python control.py stats
```
Shows:
- Posts today per website
- Success rate
- Failed posts
- Total posts

---

## 📦 Dependencies

```txt
supabase==2.3.0
python-dotenv==1.0.0
requests==2.31.0
schedule==1.2.0
```

---

## 🔐 Environment Variables

```env
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-service-key

# Settings
POST_INTERVAL_MINUTES=5
MAX_RETRIES=3
LOG_LEVEL=INFO
```

---

## 📊 Monitoring & Logging

### Log Format
```
2024-12-21 13:00:00 - INFO - System started
2024-12-21 13:05:00 - INFO - ✅ Posted: "Best Air Fryer 2024" to ProKitchenReview
2024-12-21 13:10:00 - INFO - Rotated to next website: CookingTools
2024-12-21 13:15:00 - ERROR - ❌ Failed: "Best Blender" - Connection timeout
2024-12-21 13:20:00 - INFO - System paused by user
```

### Metrics to Track
- Posts per hour/day
- Success rate per website
- Average posting time
- Error types and frequency

---

## 🚀 Deployment Options

### Option 1: Linux Server (systemd)
```bash
sudo systemctl start auto-post-wordpress
sudo systemctl enable auto-post-wordpress
```

### Option 2: Docker Container
```bash
docker build -t auto-post-wordpress .
docker run -d --restart always auto-post-wordpress
```

### Option 3: Cloud (Heroku/Railway/Render)
Deploy as a worker process

---

## ⚠️ Error Handling

### Scenarios to Handle
1. WordPress site down → Mark failed, try next site
2. Network timeout → Retry 3 times
3. Invalid credentials → Skip site, notify admin
4. Database connection lost → Retry connection
5. Duplicate slug → Generate new slug

---

## 🎯 Success Criteria

- ✅ Posts automatically every 5 minutes
- ✅ Rotates through all active websites
- ✅ Can pause/resume remotely
- ✅ Tracks all post statuses
- ✅ Logs errors for debugging
- ✅ Handles failures gracefully
- ✅ Runs 24/7 without manual intervention

---

## 📝 Next Steps

1. **Review this plan** - Confirm requirements
2. **Setup Supabase** - Create project and tables
3. **Implement Phase 1** - Database & environment
4. **Build Phase 2** - Core components
5. **Test & Deploy** - Production ready

---

## 💡 Future Enhancements

- [ ] Web dashboard for management
- [ ] Email notifications on failures
- [ ] Schedule posting times per website
- [ ] A/B testing for post formats
- [ ] Analytics integration
- [ ] Backup system for failed posts
- [ ] Multi-language support

---

**Ready to start?** Let's implement Phase 1! 🚀
