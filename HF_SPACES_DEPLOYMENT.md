# Deploy SlideForge API on Hugging Face Spaces 🚀

## Why Hugging Face Spaces?

✅ **Free forever** - No credit card needed  
✅ **Persistent storage** - Generated files don't disappear  
✅ **LibreOffice support** - Full system package installation  
✅ **Easy deployment** - Connect GitHub repo directly  
✅ **Good performance** - More generous resources than Render Free  
✅ **Community-friendly** - Share your project with others  

---

## Prerequisites

1. **GitHub account** (to connect your repo)
2. **Hugging Face account** (free at [huggingface.co](https://huggingface.co))
3. Your SlideForge repo pushed to GitHub

---

## Step 1: Push Code to GitHub

```bash
cd ~/Desktop/SlideForge/slideforge-api
git add .
git commit -m "Add Hugging Face Spaces deployment configuration"
git push origin main
```

**Files that will be deployed:**
- ✅ `Dockerfile` (Docker configuration)
- ✅ `requirements.txt` (Python packages)
- ✅ `app/` (Your FastAPI application)
- ✅ `templates/` (PPTX templates)
- ✅ `DB/` (Database files)

---

## Step 2: Create a New Hugging Face Space

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Fill in the form:
   - **Space name:** `slideforge-api` (or any name)
   - **License:** Choose one (e.g., MIT)
   - **Space SDK:** Select **"Docker"**
   - **Visibility:** Public (or Private if you prefer)

4. Click **"Create Space"**

---

## Step 3: Configure GitHub Connection

On the new Space page:

1. Click **Files** tab
2. Click **"Add file"** → **"Clone from Git repository"**
3. Enter your GitHub repo URL:
   ```
   https://github.com/YOUR_USERNAME/SlideForge.git
   ```
4. Click **"Clone repository"**

**Note:** Make sure:
- Your GitHub repo is public (or authenticate with token)
- The `Dockerfile` is in the root of `slideforge-api` directory

---

## Step 4: Set Environment Variables

1. In your Space, click **Settings** (gear icon)
2. Go to **Secrets & Environment Variables** tab
3. Add these variables:

| Name | Value |
|------|-------|
| `OPENROUTER_API_KEY` | your_api_key_here |
| `OPENROUTER_MODEL` | qwen/qwen-2.5-72b-instruct |
| `PEXELS_API_KEY` | your_api_key_here |
| `LOGO_DEV_PUBLIC_KEY` | your_api_key_here |

4. Click **"Save"** - the Space will automatically restart

---

## Step 5: Monitor Deployment

1. Click **"Logs"** tab to watch the build
2. Docker image will build (takes 5-10 minutes first time)
3. Wait for message: **"Successfully served ... at http://..."**
4. Your API is live! 🎉

---

## Accessing Your API

Once deployed, your API will be available at:

```
https://huggingface.co/spaces/YOUR_USERNAME/slideforge-api
```

### Get API Endpoint

The actual API runs at the app URL. To find it:
1. Go to your Space
2. Click the **app** link or URL shown
3. Your FastAPI docs will be at: `https://[YOUR-SPACE-URL]/docs`

### API Base URL Format

```
https://[your-username]-slideforge-api.hf.space
```

---

## Testing Your Deployment

### Test 1: Check API is Running
```bash
curl https://[your-username]-slideforge-api.hf.space/templates
```

**Expected response:**
```json
{"success": true, "data": [...]}
```

### Test 2: Get Template Metadata
```bash
curl https://[your-username]-slideforge-api.hf.space/metadata/template1
```

### Test 3: Generate a Presentation
```bash
curl -X POST https://[your-username]-slideforge-api.hf.space/api/v1/generate-ppt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a business presentation about AI",
    "template": "template1.pptx"
  }'
```

---

## Update Your Frontend

Update your React frontend to use the new API URL:

**Before (localhost):**
```javascript
const API_URL = "http://localhost:8000";
```

**After (HF Spaces):**
```javascript
const API_URL = "https://[your-username]-slideforge-api.hf.space";
```

Or use environment variable:
```javascript
const API_URL = process.env.REACT_APP_API_URL || "https://[your-username]-slideforge-api.hf.space";
```

---

## File Structure on HF Spaces

Your Space will have:

```
/
├── Dockerfile              ✅ (tells HF how to build)
├── requirements.txt        ✅ (Python packages)
├── app/                    ✅ (FastAPI app)
│   ├── main.py
│   ├── api/
│   ├── services/
│   ├── utils/
│   └── schemas/
├── templates/              ✅ (PPTX files)
├── DB/                     ✅ (Database files)
├── public/                 (created at runtime)
├── generated/              (created at runtime)
└── temp_images/            (created at runtime)
```

---

## Important Notes

### Storage Limits
- **Free tier:** 50 GB persistent storage (more than enough)
- Generated files persist even if Space restarts
- Old files are not auto-deleted (clean up manually if needed)

### Performance
- **CPU:** 2 vCPU (shared)
- **Memory:** 16 GB RAM (shared, but generous)
- **Start time:** ~2-3 minutes for new build
- **Inactivity:** Space doesn't auto-pause on free tier (stays on!)

### Automatic Updates
- Set **"Automatically restart this Space"** if you want auto-redeploy on GitHub push
- Without it, manually click **"Restart this Space"** in Settings

---

## Updating Your Deployment

To push updates to HF Spaces:

### Option 1: Auto-Deploy (Recommended)
1. In Space Settings, enable **"Persistent Storage"**
2. Enable **"Auto-restart"** (optional)
3. Just push to GitHub - Space auto-updates

### Option 2: Manual Deploy
```bash
git push origin main
# Then in HF Spaces Settings → click "Restart Space"
```

---

## Troubleshooting

### ❌ Build fails with "Dockerfile not found"
**Solution:** Make sure `Dockerfile` is in root of `slideforge-api/`, not inside `app/`

### ❌ LibreOffice fails to install
**Solution:** Check logs - may need to adjust apt-get packages. Let me know and I'll fix.

### ❌ API returns 500 error
**Solution:** 
1. Check Logs in Space
2. Verify all env variables are set
3. Make sure templates are in `templates/` folder

### ❌ Generated files disappear
**Solution:** Enable "Persistent Storage" in Space Settings

### ❌ API times out during PDF generation
**Solution:** HF Spaces has generous timeout. If this happens, may need to optimize LibreOffice or add caching.

---

## Comparison: HF Spaces vs Render vs Vercel

| Feature | HF Spaces | Render Free | Vercel |
|---------|-----------|------------|--------|
| Free tier | ✅ Unlimited | ✅ Limited | ✅ Limited |
| Credit card | ❌ No | ⚠️ Optional | ⚠️ Optional |
| LibreOffice | ✅ Yes | ✅ Slow | ❌ Timeout |
| Persistent storage | ✅ 50GB | ✅ Limited | ❌ Ephemeral |
| Auto-pause | ❌ No (stays on) | ⚠️ 15 min idle | N/A |
| Setup difficulty | Easy | Easy | Medium |
| Performance | Good | Good | Poor for this |
| Best for | Your use case | Similar | Frontend only |

---

## Summary

✅ **Dockerfile created** - Ready to deploy  
✅ **Requirements.txt exists** - All dependencies listed  
✅ **app/main.py ready** - FastAPI app configured  

**Next steps:**
1. Push to GitHub
2. Create HF Space with Docker
3. Set environment variables
4. Watch build complete (~10 min)
5. Your API is live! 🚀

---

## Quick Commands

```bash
# Push to GitHub
git add .
git commit -m "Ready for HF Spaces deployment"
git push origin main

# After HF Space is set up, monitor logs:
# (In HF Spaces UI → Logs tab)

# Test API is working:
curl https://[username]-slideforge-api.hf.space/templates
```

---

**Questions?** Check the logs in HF Spaces for detailed error messages.  
**Ready?** Let's deploy! 🚀
