import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://0.0.0.0:5000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Playlist endpoints
export const playlistAPI = {
  getAll: () => api.get('/playlists'),
  get: (id) => api.get(`/playlists/${id}`),
  add: (url) => api.post('/playlists', { url }),
  delete: (id, deleteFiles = false) => 
    api.delete(`/playlists/${id}`, { data: { delete_files: deleteFiles } })
}

// Sync endpoints
export const syncAPI = {
  syncOne: (playlistId) => api.post(`/sync/playlist/${playlistId}`),
  syncAll: () => api.post('/sync/all'),
  getHistory: (playlistId = null) => {
    const params = playlistId ? { playlist_id: playlistId } : {}
    return api.get('/sync/history', { params })
  },
  getStatus: () => api.get('/sync/status')
}

// Scheduler endpoints
export const schedulerAPI = {
  getConfig: () => api.get('/scheduler/config'),
  updateConfig: (config) => api.post('/scheduler/config', config)
}

// Streaming endpoints
export const streamAPI = {
  stream: (trackId) => `${API_BASE_URL}/stream/${trackId}`,
  download: (trackId) => `${API_BASE_URL}/download/${trackId}`
}

// Health check
export const healthCheck = () => api.get('/health')

// Error handler
export const handleApiError = (error) => {
  if (error.response) {
    return error.response.data?.message || 'An error occurred'
  } else if (error.request) {
    return 'No response from server'
  } else {
    return error.message || 'An error occurred'
  }
}

export default api
