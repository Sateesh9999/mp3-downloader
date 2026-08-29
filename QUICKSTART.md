# 🚀 Quick Start Guide

## Current Status

✅ **Both servers are running!**

- Backend: http://127.0.0.1:5000 (Flask)
- Frontend: http://localhost:5173 (React/Vite)

---

## Step-by-Step Instructions

### 1. Open the Web App

Open your browser and go to: **http://localhost:5173**

You should see:
- Header with "Music Downloader" and connection status
- Navigation with 3 tabs: 📋 Playlists | 🔄 Sync | 🎧 Library

### 2. Add Your First Playlist

**Tab**: Playlists Manager

1. **Get a playlist URL**:
   - **Spotify**: Open a playlist → Click "Share" → Copy link (e.g., `https://open.spotify.com/playlist/...`)
   - **YouTube**: Right-click playlist → Copy URL (e.g., `https://www.youtube.com/playlist?list=...`)

2. **Paste and add**:
   - Paste the URL in the input field
   - Click "➕ Add & Sync"
   - Wait for downloads to complete (check backend console for progress)

3. **View your playlist**:
   - It will appear in "Your Synced Playlists"
   - Shows: Name, source icon, track count, sync status, last sync time

### 3. Configure Weekly Auto-Sync

**Tab**: Sync Dashboard

1. Scroll to "Weekly Auto-Sync Schedule"
2. Enable checkbox: "Enable automatic weekly sync"
3. Select day (e.g., Monday) and time (e.g., 02:00 for 2 AM)
4. Click "💾 Save Schedule"
5. System will auto-sync every week at that time!

### 4. Stream Your Music

**Tab**: Library

1. **Select a playlist** from left sidebar
2. **Search or browse** tracks
3. **Click ▶️ Play** on any track
4. **Audio player** appears at bottom with:
   - Play/Pause, Previous, Next buttons
   - Progress bar with time display
   - Download button

### 5. Manually Sync Anytime

**Tab**: Sync Dashboard

- **Sync All**: Sync all playlists instantly
- **Sync One**: In "Playlist Sync Status" section, click "🔄 Sync Now" for specific playlist

---

## File Locations

### Downloaded Music

All tracks are stored here:
```
C:\Users\thakk\Music\
├── Playlist_Name_1\
│   ├── Track 1.mp3
│   ├── Track 2.mp3
│   └── ...
├── Playlist_Name_2\
│   └── ...
```

### Database

SQLite database with all metadata:
```
BE-Music-Downloader/music_downloader.db
```

---

## What Happens Behind the Scenes

### When You Add a Playlist:
1. System detects if it's Spotify or YouTube
2. Creates a folder for the playlist
3. Downloads **all tracks** to that folder
4. Stores metadata in database
5. Shows "success" status

### When You Sync:
1. System checks the source (Spotify/YouTube)
2. Finds **only new tracks** since last sync
3. Downloads only new ones (doesn't re-download old)
4. Updates database
5. Shows count of new/updated/failed tracks

### Weekly Auto-Sync:
1. Runs automatically on configured day/time
2. Repeats the sync process for **all playlists**
3. Runs in background (doesn't block web interface)
4. Records in sync history

---

## Common Tasks

### Add Multiple Playlists

Just repeat step 2 above with different playlist URLs!

### Remove a Playlist

**Tab**: Playlists Manager
- Click 🗑️ Remove on a playlist
- Files stay on disk, just removed from tracking

### See Sync History

**Tab**: Sync Dashboard
- Scroll to "Sync History"
- Shows last 10 syncs with details (new tracks, failures, timestamp)

### Download a Track

**Tab**: Library
- Click "▶️ Play" to start playing
- Click "⬇️ Download" in the player
- File saves to your Downloads folder

---

## Stopping/Restarting

### Backend

In backend terminal:
```bash
# Press Ctrl+C to stop
# To restart:
python app.py
```

### Frontend

In frontend terminal:
```bash
# Press Ctrl+C to stop
# To restart:
npm run dev
```

---

## Keyboard Shortcuts

- **Tab**: Switch between Playlists | Sync | Library
- **Ctrl+F**: Search tracks (in Library tab)
- **Space**: Play/Pause (when player is focused)
- **← →**: Previous/Next track (when player is focused)

---

## Troubleshooting

### Frontend shows "Disconnected from server"

Backend might not be running:
```bash
# In BE-Music-Downloader terminal:
python app.py
```

### Downloads not starting

Check backend terminal for error messages about spotdl or yt-dlp

### Weekly sync not running

Check that:
1. Toggle is enabled
2. Day/time is set correctly
3. Backend is still running

---

## Next: Advanced Features

- Use frontend search to quickly find tracks
- Change DEST_DIR in .env to sync to different location
- Increase DOWNLOAD_TIMEOUT if downloads keep timing out
- Check browser DevTools (F12) for detailed error messages

---

**Enjoy your music! 🎵**

For detailed documentation, see: [README.md](README.md)
