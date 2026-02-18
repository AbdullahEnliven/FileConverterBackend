# File Converter Application - Updated Version

## 🎨 Major Updates

### 1. New Feature: Image to SVG Converter
- **Backend Service**: `image_to_svg.py` - Converts raster images to vector SVG format using potrace
- **Frontend Component**: `ImageToSVGConverter.tsx` - Beautiful UI with purple/blue gradient theme
- **API Endpoint**: `/api/convert/image-to-svg`
- **Requires**: potrace system package (automatically installed in Docker)

### 2. Updated Color Scheme
Completely redesigned to match **enlivensai.com** color palette:
- **Deep Navy Blue Background**: `#1a2942` / `#1e3a5f`
- **Purple/Violet Accents**: `#8b5cf6` / `#a855f7`  
- **Bright Blue Gradients**: `#3b82f6` / `#5b9fff`
- **Cyan/Teal Highlights**: `#06b6d4` / `#22d3ee`

All UI components, buttons, gradients, and effects updated to match this theme.

---

## 📦 Installation & Deployment

### Backend Changes Required

#### 1. Add New Files to Backend Directory
Copy these files to your `FileConverterBackend-main` directory:
- `image_to_svg.py` - New converter service
- `main.py` (replace with `main_updated.py`) - Updated with new endpoint
- `requirements.txt` (replace with `requirements_updated.txt`) - Same as before, no new Python packages
- `Dockerfile` (replace with `Dockerfile_updated`) - Added potrace installation

#### 2. Updated Dockerfile (Critical for SVG Conversion)
The new Dockerfile includes potrace installation:
```dockerfile
RUN apt-get update && apt-get install -y \
    ...existing packages... \
    potrace \  # NEW: Required for image to SVG conversion
 && rm -rf /var/lib/apt/lists/*
```

### Frontend Changes Required

#### 1. Add New Files to Frontend Directory
Copy these files to your frontend `src` directory:
- `src/pages/tools/ImageToSVGConverter.tsx` - New tool page
- `src/index.css` (replace with `index_updated.css`) - Updated color scheme
- `src/App.tsx` (replace with `App_updated.tsx`) - Added new route
- `src/data/tools.ts` (replace with `tools_updated.ts`) - Added tool to list

#### 2. File Structure
```
src/
├── pages/
│   └── tools/
│       └── ImageToSVGConverter.tsx  ← NEW FILE
├── data/
│   └── tools.ts                      ← REPLACE
├── App.tsx                            ← REPLACE
└── index.css                          ← REPLACE
```

---

## 🚀 Deployment Options

### Option 1: Railway Deployment (Recommended)

1. **Push Backend to Railway**:
   ```bash
   cd FileConverterBackend-main
   # Railway will automatically detect Dockerfile and build
   railway up
   ```

2. **Environment Variables**:
   - Railway automatically sets `PORT` environment variable
   - No additional configuration needed

3. **Get Backend URL**:
   - Railway will provide a public URL like `https://your-app.railway.app`
   - Update frontend `.env` file:
     ```
     VITE_API_URL=https://your-app.railway.app
     ```

### Option 2: Self-Hosted Server

#### Backend Deployment

1. **Install System Dependencies**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y \
     libreoffice \
     ffmpeg \
     ghostscript \
     potrace \
     python3 \
     python3-pip
   ```

2. **Install Python Packages**:
   ```bash
   cd FileConverterBackend-main
   pip3 install -r requirements.txt
   ```

3. **Run with systemd** (Production):
   Create `/etc/systemd/system/file-converter.service`:
   ```ini
   [Unit]
   Description=File Converter Backend
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/path/to/FileConverterBackend-main
   Environment="PORT=5000"
   ExecStart=/usr/bin/python3 main.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start:
   ```bash
   sudo systemctl enable file-converter
   sudo systemctl start file-converter
   ```

