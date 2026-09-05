import React, { useState, useEffect } from 'react'
import { playlistAPI, syncAPI, schedulerAPI, handleApiError } from '../api/client'
import '../styles/pages.css'

export default function SyncDashboard() {
  const [playlists, setPlaylists] = useState([])
  const [syncHistory, setSyncHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [message, setMessage] = useState('')
  const [messageType, setMessageType] = useState('')

  const [scheduleForm, setScheduleForm] = useState({
    enabled: true,
    day_of_week: 0,
    time_of_day: '02:00'
  })

  useEffect(() => {
    fetchData()
    // Refresh data every 10 seconds
    const interval = setInterval(fetchData, 60000)
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [playlistsRes, historyRes, configRes] = await Promise.all([
        playlistAPI.getAll(),
        syncAPI.getHistory(),
        schedulerAPI.getConfig()
      ])

      setPlaylists(playlistsRes.data.playlists || [])
      setSyncHistory(historyRes.data.sync_histories || [])
      
      const config = configRes.data.config
      setScheduleForm({
        enabled: config.enabled,
        day_of_week: config.day_of_week,
        time_of_day: config.time_of_day
      })
    } catch (error) {
      showMessage(handleApiError(error), 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleSyncPlaylist = async (id, name) => {
    try {
      setSyncing(true)
      showMessage(`Syncing "${name}"...`, 'info')
      const response = await syncAPI.syncOne(id)
      showMessage(response.data.message, 'success')
      fetchData()
    } catch (error) {
      showMessage(handleApiError(error), 'error')
    } finally {
      setSyncing(false)
    }
  }

  const handleSyncAll = async () => {
    try {
      setSyncing(true)
      showMessage('Syncing all playlists...', 'info')
      const response = await syncAPI.syncAll()
      showMessage(response.data.message, 'success')
      fetchData()
    } catch (error) {
      showMessage(handleApiError(error), 'error')
    } finally {
      setSyncing(false)
    }
  }

  const handleScheduleUpdate = async (e) => {
    e.preventDefault()
    try {
      setLoading(true)
      await schedulerAPI.updateConfig(scheduleForm)
      showMessage('Schedule updated successfully!', 'success')
      fetchData()
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

  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

  return (
    <div className="page-container">
      <div className="section">
        <h2>🔄 Manual Sync</h2>
        <div className="sync-controls">
          <button 
            onClick={handleSyncAll}
            disabled={syncing || playlists.length === 0}
            className="btn btn-primary btn-large"
          >
            {syncing ? '⏳ Syncing...' : '🔄 Sync All Playlists'}
          </button>
          <p className="info-text">Sync all playlists now. New tracks will be downloaded automatically.</p>
        </div>

        {message && (
          <div className={`message message-${messageType}`}>
            {message}
          </div>
        )}
      </div>

      <div className="section">
        <h2>📅 Weekly Auto-Sync Schedule</h2>
        <form onSubmit={handleScheduleUpdate} className="schedule-form">
          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={scheduleForm.enabled}
                onChange={(e) => setScheduleForm({...scheduleForm, enabled: e.target.checked})}
                disabled={loading}
              />
              Enable automatic weekly sync
            </label>
          </div>

          {scheduleForm.enabled && (
            <>
              <div className="form-group">
                <label>Day of Week:</label>
                <select
                  value={scheduleForm.day_of_week}
                  onChange={(e) => setScheduleForm({...scheduleForm, day_of_week: parseInt(e.target.value)})}
                  disabled={loading}
                >
                  {days.map((day, idx) => (
                    <option key={idx} value={idx}>{day}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Time of Day (24-hour format):</label>
                <input
                  type="time"
                  value={scheduleForm.time_of_day}
                  onChange={(e) => setScheduleForm({...scheduleForm, time_of_day: e.target.value})}
                  disabled={loading}
                />
              </div>
            </>
          )}

          <button type="submit" disabled={loading} className="btn btn-secondary">
            {loading ? 'Updating...' : '💾 Save Schedule'}
          </button>
        </form>
      </div>

      <div className="section">
        <h2>🎯 Playlist Sync Status</h2>
        <div className="status-grid">
          {playlists.length === 0 ? (
            <p className="empty-text">No playlists to sync</p>
          ) : (
            playlists.map((playlist) => (
              <div key={playlist._id} className="status-card">
                <h4>{playlist.name}</h4>
                <p><strong>Status:</strong> <span className={`status-${playlist.sync_status}`}>{playlist.sync_status}</span></p>
                <p><strong>Tracks:</strong> {playlist.track_count}</p>
                <p><strong>Last Sync:</strong> {playlist.last_sync_time ? new Date(playlist.last_sync_time).toLocaleString() : 'Never'}</p>
                <button
                  onClick={() => handleSyncPlaylist(playlist._id, playlist.name)}
                  disabled={syncing}
                  className="btn btn-small btn-secondary"
                >
                  🔄 Sync Now
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="section">
        <h2>📊 Sync History</h2>
        <div className="history-table">
          {syncHistory.length === 0 ? (
            <p className="empty-text">No sync history yet</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Playlist</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>New</th>
                  <th>Updated</th>
                  <th>Failed</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {syncHistory.slice(0, 10).map((history) => (
                  <tr key={history._id}>
                    <td>
                      {playlists.find(
                        (playlist) => playlist._id === history.playlist_id
                      )?.name || 'Unknown playlist'}
                    </td>
                    <td>{history.sync_type}</td>
                    <td><span className={`status-${history.status}`}>{history.status}</span></td>
                    <td>{history.new_tracks}</td>
                    <td>{history.updated_tracks}</td>
                    <td>{history.failed_tracks}</td>
                    <td>{new Date(history.start_time).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
