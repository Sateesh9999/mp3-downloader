from pymongo import MongoClient
from config import get_config
from pymongo.server_api import ServerApi
from datetime import datetime
import os

config = get_config()
link = config.MONGO_URI
db = None
try:
    client = MongoClient(link, server_api=ServerApi('1'))
    db = client.music_downloader

  
# return a friendly error if a URI error is thrown 
except Exception as e:
    print("An error occurred while connecting to MongoDB:", e)
    print("An Invalid URI host error was received. Is your Atlas host name correct in your connection string?")
  

class Playlist():
    """Store synced playlists"""

    def getPlaylists():
        return db['Playlist'].find()

    def getPlaylistById(playlist_id):
        return db['Playlist'].find_one({"_id": playlist_id})

    def getPlaylistByUrl(url):
        return db['Playlist'].find_one({"url": url})

    def addPlaylist(playlist):
        result = db['Playlist'].insert_one(playlist)
        playlist['_id'] = result.inserted_id
        return playlist

    def deletePlaylist(playlist_id):
        result = db['Playlist'].delete_one({"_id": playlist_id})
        return result.deleted_count > 0
    
    # id = db.Column(db.Integer, primary_key=True)
    # name = db.Column(db.String(255), nullable=False, index=True)
    # url = db.Column(db.String(500), nullable=False, unique=True)
    # source = db.Column(db.String(20), nullable=False)  # 'spotify' or 'youtube'
    # source_id = db.Column(db.String(255), nullable=True)  # Platform-specific ID
    # description = db.Column(db.Text, nullable=True)
    # folder_path = db.Column(db.String(500), nullable=True)  # Local folder
    
    # # Metadata
    # track_count = db.Column(db.Integer, default=0)
    # created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # last_sync_time = db.Column(db.DateTime, nullable=True)
    # sync_status = db.Column(db.String(50), default='pending')  # pending, syncing, success, failed
    
    # # Relationships
    # tracks = db.relationship('Track', backref='playlist', lazy=True, cascade='all, delete-orphan')
    # sync_history = db.relationship('SyncHistory', backref='playlist', lazy=True, cascade='all, delete-orphan')
    
    # def __repr__(self):
    #     return f'<Playlist {self.name}>'
    
    # def to_dict(self):
    #     return {
    #         'id': self.id,
    #         'name': self.name,
    #         'url': self.url,
    #         'source': self.source,
    #         'track_count': self.track_count,
    #         'created_at': self.created_at.isoformat() if self.created_at else None,
    #         'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
    #         'sync_status': self.sync_status
    #     }


class Track():
    """Store downloaded tracks"""

    def getTracksByPlaylistId(playlist_id):
        return db['Track'].find({"playlist_id": playlist_id})

    def getTrackById(track_id):
        return db['Track'].find_one({"_id": track_id})

    def getTrackBySourceId(playlist_id, source_id):
        return db['Track'].find_one({"playlist_id": playlist_id, "source_id": source_id})

    def getTracksPending(playlist_id, download_status='pending'):
        return db['Track'].find({"playlist_id": playlist_id, "download_status": download_status})

    def addTrack(track):
        result = db['Track'].insert_one(track)
        track['_id'] = result.inserted_id
        return track

    # id = db.Column(db.Integer, primary_key=True)
    # playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), nullable=False, index=True)
    
    # # Track metadata
    # title = db.Column(db.String(255), nullable=False)
    # artist = db.Column(db.String(255), nullable=True)
    # duration = db.Column(db.Integer, nullable=True)  # in seconds
    # source_id = db.Column(db.String(255), nullable=True)  # YouTube Track ID
    
    # # File information
    # filename = db.Column(db.String(500), nullable=True)
    # file_path = db.Column(db.String(500), nullable=True)  # Full local path
    # file_size = db.Column(db.Integer, nullable=True)  # in bytes
    
    # # Status
    # download_status = db.Column(db.String(50), default='pending')  # pending, downloading, completed, failed
    # download_error = db.Column(db.Text, nullable=True)
    
    # # Timestamps
    # added_date = db.Column(db.DateTime, default=datetime.utcnow)
    # downloaded_date = db.Column(db.DateTime, nullable=True)
    
    # def __repr__(self):
    #     return f'<Track {self.title}>'
    
    # def to_dict(self):
    #     return {
    #         'id': self.id,
    #         'playlist_id': self.playlist_id,
    #         'title': self.title,
    #         'artist': self.artist,
    #         'duration': self.duration,
    #         'filename': self.filename,
    #         'download_status': self.download_status,
    #         'added_date': self.added_date.isoformat() if self.added_date else None,
    #         'downloaded_date': self.downloaded_date.isoformat() if self.downloaded_date else None
    #     }


