import React, { useState } from 'react'
import { playlistAPI, handleApiError } from '../api/client'
import '../styles/pages.css'

export default function PlaylistManager() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [messageType, setMessageType] = useState('')

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
    } catch (error) {
      showMessage(handleApiError(error), 'error')
    } finally {
      setLoading(false)
    }
  }

  const showMessage = (msg, type) => {
    setMessage(msg)
    setMessageType(type)
    setTimeout(() => setMessage(''), 4000)
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

    </div>
  )
}
