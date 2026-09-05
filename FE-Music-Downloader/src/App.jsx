import React, { useState, useEffect } from 'react'
import './styles/App.css'
import PlaylistManager from './pages/PlaylistManager'
import SyncDashboard from './pages/SyncDashboard'
import Library from './pages/Library'
import AudioPlayer from './components/AudioPlayer'
import { healthCheck } from './api/client'

const PLAYER_STORAGE_KEY = 'music-downloader-player'

const getSavedPlayer = () => {
  try {
    const savedPlayer = localStorage.getItem(PLAYER_STORAGE_KEY)
    return savedPlayer ? JSON.parse(savedPlayer) : null
  } catch {
    return null
  }
}

function App() {
  const [activeTab, setActiveTab] = useState('library')
  const [isConnected, setIsConnected] = useState(false)
  const [loading, setLoading] = useState(true)
  const [savedPlayer] = useState(getSavedPlayer)
  const [currentTrack, setCurrentTrack] = useState(savedPlayer?.track || null)
  const [playableTracks, setPlayableTracks] = useState([])
  const [currentPosition, setCurrentPosition] = useState(savedPlayer?.position || 0)
  const [shouldAutoPlay, setShouldAutoPlay] = useState(false)
  const [currentPlaylist, setCurrentPlaylist] = useState(savedPlayer?.playlist || 'Unknown playlist')

  const handlePlayTrack = (track, tracks, playlist = 'Unknown playlist') => {
    setCurrentTrack(track)
    setPlayableTracks(tracks)
    setCurrentPlaylist(playlist)
    setCurrentPosition(0)
    setShouldAutoPlay(true)
  }

  const handleTrackChange = (track) => {
    setCurrentTrack(track)
    setCurrentPosition(0)
    setShouldAutoPlay(true)
  }

  const handlePositionChange = (position) => {
    setCurrentPosition(position)
  }

  useEffect(() => {
    if (!currentTrack) return

    localStorage.setItem(PLAYER_STORAGE_KEY, JSON.stringify({
      track: currentTrack,
      position: currentPosition,
      playlist: currentPlaylist
    }))
  }, [currentTrack, currentPosition])

  useEffect(() => {
    // Check server connection
    const checkConnection = async () => {
      try {
        await healthCheck()
        setIsConnected(true)
      } catch (error) {
        console.error('Server connection failed:', error)
        setIsConnected(false)
      } finally {
        setLoading(false)
      }
    }

    checkConnection()
    
    // Check connection every 30 seconds
    const interval = setInterval(checkConnection, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          {currentTrack && (
            <div className="player-section">
              <AudioPlayer 
                track={currentTrack}
                tracks={playableTracks}
                playlist={currentPlaylist}
                initialTime={currentPosition}
                autoPlay={shouldAutoPlay}
                onTrackChange={handleTrackChange}
                onPositionChange={handlePositionChange}
              />
            </div>
          )}
          
          <div className="connection-status">
            <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></span>
            <span className="status-text">
              {isConnected ? 'Connected to server' : 'Disconnected from server'}
            </span>
          </div>
        </div>
      </header>

      <nav className="app-nav">
        <button 
          className={`nav-button ${activeTab === 'library' ? 'active' : ''}`}
          onClick={() => setActiveTab('library')}
        >
          🎧 Library
        </button>
        <button 
          className={`nav-button ${activeTab === 'playlists' ? 'active' : ''}`}
          onClick={() => setActiveTab('playlists')}
        >
          ➕ Add Playlist
        </button>
        <button 
          className={`nav-button ${activeTab === 'sync' ? 'active' : ''}`}
          onClick={() => setActiveTab('sync')}
        >
          ⚙️ Set Auto Sync
        </button>

      </nav>

      <main className="app-content">
        {loading ? (
          <div className="loading">
            <p>Connecting to server...</p>
          </div>
        ) : !isConnected ? (
          <div className="error-box">
            <h2>❌ Server Connection Failed</h2>
            <p>Cannot connect to the backend server at <code>http://localhost:5000</code></p>
            <p>Please make sure the Flask backend is running.</p>
          </div>
        ) : (
          <>
            {activeTab === 'library' && (
              <Library
                onPlayTrack={handlePlayTrack}
              />
            )}
            {activeTab === 'playlists' && <PlaylistManager />}
            {activeTab === 'sync' && <SyncDashboard />}

          </>
        )}
      </main>

      <footer className="app-footer">
        <p>Music Downloader v1.0 | Sync your favorite playlists from YouTube</p>
      </footer>
    </div>
  )
}

export default App
