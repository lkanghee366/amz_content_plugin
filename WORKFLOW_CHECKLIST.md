# 🔍 KIỂM TRA LUỒNG HOẠT ĐỘNG - CHECKLIST

## ✅ CÁC ĐIỂM ĐÃ KIỂM TRA VÀ SỬA

### 1. **Configuration Files** ✅
- [x] `.env.example` - POST_AUTHOR_ID phải là số (đã sửa từ "default" → 2)
- [x] `.env.example` - CEREBRAS_MODEL đúng: `gpt-oss-120b`
- [x] `cerebras_api_keys.txt` - Đã có 15 API keys
- [x] `keywords.txt` - Đã có 533 keywords

### 2. **Model Name Consistency** ✅
- [x] `cerebras_client.py` - Default model: `gpt-oss-120b`
- [x] `main.py` - Default model: `gpt-oss-120b`
- [x] `test_workflow.py` - Default model: `gpt-oss-120b`
- [x] `.env.example` - Model: `gpt-oss-120b`

### 3. **Amazon API** ✅
- [x] Rating extraction fix: Đổi từ `content_rating` → `customer_reviews.star_rating`
- [x] Region mapping: US, UK, DE, JP, SG
- [x] Credentials từ .env

### 4. **WordPress API** ✅
- [x] Application Password authentication
- [x] REST API endpoint: `/wp-json/wp/v2/posts`
- [x] Test connection method
- [x] Category và Author ID support

### 5. **AI Content Generator** ✅
- [x] Introduction generation (60-100 words)
- [x] Badges generation (JSON parsing với fallback)
- [x] Buying Guide (flexible schema handling)
- [x] FAQs (array validation)

### 6. **HTML Builder** ✅
- [x] Editor's Choice section
- [x] Best-for-purpose section
- [x] Product comparison cards
- [x] Buying guide rendering
- [x] FAQs rendering
- [x] Disclaimer note

### 7. **Main Workflow** ✅
- [x] Keyword file reading
- [x] Delay between posts (12 seconds default)
- [x] Error handling và retry logic
- [x] Summary report
- [x] Logging to file và console

---

## 🎯 LUỒNG HOẠT ĐỘNG CHI TIẾT

```
START
  │
  ├─► 1. Load .env configuration
  │     ├─ WordPress credentials
  │     ├─ Amazon PA-API keys
  │     ├─ Cerebras API keys file
  │     └─ Post settings
  │
  ├─► 2. Initialize components
  │     ├─ CerebrasClient (with key rotation)
  │     ├─ AmazonProductAPI
  │     ├─ AIContentGenerator
  │     └─ WordPressAPI
  │
  ├─► 3. Test WordPress connection
  │     └─ Nếu fail → EXIT
  │
  ├─► 4. Load keywords.txt
  │     └─ Parse từng dòng (bỏ qua # comments)
  │
  ├─► 5. FOR EACH keyword:
  │     │
  │     ├─► Step 1: Amazon PA-API Search
  │     │     ├─ Search 10 products
  │     │     ├─ Extract: ASIN, title, price, image, features
  │     │     └─ If no products → Skip keyword
  │     │
  │     ├─► Step 2: AI Content Generation (Cerebras)
  │     │     ├─ Introduction (prompt + generate)
  │     │     ├─ Badges + Top Recommendation (JSON parsing)
  │     │     ├─ Buying Guide (4-6 sections)
  │     │     └─ FAQs (5-10 Q&A)
  │     │
  │     ├─► Step 3: HTML Building
  │     │     ├─ Intro paragraph
  │     │     ├─ Editor's Choice box
  │     │     ├─ Best-for list
  │     │     ├─ Product comparison cards
  │     │     ├─ Buying guide
  │     │     └─ FAQs (details/summary)
  │     │
  │     ├─► Step 4: WordPress POST
  │     │     ├─ Title: "Comparison: {keyword}"
  │     │     ├─ Content: HTML from Step 3
  │     │     ├─ Status: draft/publish
  │     │     ├─ Author ID: from .env
  │     │     ├─ Category ID: from .env
  │     │     └─ Return: post ID & URL
  │     │
  │     └─► Step 5: Delay (12s default)
  │
  └─► 6. Summary Report
        ├─ Total processed
        ├─ Successful posts
        └─ Failed keywords
END
```

---

