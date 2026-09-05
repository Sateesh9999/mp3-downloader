import React, { useState, useEffect } from 'react'
import './styles/App.css'
import PlaylistManager from './pages/PlaylistManager'
import SyncDashboard from './pages/SyncDashboard'
import Library from './pages/Library'
import { healthCheck } from './api/client'

function App() {
  const [activeTab, setActiveTab] = useState('playlists')
  const [libraryPlaylistId, setLibraryPlaylistId] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const [loading, setLoading] = useState(true)

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
          <h1>🎵 Music Downloader</h1>
          <p className="subtitle">Sync & Stream your playlists</p>
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
          className={`nav-button ${activeTab === 'playlists' ? 'active' : ''}`}
          onClick={() => setActiveTab('playlists')}
        >
          📋 Playlists
        </button>
        <button 
          className={`nav-button ${activeTab === 'sync' ? 'active' : ''}`}
          onClick={() => setActiveTab('sync')}
        >
          🔄 Sync
        </button>
        <button 
          className={`nav-button ${activeTab === 'library' ? 'active' : ''}`}
          onClick={() => setActiveTab('library')}
        >
          🎧 Library
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
            {activeTab === 'playlists' && (
              <PlaylistManager
                onViewPlaylist={(playlistId) => {
                  setLibraryPlaylistId(playlistId)
                  setActiveTab('library')
                }}
              />
            )}
            {activeTab === 'sync' && <SyncDashboard />}
            {activeTab === 'library' && <Library initialPlaylistId={libraryPlaylistId} />}
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
