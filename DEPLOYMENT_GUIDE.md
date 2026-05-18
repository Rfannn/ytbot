# 🎬 Bale YouTube Downloader Bot - Deployment Guide

## Deploy on PythonAnywhere (Free Tier)

This guide will help you deploy the Python bot on PythonAnywhere.

---

## Prerequisites

- PythonAnywhere free account (https://www.pythonanywhere.com)
- Bale Bot token (from @BotFather in Bale)
- About 15 minutes

---

## Step 1: Create PythonAnywhere Account

1. Go to https://www.pythonanywhere.com
2. Sign up with free tier account
3. Verify your email
4. Log in to your account

---

## Step 2: Upload Files to PythonAnywhere

### Option A: Using Web Interface
1. Go to **Files** tab in PythonAnywhere
2. Create new folder: `/home/your-username/youtube-downloader`
3. Upload all these files:
   - `app.py`
   - `config.py`
   - `database.py`
   - `downloader.py`
   - `bot_handler.py`
   - `wsgi.py`
   - `requirements.txt`

### Option B: Using Bash Console
1. Go to **Bash** console
2. Run these commands:

```bash
# Create directory
mkdir ~/youtube-downloader
cd ~/youtube-downloader

# You can use git clone if you have a repo
# OR manually upload files via web interface
```

---

## Step 3: Create Virtual Environment & Install Dependencies

1. Go to **Bash** console
2. Run:

```bash
cd ~/youtube-downloader

# Create virtual environment
mkvirtualenv --python=/usr/bin/python3.10 youtube-dl
workon youtube-dl

# Install dependencies
pip install -r requirements.txt
```

**Note:** This may take 2-3 minutes.

---

## Step 4: Configure Web App

1. Go to **Web** tab
2. Click **Add a new web app**
3. Choose **Manual configuration**
4. Select **Python 3.10** (or latest available)
5. Click **Next**

### Configure WSGI

1. Scroll down to **Code** section
2. Click on **WSGI configuration file**
3. Replace the content with this:

```python
import sys
path = '/home/your-username/youtube-downloader'
if path not in sys.path:
    sys.path.insert(0, path)

from app import app
application = app
```

**Replace `your-username` with your actual PythonAnywhere username**

### Configure Virtual Environment

1. Scroll down to **Virtualenv** section
2. Set to: `/home/your-username/.virtualenvs/youtube-dl`
3. Click checkbox to activate

### Configure Static Files
(Skip static files - we don't use any)

---

## Step 5: Set Environment Variables

1. Go to **Web** tab
2. Scroll to **Environment variables** section
3. Add these variables:

| Name | Value | Notes |
|------|-------|-------|
| `BALE_BOT_TOKEN` | Your bot token | From @BotFather |
| `WEBHOOK_URL` | `https://your-username.pythonanywhere.com/webhook` | Your app URL |
| `PYTHONANYWHERE` | `true` | Signals PythonAnywhere environment |

---

## Step 6: Test the Web App

1. Scroll back to **Web** tab
2. Click **Reload**
3. Wait 10-15 seconds
4. Visit your URL: `https://your-username.pythonanywhere.com`
5. You should see:
```json
{
    "name": "🎬 Bale YouTube Downloader Bot",
    "status": "running"
}
```

### Test Health Check
Visit: `https://your-username.pythonanywhere.com/health`

You should see:
```json
{
    "ok": true,
    "status": "healthy",
    "bot_token": true,
    "database": true,
    "temp_dir": true
}
```

---

## Step 7: Configure Bale Webhook

Now tell Bale to send updates to your app.

### Get Your Webhook URL
Your webhook URL is: `https://your-username.pythonanywhere.com/webhook`

### Set Webhook in Bale
Send a request to set the webhook. You can use:

**Option A: Browser (easiest)**
```
https://tapi.bale.ai/botYOUR_BOT_TOKEN/setWebhook?url=https://your-username.pythonanywhere.com/webhook
```

Replace `YOUR_BOT_TOKEN` with your actual bot token, then paste in browser.

**Option B: Using curl in Bash**
```bash
curl -X POST "https://tapi.bale.ai/botYOUR_BOT_TOKEN/setWebhook" \
  -d "url=https://your-username.pythonanywhere.com/webhook"
```

**Option C: Using Python**
```python
import requests

TOKEN = "YOUR_BOT_TOKEN"
WEBHOOK_URL = "https://your-username.pythonanywhere.com/webhook"

url = f"https://tapi.bale.ai/bot{TOKEN}/setWebhook"
response = requests.post(url, data={"url": WEBHOOK_URL})
print(response.json())
```

You should get:
```json
{
    "ok": true,
    "result": true
}
```

---

## Step 8: Test the Bot

1. Open Bale messenger
2. Find your bot
3. Send `/start`
4. Bot should respond with welcome message
5. Send a YouTube URL
6. Bot should offer quality options
7. Select quality and download should start!

---

## Troubleshooting

### "ModuleNotFoundError" errors
- **Solution**: Check virtual environment is activated
  ```bash
  workon youtube-dl
  pip list  # Should show Flask, yt-dlp, requests
  ```

### Bot not responding
- **Check webhook**: Visit `https://tapi.bale.ai/botYOUR_TOKEN/getWebhookInfo`
- **Check logs**: Go to **Web** → **Log files** → view error log
- **Reload app**: Go to **Web** → Click **Reload**

### Download fails with "yt-dlp not found"
- **Solution**: yt-dlp must be installed globally or in virtualenv
  ```bash
  workon youtube-dl
  pip install --upgrade yt-dlp
  ```

### "BALE_BOT_TOKEN environment variable not set"
- **Solution**: Check you added the environment variable in Web tab
- **Reload** the app after adding

### File size too large
- **Note**: PythonAnywhere free tier limits file size
- **Solution**: Download lower quality (480p or audio)

### Slow downloads
- **Note**: Free tier has limited resources
- **Solution**: Use lower quality or be patient

---

## File Structure on PythonAnywhere

```
/home/your-username/youtube-downloader/
├── app.py                  # Main Flask app
├── config.py               # Configuration
├── database.py             # SQLite management
├── downloader.py           # yt-dlp wrapper
├── bot_handler.py          # Bot logic
├── wsgi.py                 # WSGI entry point
├── requirements.txt        # Dependencies
├── bot_database.db         # Auto-created SQLite DB
└── temp_files/             # Auto-created temp directory
    ├── video1.mp4
    ├── video2.mp3
    └── ...
```

---

## Useful Commands

### Access Bash Console
```bash
# Activate environment
workon youtube-dl

# Check Python version
python --version

# Check installed packages
pip list

# Update packages
pip install --upgrade yt-dlp

# View logs
tail -f /var/log/your-username_pythonanywhere_com.log
```

---

## PythonAnywhere Free Tier Limits

- **Storage**: 512 MB
- **CPU**: 100 seconds/day
- **Concurrent tasks**: 1
- **Threads**: Limited
- **External APIs**: Can't make requests to other APIs... wait, we can! ✅

### File Size Limits
- Video files in Bale: ~50 MB max
- We split files > 45 MB automatically
- Temp files deleted after 5 minutes

---

## Free Tier Considerations

✅ **Works great for**:
- Personal use
- Testing
- Light to medium use (few downloads/day)

⚠️ **May be slow**:
- During peak hours (5-8 PM UTC)
- With large file downloads
- With 4K video quality

✅ **What's included**:
- 24/7 uptime (app always running)
- Free SSL certificate
- No credit card needed
- Unlimited downloads (within CPU limits)

---

## Upgrade to Paid (Optional)

If you exceed free tier limits:
1. Go to **Account** → **Billing**
2. Upgrade plan (starts at $5/month)
3. Gets you:
   - Unlimited storage
   - Unlimited CPU
   - Better performance
   - Custom domain support

---

## Next Steps

1. ✅ Test bot with a simple YouTube link
2. ✅ Send `/settings` to customize
3. ✅ Try different qualities (480p, 720p, 1080p, audio)
4. ✅ Enable subtitles in settings
5. ✅ Invite friends to use the bot

---

## Getting Help

If something doesn't work:

1. **Check logs**: Go to **Web** → **Log files**
2. **Check webhook**: `https://tapi.bale.ai/botYOUR_TOKEN/getWebhookInfo`
3. **Test manually**: 
   ```bash
   curl -X POST https://your-username.pythonanywhere.com/webhook \
     -H "Content-Type: application/json" \
     -d '{"update_id": 1, "message": {"chat": {"id": 123}, "text": "/start"}}'
   ```

---

## Summary

You now have a **fully functional YouTube downloader bot** running 24/7 on PythonAnywhere! 🎉

- Send YouTube URLs
- Select quality
- Download automatically
- Rate limited for fair use
- Works offline (no GitHub Actions needed)

Enjoy! 🚀
