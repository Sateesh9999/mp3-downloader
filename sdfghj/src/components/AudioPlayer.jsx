import React, { useState, useEffect, useRef } from 'react'
import { streamAPI } from '../api/client'
import '../styles/AudioPlayer.css'

export default function AudioPlayer({ track, tracks, onTrackChange, onClose }) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const audioRef = useRef(null)

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    setCurrentTime(0)
    setDuration(0)
    if (isPlaying) {
      audio.play().catch(() => setIsPlaying(false))
    }
  }, [track._id])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const handleEnded = () => {
      // Play next track
      const currentIdx = tracks.findIndex(t => t._id === track._id)
      if (currentIdx < tracks.length - 1) {
        setIsPlaying(true)
        onTrackChange(tracks[currentIdx + 1])
      }
    }

    audio.addEventListener('ended', handleEnded)
    return () => audio.removeEventListener('ended', handleEnded)
  }, [track, tracks, onTrackChange])

  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause()
      } else {
        audioRef.current.play()
      }
    }
  }

  const handlePrevious = () => {
    const currentIdx = tracks.findIndex(t => t._id === track._id)
    if (currentIdx > 0) {
      onTrackChange(tracks[currentIdx - 1])
      setIsPlaying(true)
    }
  }

  const handleNext = () => {
    const currentIdx = tracks.findIndex(t => t._id === track._id)
    if (currentIdx < tracks.length - 1) {
      onTrackChange(tracks[currentIdx + 1])
      setIsPlaying(true)
    }
  }

  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`
  }

  return (
    <div className="audio-player">
      <audio
        ref={audioRef}
        src={streamAPI.stream(track._id)}
        onLoadedMetadata={() => setDuration(audioRef.current.duration)}
        onTimeUpdate={() => setCurrentTime(audioRef.current.currentTime)}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onError={() => setIsPlaying(false)}
      />

      <div className="player-track-info">
        <button onClick={onClose} className="btn-close" title="Close player">✕</button>
        <div className="track-details">
          <h4>{track.title}</h4>
          <p>{track.artist || 'Unknown'}</p>
        </div>
      </div>

      <div className="player-progress">
        <span className="time">{formatTime(currentTime)}</span>
        <input
          type="range"
          min="0"
          max={duration || 0}
          value={currentTime}
          onChange={(e) => {
            if (audioRef.current) {
              audioRef.current.currentTime = parseFloat(e.target.value)
            }
          }}
          className="progress-bar"
        />
        <span className="time">{formatTime(duration)}</span>
      </div>

      <div className="player-controls">
        <button onClick={handlePrevious} className="btn-control" title="Previous">⏮️</button>
        <button onClick={togglePlay} className="btn-play">
          {isPlaying ? '⏸️' : '▶️'}
        </button>
        <button onClick={handleNext} className="btn-control" title="Next">⏭️</button>
        <a
          href={streamAPI.download(track._id)}
          download={track.filename}
          className="btn-control"
          title="Download"
        >
          ⬇️
        </a>
      </div>
    </div>
  )
}
