# ChatZai API Integration Setup Guide

This guide explains how to use the new ChatZai API integration with automatic Cerebras fallback.

## Overview

The application now uses a **Unified AI Client** that provides:
- 🌐 **ChatZai API** as the primary AI provider (faster, more reliable)
- 🧠 **Cerebras API** as automatic fallback (backup when ChatZai fails)
- 📊 **Statistics tracking** to monitor which provider is being used
- 🔄 **Smart fallback** that automatically switches between providers

## Architecture

```
┌─────────────────────────────────────────────┐
│         AIContentGenerator                   │
│  (generates intro, badges, FAQs, etc.)      │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│         UnifiedAIClient                      │
│  (manages primary + fallback providers)     │
└──────────┬──────────────┬───────────────────┘
           │              │
           ▼              ▼
  ┌─────────────┐  ┌─────────────┐
  │  ChatZai    │  │  Cerebras   │
  │  (Primary)  │  │  (Fallback) │
  └─────────────┘  └─────────────┘
```

## Files Created/Modified

### New Files
1. **chat_zai_client.py** - ChatZai API wrapper
2. **unified_ai_client.py** - Unified client with fallback logic
3. **start_with_api.bat** - Windows batch startup script
4. **start_with_api.ps1** - PowerShell startup script

### Modified Files
1. **ai_generator.py** - Now uses UnifiedAIClient
2. **main.py** - Initializes both providers
3. **.env.example** - Added CHAT_ZAI_API_URL configuration

## Setup Instructions

### Step 1: Install Dependencies

The required `requests` library is already in `requirements.txt`. No additional installation needed.

```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment

Update your `.env` file with the ChatZai API URL:

```env
# Chat.z.ai API Configuration (Primary AI Provider)
CHAT_ZAI_API_URL=http://localhost:3001

# Cerebras AI Configuration (Fallback AI Provider)
CEREBRAS_KEYS_FILE=cerebras_api_keys.txt
CEREBRAS_MODEL=gpt-oss-120b
```

### Step 3: Ensure ChatZai API Server Exists

Make sure you have `chat_zai_api_playwright.js` in your project directory. This file should expose an HTTP API on port 3001.

Required endpoints:
- `GET /health` - Health check (returns 200 OK)
- `POST /ask` - Generate content
  ```json
  {
    "prompt": "user prompt here",
    "systemPrompt": "optional system prompt",
    "maxTokens": 4000,
    "temperature": 0.7
  }
  ```

## Usage

### Option 1: Use Startup Script (Recommended)

**Windows CMD:**
```bash
start_with_api.bat
```

**PowerShell:**
```powershell
.\start_with_api.ps1
```

The startup script will:
1. Check if Node.js and Python are installed
2. Start the ChatZai API server
3. Wait for the server to be healthy
4. Start the Python poster application
5. Clean up when done

### Option 2: Manual Start

**Terminal 1 - Start ChatZai API:**
```bash
node chat_zai_api_playwright.js
```

**Terminal 2 - Start Python Poster:**
```bash
python main.py
```

## How It Works

### Automatic Fallback Logic

```python
1. Check if ChatZai is healthy
   ├─ YES → Use ChatZai
   │        ├─ Success? → Continue with ChatZai
   │        └─ Failed? → Mark unhealthy, fallback to Cerebras
   │
   └─ NO → Use Cerebras directly
             └─ After success, check if ChatZai recovered
```

### Request Flow

```
User Request
    ↓
UnifiedAIClient.generate()
    ↓
ChatZai healthy? ──YES──→ Try ChatZai
    │                         ↓
    NO                    Success? ──YES──→ Return response
    │                         │
    │                        NO
    │                         ↓
    └──────→ Fallback to Cerebras
                   ↓
              Success? ──YES──→ Return response
                   │
                  NO
                   ↓
              Raise Exception
```

## Statistics Tracking

The application tracks usage statistics:

```
AI Provider Statistics:
  Total Requests: 10
  ChatZai Success: 8
  ChatZai Failed: 2
  Cerebras Success: 2
  Cerebras Failed: 0
  Overall Success Rate: 100.0%
  ChatZai Health: ✓ Healthy
```

Statistics are printed at the end of each run.

## Troubleshooting

### ChatZai API Not Starting

**Error:** `[ERROR] API server failed to start`

**Solution:**
- Check if port 3001 is already in use
- Ensure `chat_zai_api_playwright.js` exists
- Check Node.js is installed: `node --version`
- Manually start API: `node chat_zai_api_playwright.js`

### All Requests Using Cerebras

**Symptom:** Logs show "ChatZai unhealthy, using Cerebras directly"

**Possible Causes:**
1. ChatZai API server not running
2. Wrong URL in `.env` (check `CHAT_ZAI_API_URL`)
3. Firewall blocking localhost:3001
4. ChatZai server crashed

**Solution:**
- Verify API is running: `curl http://localhost:3001/health`
- Check API server logs for errors
- Restart API server

### Connection Timeout

**Error:** `Request timeout after 60s`

**Solution:**
- Increase timeout in `main.py`:
  ```python
  self.chat_zai = ChatZaiClient(
      api_url=chat_zai_url,
      timeout=120,  # Increase to 120 seconds
      max_retries=3
  )
  ```

### Both Providers Failing

**Error:** `Both AI providers failed`

**Solution:**
1. Check ChatZai API server is running
2. Verify Cerebras API keys are valid
3. Check internet connection
4. Review logs for specific error messages

## Configuration Options

### ChatZaiClient Options

```python
ChatZaiClient(
    api_url="http://localhost:3001",  # API server URL
    timeout=60,                        # Request timeout in seconds
    max_retries=3                      # Number of retry attempts
)
```

### UnifiedAIClient Features

- Automatic health checks
- Smart fallback on errors
- Statistics tracking
- Retry logic with exponential backoff

## Testing

### Test ChatZai API Only

```python
from chat_zai_client import ChatZaiClient

client = ChatZaiClient()
if client.health_check():
    response = client.generate("Write a short intro about air fryers")
    print(response)
```

### Test Unified Client

```python
from chat_zai_client import ChatZaiClient
from cerebras_client import CerebrasClient
from unified_ai_client import UnifiedAIClient

chat_zai = ChatZaiClient()
cerebras = CerebrasClient(api_keys_file="cerebras_api_keys.txt")
unified = UnifiedAIClient(chat_zai, cerebras)

response = unified.generate("Write a short intro about air fryers")
print(response)
unified.print_stats()
```

## Benefits

✅ **Faster Content Generation** - ChatZai API is typically faster than direct API calls

✅ **Higher Reliability** - Automatic fallback ensures content generation never fails

✅ **Cost Optimization** - Use ChatZai primarily, save Cerebras for backup

✅ **Better Monitoring** - Statistics show which provider is being used

✅ **Zero Downtime** - Seamless switching between providers

## Next Steps

1. Monitor the statistics to see provider usage patterns
2. Adjust timeout and retry settings based on your needs
3. Consider adding more AI providers to the unified client
4. Set up monitoring/alerts for when fallback is used frequently

---

**Questions or Issues?** Check the main README.md or review the logs in `amazon_poster.log`
