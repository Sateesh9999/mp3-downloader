import React, { useState, useEffect } from 'react'
import { playlistAPI, trackAPI, syncAPI, streamAPI, handleApiError } from '../api/client'
import '../styles/pages.css'

export default function Library({ initialPlaylistId, onPlayTrack }) {
  const [playlists, setPlaylists] = useState([])
  const [selectedPlaylistId, setSelectedPlaylistId] = useState(null)
  const [playlistTracks, setPlaylistTracks] = useState(null)
  const [databaseTracks, setDatabaseTracks] = useState([])
  const [loading, setLoading] = useState(false)
  const [databaseLoading, setDatabaseLoading] = useState(false)
  const [activeView, setActiveView] = useState('database')
  const [filter, setFilter] = useState('')
  const [actionId, setActionId] = useState(null)

  useEffect(() => {
    fetchPlaylists()
    fetchDatabaseTracks()
  }, [])

  useEffect(() => {
    if (initialPlaylistId) {
      setSelectedPlaylistId(initialPlaylistId)
    }
  }, [initialPlaylistId])

  useEffect(() => {
    if (selectedPlaylistId) {
      fetchPlaylistTracks(selectedPlaylistId)
    }
  }, [selectedPlaylistId])

  const fetchPlaylists = async () => {
    try {
      setLoading(true)
      const response = await playlistAPI.getAll()
      const playlists = response.data.playlists || []
      setPlaylists(playlists)
      if (playlists.length > 0 && !selectedPlaylistId) {
        setSelectedPlaylistId(playlists[0]._id)
      }
    } catch (error) {
      console.error(handleApiError(error))
    } finally {
      setLoading(false)
    }
  }

  const fetchPlaylistTracks = async (playlistId) => {
    try {
      setLoading(true)
      const response = await playlistAPI.get(playlistId)
      setPlaylistTracks(response.data.data)
    } catch (error) {
      console.error(handleApiError(error))
      setPlaylistTracks(null)
    } finally {
      setLoading(false)
    }
  }

  const fetchDatabaseTracks = async () => {
    try {
      setDatabaseLoading(true)
      const response = await trackAPI.getAll()
      setDatabaseTracks(response.data.tracks || [])
    } catch (error) {
      console.error(handleApiError(error))
      setDatabaseTracks([])
    } finally {
      setDatabaseLoading(false)
    }
  }

  const handleSyncPlaylist = async (playlist) => {
    try {
      setActionId(playlist._id)
      await syncAPI.syncOne(playlist._id)
      await Promise.all([fetchPlaylists(), fetchDatabaseTracks()])
      if (selectedPlaylistId === playlist._id) {
        await fetchPlaylistTracks(playlist._id)
      }
    } catch (error) {
      console.error(handleApiError(error))
    } finally {
      setActionId(null)
    }
  }

  const handleRemovePlaylist = async (playlist) => {
    if (!window.confirm(`Remove "${playlist.name}" from your playlists? Downloaded files will be preserved.`)) {
      return
    }

    try {
      setActionId(playlist._id)
      await playlistAPI.delete(playlist._id, false)
      if (selectedPlaylistId === playlist._id) {
        setSelectedPlaylistId(null)
        setPlaylistTracks(null)
        setActiveView('database')
      }
      await fetchPlaylists()
    } catch (error) {
      console.error(handleApiError(error))
    } finally {
      setActionId(null)
    }
  }

  const playTrack = (track) => {
    if (track.download_status === 'completed') {
      onPlayTrack(track, playableTracks, playlistTracks?.playlist?.name)
    }
  }

  const filteredTracks = playlistTracks?.tracks?.filter(track => {
    const query = filter.toLowerCase()
    return (
      track.title.toLowerCase().includes(query) ||
      (track.artist && track.artist.toLowerCase().includes(query))
    )
  }) || []
  const playableTracks = filteredTracks.filter(track => track.download_status === 'completed')
  const filteredDatabaseTracks = databaseTracks.filter(track => {
    const query = filter.toLowerCase()
    return (
      track.title.toLowerCase().includes(query) ||
      (track.artist && track.artist.toLowerCase().includes(query))
    )
  })
  const playableDatabaseTracks = filteredDatabaseTracks.filter(track => track.download_status === 'completed')

  return (
    <div className="page-container">
      
      <div className="section">
        <div className="library-heading">
          <div>
            <h2>🎧 Music Library</h2>
            <p className="section-subtitle">Your downloaded music, organized by source.</p>
          </div>
          <div className="library-toolbar">
            <button
              className={`nav-button ${activeView === 'database' ? 'active' : ''}`}
              onClick={() => setActiveView('database')}
            >
              Drift Through DataBase
            </button>
          </div>
        </div>

        <div className="library-layout">
          <div className="sidebar">
            <h3>🎵 Your Playlists</h3>
            {playlists.length === 0 ? (
              <p className="empty-text">No playlists yet</p>
            ) : (
              <div className="playlist-list">
                {playlists.map((playlist) => (
                  <div key={playlist._id} className="playlist-entry">
                    <button
                      className={`playlist-item ${activeView === playlist._id && selectedPlaylistId === playlist._id ? 'active' : ''}`}
                      onClick={() => {
                        setSelectedPlaylistId(playlist._id)
                        setActiveView(playlist._id)
                      }}
                    >
                      <span className="playlist-name">{playlist.name}</span>
                      <span className="track-count">{playlist.track_count} tracks</span>
                    </button>
                    <div className="playlist-entry-actions">
                      <button
                        className="btn btn-small btn-secondary"
                        onClick={() => handleSyncPlaylist(playlist)}
                        disabled={actionId === playlist._id}
                        title="Sync playlist"
                      >
                        🔄
                      </button>
                      <button
                        className="btn btn-small btn-danger"
                        onClick={() => handleRemovePlaylist(playlist)}
                        disabled={actionId === playlist._id}
                        title="Remove playlist"
                      >
                        🗑️
                      </button>
                      <button
                        className="btn btn-small btn-secondary"
                        onClick={() => {
                          setSelectedPlaylistId(playlist._id)
                          setActiveView(playlist._id)
                        }}
                        title="View playlist"
                      >
                        📂
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="main-content">
            {activeView === 'database' ? (
              <>
                <h3>All downloaded tracks</h3>
                <div className="library-controls">
                  <input
                    type="text"
                    placeholder="Search tracks by title or artist..."
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    className="search-input"
                  />
                </div>
                {databaseLoading ? (
                  <p className="loading-text">Loading tracks...</p>
                ) : filteredDatabaseTracks.length === 0 ? (
                  <div className="empty-state">
                    <p>{filter ? 'No tracks match your search' : 'No tracks in the database'}</p>
                  </div>
                ) : (
                  <div className="tracks-list">
                    {filteredDatabaseTracks.map((track) => (
                      <div key={track._id} className="track-item">
                        <div className="track-info">
                          <h4>{track.title}</h4>
                          <p>{track.artist || 'Unknown Artist'}</p>
                          <span className={`status-${track.download_status}`}>
                            {track.download_status === 'completed' ? '✓ Downloaded' : `⏳ ${track.download_status}`}
                          </span>
                        </div>
                        {track.download_status === 'completed' && (
                          <div className="track-actions">
                            <button
                              onClick={() => onPlayTrack(track, playableDatabaseTracks, 'Drift in DataBase')}
                              className="btn btn-small btn-primary"
                              title="Play"
                            >
                              ▶️ Play
                            </button>
                            <a
                              href={streamAPI.download(track._id)}
                              download={track.filename}
                              className="btn btn-small btn-secondary"
                              title="Download"
                            >
                              ⬇️ Download
                            </a>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : selectedPlaylistId && playlistTracks ? (
              <>
                <div className="playlist-view-heading">
                  <div>
                    <h3>{playlistTracks.playlist?.name}</h3>
                    <p className="section-subtitle">Playlist collection</p>
                  </div>
                  <div className="playlist-actions">
                    <button
                      className="btn btn-small btn-secondary"
                      onClick={() => handleSyncPlaylist(playlistTracks.playlist)}
                      disabled={actionId === selectedPlaylistId}
                    >
                      {actionId === selectedPlaylistId ? '⏳ Syncing...' : '🔄 Sync'}
                    </button>
                    <button
                      className="btn btn-small btn-danger"
                      onClick={() => handleRemovePlaylist(playlistTracks.playlist)}
                      disabled={actionId === selectedPlaylistId}
                    >
                      🗑️ Remove
                    </button>
                  </div>
                </div>
                <p className="playlist-stats">
                  Total: {playlistTracks.total_tracks} | 
                  Downloaded: {playlistTracks.downloaded_tracks} | 
                  Failed: {playlistTracks.failed_tracks}
                </p>

                <div className="library-controls">
                  <input
                    type="text"
                    placeholder="Search tracks by title or artist..."
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    className="search-input"
                  />
                </div>

                {filteredTracks.length === 0 ? (
                  <div className="empty-state">
                    <p>{filter ? 'No tracks match your search' : 'No tracks in this playlist'}</p>
                  </div>
                ) : (
                  <div className="tracks-list">
                    {filteredTracks.map((track) => (
                      <div key={track._id} className="track-item">
                        <div className="track-info">
                          <h4>{track.title}</h4>
                          <p>{track.artist || 'Unknown Artist'}</p>
                          <span className={`status-${track.download_status}`}>
                            {track.download_status === 'completed' ? '✓ Downloaded' : `⏳ ${track.download_status}`}
                          </span>
                        </div>

                        <div className="track-actions">
                          {track.download_status === 'completed' && (
                            <>
                              <button
                                onClick={() => playTrack(track)}
                                className="btn btn-small btn-primary"
                                title="Play"
                              >
                                ▶️ Play
                              </button>
                              <a
                                href={streamAPI.download(track._id)}
                                download={track.filename}
                                className="btn btn-small btn-secondary"
                                title="Download"
                              >
                                ⬇️ Download
                              </a>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : loading ? (
              <p className="loading-text">Loading...</p>
            ) : (
              <p className="empty-text">Select a playlist to view tracks</p>
            )}
          </div>
        </div>
      </div>

    </div>
  )
}