4. **Nginx Reverse Proxy** (Optional but recommended):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           
           # Important for file uploads
           client_max_body_size 500M;
       }
   }
   ```

#### Frontend Deployment

1. **Update API URL**:
   Create `.env` file:
   ```
   VITE_API_URL=http://your-server-ip:5000
   # or
   VITE_API_URL=https://api.yourdomain.com
   ```

2. **Build**:
   ```bash
   npm install
   npm run build
   ```

3. **Deploy**:
   - Copy `dist` folder to web server (Nginx, Apache)
   - Or use Netlify/Vercel for frontend hosting

---

## 🧪 Testing the New Feature

### Test Image to SVG Converter

1. **Backend Health Check**:
   ```bash
   curl http://localhost:5000/health
   ```

2. **Test SVG Conversion**:
   ```bash
   curl -X POST http://localhost:5000/api/convert/image-to-svg \
     -F "file=@test-image.png" \
     -o response.json
   ```

3. **Frontend Testing**:
   - Navigate to `/tools/image-to-svg`
   - Upload a simple image (logo, icon)
   - Download the resulting SVG file
   - Open in browser or vector editor (Inkscape, Illustrator)

### Best Images for SVG Conversion
- ✅ Logos and icons
- ✅ Simple graphics with solid colors
- ✅ Line art and illustrations
- ❌ Complex photographs (will create very large SVG files)
- ❌ Images with gradients or complex textures

---

## 📝 Color Scheme Details

### CSS Variables (Updated)
```css
:root {
  --background: 222 47% 11%;           /* #1a2942 Deep Navy */
  --primary: 262 83% 58%;              /* #8b5cf6 Purple */
  --gradient-primary: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 50%, #5b9fff 100%);
  --shadow-primary: 0 4px 16px 0 rgba(139, 92, 246, 0.4);  /* Purple glow */
}
```

### Component Updates
All these components now use the new color scheme:
- Buttons: Purple/blue gradient backgrounds
- Cards: Navy blue with purple borders
- Hover effects: Purple glow shadows
- Scrollbars: Purple theme
- Selection: Purple highlight
- Loading states: Purple shimmer

---

## 🐳 Docker Deployment

### Build and Run
```bash
# Backend
cd FileConverterBackend-main
docker build -t file-converter-backend .
docker run -p 5000:5000 file-converter-backend

# Frontend (if using Docker)
cd Frontend
docker build -t file-converter-frontend .
docker run -p 3000:80 file-converter-frontend
```

### Docker Compose (Full Stack)
```yaml
version: '3.8'
services:
  backend:
    build: ./FileConverterBackend-main
    ports:
      - "5000:5000"
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
    restart: unless-stopped

  frontend:
    build: ./Frontend
    ports:
      - "80:80"
    environment:
      - VITE_API_URL=http://backend:5000
    depends_on:
      - backend
    restart: unless-stopped
```

---

## 📋 File Checklist

### Backend Files to Update/Add
- ✅ `image_to_svg.py` (NEW)
- ✅ `main.py` (REPLACE)
- ✅ `Dockerfile` (REPLACE)
- ⚠️ `requirements.txt` (Same as before, no changes needed)

### Frontend Files to Update/Add
- ✅ `src/pages/tools/ImageToSVGConverter.tsx` (NEW)
- ✅ `src/index.css` (REPLACE)
- ✅ `src/App.tsx` (REPLACE)
- ✅ `src/data/tools.ts` (REPLACE)

---

## 🔧 Troubleshooting

### SVG Conversion Issues

**Error: "potrace: command not found"**
- Solution: Install potrace
  ```bash
  # Ubuntu/Debian
  sudo apt-get install potrace
  
  # macOS
  brew install potrace
  
  # Docker: Already included in updated Dockerfile
  ```

**Error: "Conversion failed"**
- Check image format is supported (PNG, JPG, BMP, etc.)
- Try with a simpler image first
- Check backend logs for detailed error messages

### Color Scheme Issues

**Colors not updating**
- Clear browser cache and hard refresh (Ctrl+Shift+R)
- Rebuild frontend: `npm run build`
- Check that `index.css` was properly replaced

**Gradients not showing**
- Verify Tailwind CSS is processing the updated config
- Check browser console for CSS errors
- Ensure all gradient classes are properly applied

---

## 🎯 Quick Start Commands

```bash
# Backend
cd FileConverterBackend-main
pip install -r requirements.txt
python main.py

# Frontend
cd Frontend
npm install
npm run dev

# Access application
# Frontend: http://localhost:5173
# Backend: http://localhost:5000
```

---

## 📞 Support

For issues with:
- **SVG Conversion**: Check potrace installation and image format
- **Color Scheme**: Verify CSS files were replaced correctly
- **Deployment**: Check server logs and environment variables
- **API Errors**: Check CORS settings and backend connectivity

---

## 🎉 Features Summary

### New Features
1. ✨ Image to SVG vector conversion
2. 🎨 Complete UI redesign with purple/blue theme
3. 🌈 Gradient buttons and cards
4. 💫 Purple glow effects and shadows
5. 🎯 Improved user experience consistency

### Existing Features (Maintained)
- Image conversion (JPG, PNG, WEBP, BMP)
- Image compression and resizing
- Background removal
- PDF/Word/PPT/Excel conversions
- Video/Audio conversion
- PDF merge, split, compress
- Image extraction from PDF/PPT

---

## 📄 License
Same as original project

## 🤝 Contributing
Feel free to submit issues and enhancement requests!