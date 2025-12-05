# Amazon to WordPress Auto Poster 🚀

Chương trình Python tự động tạo bài viết so sánh sản phẩm Amazon và đăng lên WordPress qua REST API.

## ✨ Tính năng

- ✅ Tìm kiếm sản phẩm từ Amazon PA-API
- ✅ Generate nội dung bằng Cerebras AI (llama3.1-70b)
- ✅ Tự động rotate API keys khi hit rate limit
- ✅ Tạo bài viết WordPress với HTML structure hoàn chỉnh:
  - Introduction
  - Editor's Choice
  - Product Comparison Cards
  - Buying Guide
  - FAQs
- ✅ Hỗ trợ batch processing từ file keywords.txt
- ✅ Delay giữa các bài để tránh spam

## 📦 Cài đặt

### 1. Clone/Download project

```powershell
cd C:\Users\quang\Downloads\amz_content_plugin\python_poster
```

### 2. Cài đặt Python dependencies

```powershell
pip install -r requirements.txt
```

### 3. Cấu hình

#### 3.1 Copy file .env

```powershell
Copy-Item .env.example .env
```

#### 3.2 Chỉnh sửa `.env`

Mở file `.env` và điền thông tin:

```env
# WordPress Configuration
WP_SITE_URL=https://yoursite.com
WP_USERNAME=admin
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx

# Amazon PA-API Configuration
AMAZON_ACCESS_KEY=AKPA5ULF681752575129
AMAZON_SECRET_KEY=YmYcpWerS9ACCnAvt5RRkTJqu1d7/W1dAbW3J8Wq
AMAZON_PARTNER_TAG=toolsrevi00b3-20
AMAZON_REGION=us-east-1

# Cerebras API Keys File
CEREBRAS_KEYS_FILE=cerebras_api_keys.txt
CEREBRAS_MODEL=llama3.1-70b

# Post Settings
POST_AUTHOR_ID=2
POST_CATEGORY_ID=5
POST_STATUS=draft
POST_DELAY_SECONDS=12
```

#### 3.3 Thêm Cerebras API Keys

Mở file `cerebras_api_keys.txt` và thêm API keys (mỗi key 1 dòng):

```
csk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
csk-yyyyyyyyyyyyyyyyyyyyyyyyyyy
csk-zzzzzzzzzzzzzzzzzzzzzzzzzzzzz
```

#### 3.4 Thêm keywords

Mở file `keywords.txt` và thêm keywords (mỗi keyword 1 dòng):

```
best laptop 2024
wireless headphones
gaming mouse
coffee maker
air fryer
```

## 🚀 Sử dụng

### Chạy chương trình

```powershell
python main.py
```

### Output mẫu

```
╔═══════════════════════════════════════════════════════════╗
║  Amazon Product Comparison → WordPress Auto Poster       ║
║  Powered by PA-API + Cerebras AI                         ║
╚═══════════════════════════════════════════════════════════╝

2024-11-07 10:30:15 - INFO - 🚀 Initializing Amazon WP Poster...
2024-11-07 10:30:15 - INFO - ✅ Loaded 3 Cerebras API key(s)
2024-11-07 10:30:15 - INFO - ✅ Initialized Cerebras client with key #0
2024-11-07 10:30:16 - INFO - ✅ Amazon PA-API initialized for region: US
2024-11-07 10:30:16 - INFO - ✅ WordPress API initialized: https://yoursite.com
2024-11-07 10:30:16 - INFO - ✅ All components initialized successfully!

2024-11-07 10:30:16 - INFO - 📋 Found 3 keyword(s) to process
2024-11-07 10:30:16 - INFO - ⏱️ Estimated time: ~2.1 minutes

============================================================
🎯 Processing keyword: best laptop 2024
============================================================

📦 Step 1: Searching Amazon products...
🔍 Searching Amazon for: 'best laptop 2024' (max 10 results)
✓ Found: MacBook Pro 16-inch, M3 Chip...
✅ Retrieved 10 products

🤖 Step 2: Generating AI content...
📝 Generating introduction for: best laptop 2024
✅ Introduction generated (85 words)
🏷️ Generating badges for 10 products
✅ Generated 10 badges, top: B0XXXXXX
📚 Generating buying guide for: best laptop 2024
✅ Generated buying guide with 5 sections
❓ Generating FAQs for: best laptop 2024
✅ Generated 7 FAQs
✅ All AI content generated successfully!

🏗️ Step 3: Building HTML content...
✅ HTML content built (12450 chars)

📤 Step 4: Posting to WordPress...
✅ Post created successfully!
   ID: 123
   Status: draft
   URL: https://yoursite.com/comparison-best-laptop-2024/

============================================================
✅ SUCCESS! Post created for: best laptop 2024
============================================================

⏳ Waiting 12 seconds before next post...
```

## 📁 Cấu trúc thư mục

```
python_poster/
├── main.py                      # File chính
├── cerebras_client.py           # Cerebras AI client với key rotation
├── amazon_api.py                # Amazon PA-API wrapper
├── ai_generator.py              # AI content generation
├── html_builder.py              # HTML structure builder
├── wordpress_api.py             # WordPress REST API client
├── requirements.txt             # Python dependencies
├── .env                         # Configuration (không commit)
├── .env.example                 # Configuration template
├── cerebras_api_keys.txt        # Cerebras API keys (không commit)
├── keywords.txt                 # Danh sách keywords
├── amazon_poster.log            # Log file
└── README.md                    # Documentation
```

## 🔧 Troubleshooting

### Lỗi: "Import amazon.paapi could not be resolved"

Cài đặt lại thư viện:

```powershell
pip install --upgrade python-amazon-paapi
```

### Lỗi: "WordPress connection failed"

1. Kiểm tra `WP_SITE_URL` có đúng không
2. Kiểm tra Application Password:
   - Vào WordPress: Users → Profile → Application Passwords
   - Tạo password mới
   - Copy vào `.env` (giữ nguyên dấu cách)

### Lỗi: "Cerebras API rate limit"

- Chương trình tự động rotate sang key tiếp theo
- Thêm nhiều API keys vào `cerebras_api_keys.txt`

### Lỗi: "No products found"

- Kiểm tra Amazon PA-API credentials
- Thử keyword khác (tiếng Anh)

## 📝 Notes

- Chương trình sẽ chờ 12 giây giữa mỗi bài (có thể thay đổi trong `.env`)
- Tất cả bài sẽ ở trạng thái `draft` theo mặc định
- Log được lưu vào file `amazon_poster.log`
- API keys tự động rotate khi gặp rate limit

## 🛡️ Security

**QUAN TRỌNG:** Không commit các file sau lên Git:

- `.env`
- `cerebras_api_keys.txt`
- `amazon_poster.log`

Thêm vào `.gitignore`:

```
.env
cerebras_api_keys.txt
*.log
__pycache__/
```

## 📞 Support

Nếu gặp vấn đề, check log file `amazon_poster.log` để xem chi tiết lỗi.
