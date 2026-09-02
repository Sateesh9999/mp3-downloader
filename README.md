# 🎵 Music Downloader - Full Implementation

A full-featured music sync and streaming application supporting **both Spotify and YouTube** playlists, with automatic weekly syncing, database tracking, and mobile-friendly streaming.

---

## 📋 Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Usage Guide](#usage-guide)
- [API Endpoints](#api-endpoints)
- [Architecture](#architecture)
- [Database Schema](#database-schema)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

### ✅ Implemented

- **Dual Source Support**: Sync from both Spotify and YouTube playlists
- **Database Tracking**: SQLite database stores playlist metadata, track info, and sync history
- **Automatic Weekly Sync**: APScheduler runs background sync jobs on configurable day/time
- **No Deletion Policy**: New syncs only add/update tracks, never delete existing files
- **Web-Based UI**: React frontend with responsive design
- **Audio Streaming**: Stream downloaded tracks directly from the web browser
- **Track Download**: Download individual tracks to mobile devices
- **Sync Dashboard**: Monitor sync status, history, and configure schedules
- **Playlist Management**: Add, remove, and view synced playlists
- **Music Library**: Browse all downloaded tracks with search functionality

### 🎯 Sync Logic

- **Initial Add**: When you add a playlist URL, the backend automatically:
  1. Detects if it's Spotify or YouTube
  2. Fetches playlist metadata (name, track count)
  3. Creates a folder structure: `Music/Playlist_Name/`
  4. Downloads all tracks to that folder
  5. Stores metadata in the database

- **Weekly Auto-Sync**: Runs on configured day/time:
  1. Checks each synced playlist on the source (Spotify API or YouTube)
  2. Compares with database to find new/updated tracks
  3. Downloads only new tracks (never touches old files)
  4. Updates sync history and last_sync_time

- **Manual Sync**: Click "Sync Now" anytime to manually sync:
  - Single playlist: Sync one playlist
  - Sync All: Sync all playlists at once

---

## 📁 Project Structure

```
musicDownloaderProject/
├── BE-Music-Downloader/          # Python Flask Backend
│   ├── app.py                     # Main Flask application + API routes
│   ├── config.py                  # Configuration management
│   ├── models.py                  # SQLAlchemy ORM models
│   ├── requirements.txt           # Python dependencies
│   ├── .env                       # Environment variables
│   ├── music_downloader.db        # SQLite database (auto-created)
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── spotify.py            # Spotify integration (spotdl)
│   │   └── youtube.py            # YouTube integration (yt-dlp)
│   └── services/
│       ├── __init__.py
│       └── sync.py               # Unified sync service
│
└── FE-Music-Downloader/          # React Vite Frontend
    ├── package.json
    ├── vite.config.js
    ├── index.html
    ├── src/
    │   ├── main.jsx              # React entry point
    │   ├── App.jsx               # Main app component
    │   ├── api/
    │   │   └── client.js         # API client & utilities
    │   ├── pages/
    │   │   ├── PlaylistManager.jsx   # Add/manage playlists
    │   │   ├── SyncDashboard.jsx     # Sync & schedule
    │   │   └── Library.jsx            # Browse & stream
    │   ├── components/
    │   │   └── AudioPlayer.jsx       # Music player component
    │   └── styles/
    │       ├── index.css
    │       ├── App.css
    │       ├── pages.css
    │       └── AudioPlayer.css
    └── node_modules/
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- `spotdl` and `yt-dlp` command-line tools (installed via pip)

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd BE-Music-Downloader
   ```

2. **Install Python dependencies** (already done):
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the backend** (already running on port 5000):
   ```bash
   python app.py
   ```

   The server will:
   - Create the SQLite database automatically
   - Initialize the APScheduler
   - Start listening on `http://127.0.0.1:5000`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd FE-Music-Downloader
   ```

2. **Install Node dependencies** (already done):
   ```bash
   npm install
   ```

3. **Start the dev server** (already running on port 5173):
   ```bash
   npm run dev
   ```

   Opens automatically at `http://localhost:5173`

---

## 📖 Usage Guide

### 1️⃣ Add a Playlist

**Page**: Playlist Manager → "Add New Playlist"

1. Copy a **Spotify or YouTube playlist URL**:
   - Spotify: `https://open.spotify.com/playlist/XXXXX`
   - YouTube: `https://www.youtube.com/playlist?list=XXXXX`

2. Paste it in the input field
3. Click "➕ Add & Sync"
4. The app will:
   - Auto-detect the source (Spotify/YouTube)
   - Create a folder: `C:/Users/thakk/Music/Playlist_Name/`
   - Download all tracks
   - Add to your library

### 2️⃣ View Your Playlists

**Page**: Playlist Manager → "Your Synced Playlists"

Shows all synced playlists with:
- Playlist name and source (Spotify 🎵 or YouTube 📺)
- Track count
- Sync status (pending/syncing/success/failed)
- Last sync time
- Actions: View or Remove

### 3️⃣ Sync Playlists

**Page**: Sync Dashboard → "Manual Sync"

#### Option A: Sync All
- Click "🔄 Sync All Playlists"
- Checks all playlists for new tracks
- Downloads new tracks only

#### Option B: Sync One Playlist
- In "Playlist Sync Status" section
- Click "🔄 Sync Now" on a specific playlist

### 4️⃣ Configure Weekly Auto-Sync

**Page**: Sync Dashboard → "Weekly Auto-Sync Schedule"

1. Enable the toggle: "Enable automatic weekly sync"
2. Select day of week (Monday-Sunday)
3. Select time (24-hour format, e.g., 02:00 = 2 AM)
4. Click "💾 Save Schedule"

The system will automatically sync all playlists on that day/time.

### 5️⃣ View Sync History

**Page**: Sync Dashboard → "Sync History"

Shows recent syncs with:
- Playlist ID
- Sync type (manual/automatic)
- Status (success/partial/failed)
- Tracks: new, updated, failed counts
- Timestamp

### 6️⃣ Stream & Download Tracks

**Page**: Library → "Music Library"

1. **Browse playlists**:
   - Left sidebar shows all synced playlists
   - Click a playlist to view its tracks

2. **Stream audio**:
   - Click "▶️ Play" on a track
   - Audio player opens at bottom
   - Controls: play/pause, prev/next, progress bar
   - Download button to save to device

3. **Search tracks**:
   - Use the search box to filter by title/artist

4. **Download tracks**:
   - Click "⬇️ Download" or in the player
   - Saves to your device's Downloads folder

---

## 🔌 API Endpoints

### Playlists

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/playlists` | Get all playlists |
| `POST` | `/api/playlists` | Add new playlist |
| `GET` | `/api/playlists/{id}` | Get playlist details + tracks |
| `DELETE` | `/api/playlists/{id}` | Remove playlist from sync |

**Request body (add playlist)**:
```json
{
  "url": "https://open.spotify.com/playlist/XXXXX"
}
```

### Sync

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/sync/playlist/{id}` | Sync single playlist |
| `POST` | `/api/sync/all` | Sync all playlists |
| `GET` | `/api/sync/history` | Get sync history |
| `GET` | `/api/sync/status` | Get current sync status |

### Scheduler

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/scheduler/config` | Get schedule config |
| `POST` | `/api/scheduler/config` | Update schedule |

**Request body (update schedule)**:
```json
{
  "enabled": true,
  "day_of_week": 0,
  "time_of_day": "02:00"
}
```

### Streaming

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/stream/{id}` | Stream audio (play in browser) |
| `GET` | `/api/download/{id}` | Download audio file |

### Health

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/health` | Server status check |

---

## 🏗️ Architecture

### Backend Flow

```
Frontend (React)
    ↓
  Axios API Calls
    ↓
Flask App (app.py)
    ├── /api/playlists → PlaylistManager → SyncService
    ├── /api/sync/* → SyncService
    ├── /api/stream/* → File Server
    └── /api/scheduler/* → APScheduler
    ↓
SyncService
    ├── Detects source (Spotify/YouTube)
    ├── SpotifySource (spotdl) → Downloads tracks
    ├── YouTubeSource (yt-dlp) → Downloads audio
    └── Updates DB (Playlists, Tracks, SyncHistory)
    ↓
SQLite Database
    ├── playlists table
    ├── tracks table
    ├── sync_history table
    └── scheduled_syncs table
    ↓
File System
    └── C:/Users/thakk/Music/Playlist_Name/*.mp3
```

### Frontend Architecture

```
App.jsx (Main Component)
    ├── Navigation (3 tabs)
    ├── Page Routing
    │   ├── PlaylistManager.jsx
    │   │   ├── Add Playlist Form
    │   │   └── Playlists Grid
    │   ├── SyncDashboard.jsx
    │   │   ├── Manual Sync Button
    │   │   ├── Weekly Schedule Config
    │   │   ├── Playlist Status Grid
    │   │   └── Sync History Table
    │   └── Library.jsx
    │       ├── Playlist Sidebar
    │       ├── Tracks List with Search
    │       └── AudioPlayer Component
    └── API Client (api/client.js)
        └── Axios instances for all endpoints
```

---

## 📊 Database Schema

### Playlists Table

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer | Primary key |
| `name` | String | Playlist name |
| `url` | String | Source URL (unique) |
| `source` | String | 'spotify' or 'youtube' |
| `source_id` | String | Platform-specific ID |
| `folder_path` | String | Local folder path |
| `track_count` | Integer | Number of tracks |
| `sync_status` | String | pending/syncing/success/failed |
| `last_sync_time` | DateTime | Last sync timestamp |
| `created_at` | DateTime | When added |

### Tracks Table

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer | Primary key |
| `playlist_id` | Integer | Foreign key to playlists |
| `title` | String | Track title |
| `artist` | String | Artist name |
| `source_id` | String | Spotify URI or YouTube ID |
| `filename` | String | Downloaded file name |
| `file_path` | String | Full local path |
| `download_status` | String | pending/downloading/completed/failed |
| `downloaded_date` | DateTime | When downloaded |

### SyncHistory Table

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer | Primary key |
| `playlist_id` | Integer | Foreign key to playlists |
| `sync_type` | String | 'manual' or 'automatic' |
| `status` | String | success/partial/failed |
| `new_tracks` | Integer | Count of new downloads |
| `updated_tracks` | Integer | Count of already synced |
| `failed_tracks` | Integer | Count of failures |
| `start_time` | DateTime | Sync start |
| `end_time` | DateTime | Sync end |

---

## 🔧 Configuration

### Backend (.env file)

```env
# Environment
FLASK_ENV=development
FLASK_DEBUG=True

# Database
DATABASE_URL=sqlite:///music_downloader.db

# Server
BACKEND_PORT=5000
FRONTEND_ORIGIN=http://localhost:5173

# Storage
DEST_DIR=C:/Users/thakk/Music

# Timeouts
DOWNLOAD_TIMEOUT=300

# Schedule
SYNC_DAY_OF_WEEK=0  (0=Monday)
SYNC_TIME_OF_DAY=02:00
```

### Key Settings

- **DEST_DIR**: Where to save downloaded music
- **DOWNLOAD_TIMEOUT**: Max time (seconds) for one track download
- **FRONTEND_ORIGIN**: CORS origin for browser requests

---

## ⚙️ Sync Behavior

### Initial Sync (When Adding Playlist)

1. Fetch playlist info from Spotify API or YouTube
2. Get track list with metadata
3. Create local folder: `DEST_DIR/PlaylistName/`
4. Download all tracks using:
   - **Spotify**: `spotdl download {spotify_uri}` 
   - **YouTube**: `yt-dlp --extract-audio --audio-format mp3 {video_url}`
5. Store in database with status "completed"
6. Update playlist.track_count

### Weekly Auto-Sync (If Enabled)

1. APScheduler triggers at configured day/time
2. For each synced playlist:
   - Fetch current playlist info from source
   - Compare source IDs with database
   - Find new/removed tracks
3. Download only new tracks
4. Update sync_history with results
5. **Never delete** existing tracks

### Key Properties

- ✅ **Additive Only**: Sync only adds/updates, never removes
- ✅ **Duplicate Prevention**: Checks source_id before re-downloading
- ✅ **Metadata Tracking**: Stores which playlist each track belongs to
- ✅ **Error Handling**: Failed tracks marked in database, can retry
- ✅ **Performance**: Only processes new tracks

---

## 🆘 Troubleshooting

### Issue: "Cannot connect to server"

**Solution**:
```bash
# Make sure backend is running
cd BE-Music-Downloader
python app.py

# Check port 5000 is open
netstat -ano | findstr :5000
```

### Issue: "spotdl not found"

**Solution**:
```bash
pip install spotdl
spotdl --version  # Verify
```

### Issue: "yt-dlp not found"

**Solution**:
```bash
pip install yt-dlp
yt-dlp --version  # Verify
```

### Issue: Downloads are slow

**Causes**:
- Internet speed
- Download timeout too short (increase `DOWNLOAD_TIMEOUT` in .env)
- Server overload

**Solution**:
```env
# Increase to 10 minutes
DOWNLOAD_TIMEOUT=600
```

### Issue: "Database locked" error

**Solution**:
- Only one Flask instance should run at a time
- Kill any existing Python processes:
  ```bash
  taskkill /F /IM python.exe
  ```

### Issue: Playlists not syncing automatically

**Check**:
1. APScheduler is enabled in database
2. Check backend logs for scheduler messages
3. Verify day/time configuration matches your timezone

---

## 📝 Next Steps

### Future Enhancements

1. **Authentication**: Multi-user support with accounts
2. **Caching**: Cache Spotify/YouTube API responses
3. **Progress Indicator**: Show download progress during sync
4. **Playlist Sharing**: Share playlists between users
5. **Offline Mode**: Downloaded tracks work offline
6. **Advanced Search**: Filter by date added, artist, etc.
7. **Mobile App**: Native iOS/Android app
8. **Cloud Backup**: Backup synced tracks to cloud storage

---

## 📄 License

MIT

---

## 🎯 Support

For issues or questions:
1. Check the database: `music_downloader.db`
2. Review backend logs in terminal
3. Check browser console (F12) for frontend errors
4. Verify .env configuration

---

**Happy Syncing! 🎵**
migrated to mongodb and docker images