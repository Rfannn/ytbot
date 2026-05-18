# 🎬 Bale YouTube Downloader - Python Version

A **serverless YouTube downloader bot** for Bale Messenger, powered by **Python + Flask + yt-dlp**, running on **PythonAnywhere**.

No GitHub Actions needed. No dedicated servers. Just **one simple Python app**.

---

## ✨ Features

- ✅ **Direct YouTube Download**: Send a link, get the file
- ✅ **Quality Selection**: 480p, 720p, 1080p, audio-only
- ✅ **Auto Subtitles**: Download Farsi & English captions
- ✅ **Rate Limiting**: Fair use (5 min between downloads)
- ✅ **User Settings**: Save preferences (quality, subtitles)
- ✅ **Persistent Database**: SQLite for user data
- ✅ **Simple Setup**: Flask app on PythonAnywhere
- ✅ **Bilingual**: Farsi & English interface
- ✅ **Zero Dependencies**: Only Flask, yt-dlp, requests

---

## 🚀 Quick Start

### Prerequisites
- PythonAnywhere account (free tier works!)
- Bale Bot token
- 15 minutes

### Deploy in 5 Steps

1. **Create PythonAnywhere account**: https://www.pythonanywhere.com
2. **Upload files** to `/home/your-username/youtube-downloader/`
3. **Create web app** with Python 3.10 + virtual environment
4. **Set environment variables**:
   - `BALE_BOT_TOKEN` = your bot token
   - `WEBHOOK_URL` = https://your-username.pythonanywhere.com/webhook
5. **Set Bale webhook**: 
   ```
   https://tapi.bale.ai/botYOUR_TOKEN/setWebhook?url=https://your-username.pythonanywhere.com/webhook
   ```

**See `DEPLOYMENT_GUIDE.md` for detailed instructions.**

---

## 📁 Project Structure

```
python_bot/
├── app.py                   # Flask application
├── config.py                # Settings & environment
├── database.py              # SQLite management
├── downloader.py            # yt-dlp wrapper
├── bot_handler.py           # Bale message handling
├── wsgi.py                  # PythonAnywhere WSGI
├── requirements.txt         # Python dependencies
├── DEPLOYMENT_GUIDE.md      # Setup instructions
└── temp_files/              # Downloaded files (auto-created)
```

---

## 🔧 Architecture

```
Bale Messenger
    ↓
Webhook → Flask App (PythonAnywhere)
    ↓
yt-dlp (download video)
    ↓
SQLite (rate limits, settings)
    ↓
Send file back to Bale
```

---

## 📝 Usage

### User Commands

| Command | Action |
|---------|--------|
| `/start` | Show welcome & help |
| `/settings` | Change quality & subtitles |
| Send YouTube URL | Start download |

### Quality Options

| Quality | Resolution | Notes |
|---------|-----------|-------|
| 🔊 Audio | MP3 | Music only |
| 📱 SD | 480p | Mobile-friendly |
| 📺 HD | 720p | Good quality |
| 🎬 Full HD | 1080p | High quality |
| ✨ Best | Auto | Highest available |

---

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Rate limiting (seconds)
RATE_LIMIT_SECONDS = 300  # 5 minutes

# File retention (seconds)
MAX_FILE_AGE_SECONDS = 300  # 5 minutes

# Quality options (edit QUALITY_OPTIONS dict)
QUALITY_OPTIONS = {
    '1': {'label': '🔊 فقط صدا', 'value': 'audio'},
    '2': {'label': '📱 480p', 'value': '480'},
    # ...
}

# Messages (add more languages if needed)
MESSAGES = {
    'start': {'fa': '...', 'en': '...'},
    # ...
}
```

---

## 📊 Database Schema

### rate_limits
```sql
chat_id TEXT PRIMARY KEY
last_request_time INTEGER
```

### user_settings
```sql
chat_id TEXT PRIMARY KEY
quality TEXT DEFAULT 'best'
subtitles BOOLEAN DEFAULT 0
language TEXT DEFAULT 'fa'
```

### file_cache
```sql
id INTEGER PRIMARY KEY
chat_id TEXT
file_id TEXT
file_name TEXT
file_path TEXT
file_size INTEGER
youtube_url TEXT
created_at INTEGER
```

---

## 🔐 Security

- **Rate Limiting**: Prevents abuse (5 min between downloads)
- **Update Deduplication**: Prevents double-processing
- **File Size Limits**: 45 MB max (respects Bale limits)
- **Token in Environment**: Never commit secrets
- **Persistent Storage**: SQLite (local, encrypted by PythonAnywhere)

---

## 🛠️ Deployment Options

### ✅ PythonAnywhere (Recommended)
- **Pros**: Free tier, always running, SSL included
- **Cons**: Limited CPU (100s/day free tier)
- **Best for**: Personal use, testing

### Other Options
- **Heroku**: Free tier discontinued (use paid)
- **Render**: Similar to PythonAnywhere
- **Railway**: Similar to Heroku
- **Your VPS**: Full control, pay for hosting

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| **Download Time** | 30s - 5min (depends on file size) |
| **Rate Limit** | 5 min between users |
| **File Size Max** | 45 MB |
| **Supported Formats** | MP4, MP3, WebM, etc |
| **Database Size** | ~1 MB (growing slowly) |
| **PythonAnywhere** | Handles ~10-20 downloads/day free |

---

## 🐛 Troubleshooting

### Bot not responding?
- Check webhook: `https://tapi.bale.ai/botYOUR_TOKEN/getWebhookInfo`
- Reload web app on PythonAnywhere
- Check error logs: **Web** → **Log files**

### "yt-dlp not found"?
- Install in virtual environment: `pip install yt-dlp`
- Make sure virtualenv is activated

### Download too slow?
- Use lower quality (480p instead of 1080p)
- Try at off-peak times
- Consider upgrading PythonAnywhere plan

### File size error?
- Only download videos < 45 MB
- Use audio-only format
- Split large videos manually

---

## 🚀 Advanced Features (Optional)

### Add Search Function
Uncomment search routes in `app.py` and `bot_handler.py`

### Custom Formats
Add more formats to `QUALITY_FORMAT_MAP` in `downloader.py`

### Multiple Bot Accounts
Create multiple folders, one per bot token

### Webhooks Monitoring
Add logging to Telegram or Discord for errors

---

## 📚 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Flask | 2.3.3 | Web framework |
| yt-dlp | 2025.01.15 | YouTube downloader |
| requests | 2.31.0 | HTTP library |

Install: `pip install -r requirements.txt`

---

## 📄 License

MIT License - Feel free to use and modify!

---

## 🤝 Contributing

Found a bug or want to add a feature?

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

---

## 📞 Support

- **Issues**: GitHub Issues
- **Questions**: Bale Chat (link your bot)
- **Suggestions**: GitHub Discussions

---

## 🎯 Roadmap

- [ ] Search functionality
- [ ] Playlist downloads
- [ ] Video preview
- [ ] Download history
- [ ] Admin commands
- [ ] Multi-language support

---

## ⚖️ Legal Notice

This bot is for **personal use only**. Respect YouTube's Terms of Service and copyright laws. Use responsibly!

---

## 🌟 Credits

Built with ❤️ for Bale Messenger users.

Made possible by:
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [Flask](https://flask.palletsprojects.com/)
- [PythonAnywhere](https://www.pythonanywhere.com/)

---

**Ready to deploy? See `DEPLOYMENT_GUIDE.md` →**
