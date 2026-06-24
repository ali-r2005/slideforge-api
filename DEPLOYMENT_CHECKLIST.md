# SlideForge API - Render Deployment Checklist ✅

## Pre-Deployment Setup

### 1. **Python Dependencies** ✅
- [x] `requirements.txt` exists with all Python packages
- [x] Core packages included:
  - `fastapi` - Web framework
  - `uvicorn` - ASGI server
  - `pydantic` - Data validation
  - `python-pptx` - PowerPoint generation
  - `langchain-openai` - AI integration
  - `python-dotenv` - Environment variables

### 2. **System Dependencies** ✅
- [x] **LibreOffice** - Required for PDF/PNG conversion
  - Installed via `build.sh` script
  - Packages: `libreoffice`, `libreoffice-writer`, `libreoffice-calc`, `libreoffice-impress`
  - Font dependencies: `fonts-liberation`, `fonts-dejavu`, `libfreetype6`

### 3. **Render Configuration Files** ✅
- [x] **Procfile** - Defines how to start the application
  - Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [x] **render.yaml** - Render-specific configuration
  - Build command: `bash build.sh`
  - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Python version: 3.11.10
- [x] **runtime.txt** - Specifies Python version
  - Version: 3.11.10
- [x] **build.sh** - Custom build script for system dependencies
  - Installs LibreOffice and fonts
  - Creates required directories

### 4. **Environment Variables** ⚠️ NEEDS CONFIGURATION
**You must set these in Render's dashboard under Environment Groups:**

```
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=qwen/qwen-2.5-72b-instruct
PEXELS_API_KEY=your_pexels_api_key_here
LOGO_DEV_PUBLIC_KEY=your_logo_dev_public_key_here
```

**How to add them:**
1. Go to your Render dashboard
2. Find the service "slideforge-api"
3. Click "Environment" tab
4. Create an environment group named `slideforge-api-env`
5. Add the variables above
6. Deploy again

### 5. **Directory Structure** ✅
Required directories (created by `build.sh`):
- [x] `public/thumbnails/` - Stores template thumbnails
- [x] `generated/` - Stores generated PPTX files
- [x] `temp_images/` - Temporary image storage during processing
- [x] `templates/` - Your PPTX template files (should be in repo)
- [x] `DB/` - Database files for select fields

### 6. **CORS Configuration** ✅
- [x] FastAPI CORS middleware configured
- [x] Allows `http://localhost:3000` (for local dev)
- **⚠️ TODO:** Update `app/main.py` line 16 to add your production frontend URL:
  ```python
  allow_origins=["http://localhost:3000", "https://your-frontend-domain.com"]
  ```

### 7. **Port Configuration** ✅
- [x] App binds to `0.0.0.0` (all interfaces)
- [x] Port comes from `$PORT` environment variable
- [x] Render automatically assigns and manages the port

### 8. **File Cleanup** ✅
- [x] `cleanup_temp_images()` called after presentation generation
- [x] Temporary files in `temp_images/` are cleaned up

### 9. **Error Handling** ✅
- [x] LibreOffice not found error is handled gracefully
- [x] API returns proper HTTP exceptions with error messages

---

## Deployment Steps

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Add Render deployment configuration"
git push
```

### Step 2: Connect to Render
1. Go to [render.com](https://render.com)
2. Sign in with your GitHub account
3. Click "New +" → "Web Service"
4. Select your SlideForge repository
5. Configure:
   - **Name:** `slideforge-api`
   - **Environment:** `Python 3`
   - **Build Command:** `bash build.sh`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Standard (recommended for production)

### Step 3: Set Environment Variables
1. In Render dashboard, go to your service
2. Click "Environment" tab
3. Create a new environment group: `slideforge-api-env`
4. Add all variables from section 4 above
5. Click "Deploy" to start deployment

### Step 4: Monitor Deployment
- Logs appear in real-time
- Wait for "✓ Deploy successful" message
- Your API will be available at: `https://your-service-name.onrender.com`

---

## Testing After Deployment

### Test 1: Health Check
```bash
curl https://your-service-name.onrender.com/templates
```
Should return: `{"success": true, "data": [...]}`

### Test 2: Get Metadata (requires template)
```bash
curl https://your-service-name.onrender.com/metadata/template1
```

### Test 3: Generate Presentation
```bash
curl -X POST https://your-service-name.onrender.com/api/v1/generate-ppt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a business presentation", "template": "template1.pptx"}'
```

---

## Common Issues & Fixes

### ❌ LibreOffice not found
**Cause:** System packages not installed during build
**Fix:** Make sure `build.sh` is in the root directory and render.yaml points to it

### ❌ PORT environment variable not set
**Cause:** App tries to use hardcoded port
**Fix:** Already fixed - app uses `$PORT` from Render environment

### ❌ CORS error from frontend
**Cause:** Frontend domain not in allow_origins
**Fix:** Update `app/main.py` line 16 with your frontend domain

### ❌ Missing environment variables
**Cause:** Variables not set in Render dashboard
**Fix:** Add them via Render's Environment Groups (see step 3)

### ❌ PDF conversion fails
**Cause:** LibreOffice not installed
**Fix:** Ensure `build.sh` runs successfully (check deployment logs)

---

## File Checklist

**Created/Updated files:**
- ✅ `Procfile` - Process definition
- ✅ `render.yaml` - Render configuration
- ✅ `runtime.txt` - Python version
- ✅ `build.sh` - Build script with system dependencies
- ✅ `requirements.txt` - All dependencies
- ✅ `main.py` - Root entry point (created earlier)
- ✅ `app/main.py` - FastAPI app with CORS
- ✅ `app/api/v1/endpoints.py` - API endpoints

**Still needed (optional but recommended):**
- `.gitignore` - Already exists
- `README.md` - Already exists
- `.env.example` - Already exists (reference only)

---

## Production Recommendations

1. **Upgrade Python version** if needed (currently 3.11.10)
2. **Enable HTTPS** (automatic on Render)
3. **Set up monitoring/logging** (Render provides basic logs)
4. **Configure a custom domain** instead of `*.onrender.com`
5. **Add rate limiting** for API endpoints
6. **Set up health checks** for auto-recovery
7. **Enable auto-deploys** on GitHub push

---

## Quick Start Command

After all files are created and pushed:
```bash
# In Render dashboard:
# 1. Select service "slideforge-api"
# 2. Click "Manual Deploy" → "Deploy latest commit"
# 3. Wait for build to complete
# 4. Your API is live! 🚀
```

---

**Status:** Ready to deploy! All configuration files are in place.
**Next Step:** Add environment variables to Render and deploy.
