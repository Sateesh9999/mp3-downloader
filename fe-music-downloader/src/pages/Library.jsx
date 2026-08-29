import React, { useState, useEffect } from 'react'
import { playlistAPI, streamAPI, handleApiError } from '../api/client'
import AudioPlayer from '../components/AudioPlayer'
import '../styles/pages.css'

export default function Library() {
  const [playlists, setPlaylists] = useState([])
  const [selectedPlaylistId, setSelectedPlaylistId] = useState(null)
  const [playlistTracks, setPlaylistTracks] = useState(null)
  const [loading, setLoading] = useState(false)
  const [currentTrack, setCurrentTrack] = useState(null)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    fetchPlaylists()
  }, [])

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
        setSelectedPlaylistId(playlists[0].id)
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

  const playTrack = (track) => {
    if (track.download_status === 'completed') {
      setCurrentTrack(track)
    }
  }

  const filteredTracks = playlistTracks?.tracks?.filter(track => {
    const query = filter.toLowerCase()
    return (
      track.title.toLowerCase().includes(query) ||
      (track.artist && track.artist.toLowerCase().includes(query))
    )
  }) || []

  return (
    <div className="page-container">
      <div className="section">
        <h2>🎧 Music Library</h2>

        <div className="library-layout">
          <div className="sidebar">
            <h3>🎵 Your Playlists</h3>
            {playlists.length === 0 ? (
              <p className="empty-text">No playlists yet</p>
            ) : (
              <div className="playlist-list">
                {playlists.map((playlist) => (
                  <button
                    key={playlist.id}
                    className={`playlist-item ${selectedPlaylistId === playlist.id ? 'active' : ''}`}
                    onClick={() => setSelectedPlaylistId(playlist.id)}
                  >
                    <span className="playlist-name">{playlist.name}</span>
                    <span className="track-count">{playlist.track_count} tracks</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="main-content">
            {selectedPlaylistId && playlistTracks ? (
              <>
                <h3>{playlistTracks.playlist?.name}</h3>
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
                      <div key={track.id} className="track-item">
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
                                href={streamAPI.download(track.id)}
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

      {currentTrack && (
        <div className="player-section">
          <AudioPlayer 
            track={currentTrack}
            tracks={filteredTracks}
            onTrackChange={setCurrentTrack}
            onClose={() => setCurrentTrack(null)}
          />
        </div>
      )}
    </div>
  )
}
