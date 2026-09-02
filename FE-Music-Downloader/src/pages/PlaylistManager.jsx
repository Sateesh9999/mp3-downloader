import React, { useState, useEffect } from 'react'
import { playlistAPI, handleApiError } from '../api/client'
import '../styles/pages.css'

export default function PlaylistManager({ onViewPlaylist }) {
  const [playlists, setPlaylists] = useState([])
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [messageType, setMessageType] = useState('')

  useEffect(() => {
    fetchPlaylists()
  }, [])

  const fetchPlaylists = async () => {
    try {
      setLoading(true)
      const response = await playlistAPI.getAll()
      setPlaylists(response.data.playlists || [])
    } catch (error) {
      showMessage(handleApiError(error), 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleAddPlaylist = async (e) => {
    e.preventDefault()
    if (!url.trim()) {
      showMessage('Please enter a playlist URL', 'error')
      return
    }

    try {
      setLoading(true)
      await playlistAPI.add(url)
      showMessage('Playlist added successfully!', 'success')
      setUrl('')
      fetchPlaylists()
    } catch (error) {
      showMessage(handleApiError(error), 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleDeletePlaylist = async (id, name) => {
    if (window.confirm(`Delete "${name}" from sync? (Files will not be deleted)`)) {
      try {
        setLoading(true)
        await playlistAPI.delete(id, false)
        showMessage('Playlist removed from sync', 'success')
        fetchPlaylists()
      } catch (error) {
        showMessage(handleApiError(error), 'error')
      } finally {
        setLoading(false)
      }
    }
  }

  const showMessage = (msg, type) => {
    setMessage(msg)
    setMessageType(type)
    setTimeout(() => setMessage(''), 4000)
  }

  const getSourceIcon = (source) => {
    return source === 'spotify' ? '🎵' : '📺'
  }

  return (
    <div className="page-container">
      <div className="section">
        <h2>📋 Add New Playlist</h2>
        <form onSubmit={handleAddPlaylist} className="add-playlist-form">
          <input
            type="text"
            placeholder="Paste YouTube playlist URL"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={loading}
          />
          <button type="submit" disabled={loading} className="btn btn-primary">
            {loading ? 'Adding...' : '➕ Add & Sync'}
          </button>
        </form>

        {message && (
          <div className={`message message-${messageType}`}>
            {message}
          </div>
        )}
      </div>

      <div className="section">
        <h2>📚 Your Synced Playlists ({playlists.length})</h2>
        
        {playlists.length === 0 ? (
          <div className="empty-state">
            <p>No playlists synced yet</p>
            <p className="small">Add a playlist above to get started!</p>
          </div>
        ) : (
          <div className="playlists-grid">
            {playlists.map((playlist) => (
              <div key={playlist._id} className="playlist-card">
                <div className="playlist-header">
                  <h3>{getSourceIcon(playlist.source)} {playlist.name}</h3>
                  <span className="source-badge">{playlist.source}</span>
                </div>
                
                <div className="playlist-info">
                  <p><strong>Tracks:</strong> {playlist.track_count}</p>
                  <p><strong>Status:</strong> <span className={`status-${playlist.sync_status}`}>{playlist.sync_status}</span></p>
                  {playlist.last_sync_time && (
                    <p><strong>Last Sync:</strong> {new Date(playlist.last_sync_time).toLocaleString()}</p>
                  )}
                </div>

                <div className="playlist-actions">
                  <button
                    type="button"
                    onClick={() => onViewPlaylist(playlist._id)}
                    className="btn btn-secondary"
                    title="View playlist tracks"
                  >
                    📂 View
                  </button>
                  <button 
                    onClick={() => handleDeletePlaylist(playlist._id, playlist.name)}
                    className="btn btn-danger"
                    disabled={loading}
                  >
                    🗑️ Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
