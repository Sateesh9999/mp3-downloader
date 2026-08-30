from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

db = SQLAlchemy()


class Playlist(db.Model):
    """Store synced playlists"""
    __tablename__ = 'playlists'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    url = db.Column(db.String(500), nullable=False, unique=True)
    source = db.Column(db.String(20), nullable=False)  # 'spotify' or 'youtube'
    source_id = db.Column(db.String(255), nullable=True)  # Platform-specific ID
    description = db.Column(db.Text, nullable=True)
    folder_path = db.Column(db.String(500), nullable=True)  # Local folder
    
    # Metadata
    track_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_sync_time = db.Column(db.DateTime, nullable=True)
    sync_status = db.Column(db.String(50), default='pending')  # pending, syncing, success, failed
    
    # Relationships
    tracks = db.relationship('Track', backref='playlist', lazy=True, cascade='all, delete-orphan')
    sync_history = db.relationship('SyncHistory', backref='playlist', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Playlist {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'source': self.source,
            'track_count': self.track_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'sync_status': self.sync_status
        }


class Track(db.Model):
    """Store downloaded tracks"""
    __tablename__ = 'tracks'
    
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), nullable=False, index=True)
    
    # Track metadata
    title = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # in seconds
    source_id = db.Column(db.String(255), nullable=True)  # YouTube Track ID
    
    # File information
    filename = db.Column(db.String(500), nullable=True)
    file_path = db.Column(db.String(500), nullable=True)  # Full local path
    file_size = db.Column(db.Integer, nullable=True)  # in bytes
    
    # Status
    download_status = db.Column(db.String(50), default='pending')  # pending, downloading, completed, failed
    download_error = db.Column(db.Text, nullable=True)
    
    # Timestamps
    added_date = db.Column(db.DateTime, default=datetime.utcnow)
    downloaded_date = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Track {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'playlist_id': self.playlist_id,
            'title': self.title,
            'artist': self.artist,
            'duration': self.duration,
            'filename': self.filename,
            'download_status': self.download_status,
            'added_date': self.added_date.isoformat() if self.added_date else None,
            'downloaded_date': self.downloaded_date.isoformat() if self.downloaded_date else None
        }


class SyncHistory(db.Model):
    """Track all sync operations"""
    __tablename__ = 'sync_history'
    
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), nullable=False, index=True)
    
    # Sync details
    sync_type = db.Column(db.String(50), nullable=False)  # 'manual' or 'automatic'
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    
    # Results
    status = db.Column(db.String(50), nullable=False)  # 'success', 'partial', 'failed'
    total_tracks = db.Column(db.Integer, default=0)
    new_tracks = db.Column(db.Integer, default=0)
    updated_tracks = db.Column(db.Integer, default=0)
    failed_tracks = db.Column(db.Integer, default=0)
    
    # Error info
    error_message = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<SyncHistory Playlist:{self.playlist_id} {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'playlist_id': self.playlist_id,
            'sync_type': self.sync_type,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'total_tracks': self.total_tracks,
            'new_tracks': self.new_tracks,
            'updated_tracks': self.updated_tracks,
            'failed_tracks': self.failed_tracks,
            'error_message': self.error_message
        }


class ScheduledSync(db.Model):
    """Store scheduled sync configurations"""
    __tablename__ = 'scheduled_syncs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Schedule
    enabled = db.Column(db.Boolean, default=True)
    day_of_week = db.Column(db.Integer, default=0)  # 0=Monday, 6=Sunday
    time_of_day = db.Column(db.String(5), default='02:00')  # HH:MM format
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_run = db.Column(db.DateTime, nullable=True)
    next_run = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<ScheduledSync {self.day_of_week}:{self.time_of_day}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'enabled': self.enabled,
            'day_of_week': self.day_of_week,
            'time_of_day': self.time_of_day,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None
        }