## 🔥 ĐIỂM QUAN TRỌNG CẦN LƯU Ý

### **Cerebras API Key Rotation**
- Tự động rotate khi gặp: 429 (rate limit), 401 (unauthorized), 403 (forbidden)
- Exponential backoff: 2s → 4s → 8s → 16s → 30s (max)
- Thử tất cả keys trước khi báo lỗi

### **Amazon PA-API Rate Limits**
- Free tier: 8,640 requests/day (1 request/10s)
- Production: 1 request/second
- Plugin delay 12s giữa các bài → an toàn

### **WordPress REST API**
- Cần Application Password (WordPress 5.6+)
- Endpoint: `https://yoursite.com/wp-json/wp/v2/posts`
- Auth: Basic Auth (username:app_password)

### **Error Handling**
- Mỗi keyword độc lập, fail 1 không ảnh hưởng khác
- Log chi tiết vào `amazon_poster.log`
- Retry logic trong AI generation (3 attempts)

---

## 🧪 CÁCH TEST TRƯỚC KHI CHẠY

### 1. **Setup Environment**
```powershell
# Tạo .env từ template
Copy-Item .env.example .env

# Edit .env với credentials thực
notepad .env
```

### 2. **Chạy Setup Script**
```powershell
.\setup.ps1
```

### 3. **Chạy Test Workflow**
```powershell
python test_workflow.py
```

Nếu tất cả tests PASS → OK để chạy main.py

### 4. **Test với 1 keyword trước**
Tạo `keywords_test.txt`:
```
best coffee maker
```

Sửa `main.py` dòng 267:
```python
keywords_file = 'keywords_test.txt'  # Thay vì 'keywords.txt'
```

Chạy:
```powershell
python main.py
```

### 5. **Kiểm tra kết quả**
- Vào WordPress Admin → Posts
- Xem bài draft/publish vừa tạo
- Kiểm tra format HTML
- Kiểm tra log file: `amazon_poster.log`

---

## ⚠️ POTENTIAL ISSUES & SOLUTIONS

### Issue 1: "Import amazon.paapi could not be resolved"
**Solution:**
```powershell
pip install --upgrade python-amazon-paapi
```

### Issue 2: "WordPress connection failed"
**Checks:**
1. WP_SITE_URL đúng chưa? (không có trailing slash)
2. Application Password còn valid không?
3. WordPress có bật REST API không? (check: `yoursite.com/wp-json`)

### Issue 3: "No products found"
**Possible causes:**
1. Amazon PA-API credentials sai
2. Keyword quá specific
3. Region không match (US keywords cần US region)

### Issue 4: "Cerebras API rate limit"
**Auto-handled:**
- Program tự động rotate sang key tiếp theo
- Nếu tất cả keys đều rate limited → thêm delay hoặc thêm keys

### Issue 5: "JSON parsing error in AI response"
**Handled in code:**
- Multiple JSON extraction strategies
- Manual fix fallback
- 3 retry attempts với different prompts

---

## 📊 EXPECTED PERFORMANCE

**Với 533 keywords:**
- Thời gian/bài: ~30-60 seconds
  - Amazon search: 2-5s
  - AI generation: 15-30s (4 API calls)
  - HTML build: <1s
  - WordPress POST: 1-3s
  - Delay: 12s

- **Total time:** 533 × 50s ≈ **7.4 hours**

**Recommendations:**
- Chạy vào lúc ít traffic
- Monitor CPU/RAM usage
- Kiểm tra WordPress server load
- Có thể chia thành batches nhỏ hơn

---

## ✅ FINAL CHECKLIST TRƯỚC KHI PRODUCTION

- [ ] Đã test với 1-2 keywords thành công
- [ ] WordPress nhận được bài đúng format
- [ ] Tất cả images/links đều hoạt động
- [ ] Categories/Author được set đúng
- [ ] Log file ghi rõ ràng
- [ ] Có backup WordPress trước khi chạy bulk
- [ ] Cerebras API keys đủ quota
- [ ] Amazon PA-API không vượt rate limit
- [ ] Server đủ dung lượng cho 533 bài

---

**STATUS: ✅ SẴN SÀNG PRODUCTION**

Tất cả components đã được kiểm tra và sửa lỗi. Có thể bắt đầu test với 1-2 keywords trước khi chạy full batch.