class SyncHistory():
    """Track all sync operations"""

    def addSyncHistory(sync_history):
        result = db['SyncHistory'].insert_one(sync_history)
        sync_history['_id'] = result.inserted_id
        return sync_history

    def getSyncHistoriesByPlaylistId(playlist_id):
        return db['SyncHistory'].find({"playlist_id": playlist_id}).sort("start_time", pymongo.DESCENDING)

    
    # id = db.Column(db.Integer, primary_key=True)
    # playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), nullable=False, index=True)
    
    # # Sync details
    # sync_type = db.Column(db.String(50), nullable=False)  # 'manual' or 'automatic'
    # start_time = db.Column(db.DateTime, default=datetime.utcnow)
    # end_time = db.Column(db.DateTime, nullable=True)
    
    # # Results
    # status = db.Column(db.String(50), nullable=False)  # 'success', 'partial', 'failed'
    # total_tracks = db.Column(db.Integer, default=0)
    # new_tracks = db.Column(db.Integer, default=0)
    # updated_tracks = db.Column(db.Integer, default=0)
    # failed_tracks = db.Column(db.Integer, default=0)
    
    # # Error info
    # error_message = db.Column(db.Text, nullable=True)
    
    # def __repr__(self):
    #     return f'<SyncHistory Playlist:{self.playlist_id} {self.status}>'
    
    # def to_dict(self):
    #     return {
    #         'id': self.id,
    #         'playlist_id': self.playlist_id,
    #         'sync_type': self.sync_type,
    #         'start_time': self.start_time.isoformat() if self.start_time else None,
    #         'end_time': self.end_time.isoformat() if self.end_time else None,
    #         'status': self.status,
    #         'total_tracks': self.total_tracks,
    #         'new_tracks': self.new_tracks,
    #         'updated_tracks': self.updated_tracks,
    #         'failed_tracks': self.failed_tracks,
    #         'error_message': self.error_message
    #     }


class ScheduledSync():
    """Store scheduled sync configurations"""

    def getSchedulerConfig():
        return db['ScheduledSync'].find_one()

    def addSchedulerConfig(config_data):
        result = db['ScheduledSync'].insert_one(config_data)
        config_data['_id'] = result.inserted_id
        return config_data

    # __tablename__ = 'scheduled_syncs'
    
    # id = db.Column(db.Integer, primary_key=True)
    
    # # Schedule
    # enabled = db.Column(db.Boolean, default=True)
    # day_of_week = db.Column(db.Integer, default=0)  # 0=Monday, 6=Sunday
    # time_of_day = db.Column(db.String(5), default='02:00')  # HH:MM format
    
    # # Metadata
    # created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # last_run = db.Column(db.DateTime, nullable=True)
    # next_run = db.Column(db.DateTime, nullable=True)
    
    # def __repr__(self):
    #     return f'<ScheduledSync {self.day_of_week}:{self.time_of_day}>'
    
    # def to_dict(self):
    #     return {
    #         'id': self.id,
    #         'enabled': self.enabled,
    #         'day_of_week': self.day_of_week,
    #         'time_of_day': self.time_of_day,
    #         'last_run': self.last_run.isoformat() if self.last_run else None,
    #         'next_run': self.next_run.isoformat() if self.next_run else None
    #     }
