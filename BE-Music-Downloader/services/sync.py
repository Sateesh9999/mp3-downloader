"""Unified sync service for handling playlist synchronization"""
import os
from datetime import datetime
from typing import Tuple, List
from models import db, Playlist, Track, SyncHistory
from sources import SpotifySource, YouTubeSource


class SyncService:
    """Manages playlist synchronization from various sources"""
    
    @staticmethod
    def detect_source(url: str) -> str:
        """Detect if URL is from Spotify or YouTube"""
        if SpotifySource.is_spotify_url(url):
            return 'spotify'
        elif YouTubeSource.is_youtube_url(url):
            return 'youtube'
        else:
            return None
    
    @staticmethod
    def add_playlist(url: str, dest_dir: str) -> Tuple[bool, str, Playlist]:
        """
        Add a new playlist to sync
        Returns: (success, message, playlist_object)
        """
        try:
            # Detect source
            source = SyncService.detect_source(url)
            if not source:
                return False, "URL is not a valid Spotify or YouTube URL", None
            
            # Check if already exists
            existing = Playlist.query.filter_by(url=url).first()
            if existing:
                return False, f"Playlist already synced (ID: {existing.id})", existing
            
            # Get playlist info
            if source == 'spotify':
                info = SpotifySource.get_playlist_info(url)
            else:
                info = YouTubeSource.get_playlist_info(url)
            
            if not info:
                return False, f"Failed to fetch {source} playlist information", None
            
            # Create folder for playlist
            playlist_folder = os.path.join(dest_dir, info['name'])
            if not os.path.exists(playlist_folder):
                os.makedirs(playlist_folder)
            
            # Create playlist record
            playlist = Playlist(
                name=info['name'],
                url=url,
                source=source,
                source_id=info.get('source_id'),
                description=info.get('description'),
                folder_path=playlist_folder,
                track_count=info.get('track_count', 0),
                sync_status='pending'
            )
            
            db.session.add(playlist)
            db.session.commit()
            
            return True, f"Playlist added successfully (ID: {playlist.id})", playlist
            
        except Exception as e:
            return False, f"Error adding playlist: {str(e)}", None
    
    @staticmethod
    def sync_playlist(playlist_id: int, timeout: int = 300) -> Tuple[bool, str, SyncHistory]:
        """
        Sync a single playlist
        Returns: (success, message, sync_history_object)
        """
        try:
            playlist = Playlist.query.get(playlist_id)
            if not playlist:
                return False, "Playlist not found", None
            
            # Create sync history record
            sync_history = SyncHistory(
                playlist_id=playlist_id,
                sync_type='manual',
                status='pending'
            )
            db.session.add(sync_history)
            playlist.sync_status = 'syncing'
            db.session.commit()
            
            # Get current tracks in playlist
            if playlist.source == 'spotify':
                tracks = SpotifySource.get_playlist_tracks(playlist.url)
            else:
                tracks = YouTubeSource.get_playlist_tracks(playlist.url)
            
            if not tracks:
                sync_history.status = 'failed'
                sync_history.error_message = f"Failed to fetch tracks from {playlist.source}"
                sync_history.end_time = datetime.utcnow()
                playlist.sync_status = 'failed'
                db.session.commit()
                return False, "Failed to fetch playlist tracks", sync_history
            
            # Track counts
            new_tracks = 0
            updated_tracks = 0
            failed_tracks = 0
            
            # Process each track
            for track_data in tracks:
                # Check if track already exists
                existing_track = Track.query.filter_by(
                    playlist_id=playlist_id,
                    source_id=track_data['source_id']
                ).first()
                
                if existing_track:
                    updated_tracks += 1
                    continue
                
                # Create new track record
                track = Track(
                    playlist_id=playlist_id,
                    title=track_data['title'],
                    artist=track_data.get('artist'),
                    duration=track_data.get('duration'),
                    source_id=track_data['source_id'],
                    download_status='pending'
                )
                
                db.session.add(track)
                new_tracks += 1
            
            # Download new tracks
            tracks_to_download = Track.query.filter_by(
                playlist_id=playlist_id,
                download_status='pending'
            ).all()
            
            for track in tracks_to_download:
                try:
                    if playlist.source == 'spotify':
                        # For Spotify, use the source_id directly
                        success, message, file_path = SpotifySource.download_track(
                            track.source_id,
                            playlist.folder_path,
                            timeout
                        )
                    else:
                        # For YouTube, use video ID
                        success, message, file_path = YouTubeSource.download_track(
                            track.source_id,
                            playlist.folder_path,
                            timeout
                        )
                    
                    if success:
                        track.download_status = 'completed'
                        track.file_path = file_path
                        track.filename = os.path.basename(file_path)
                        track.file_size = os.path.getsize(file_path)
                        track.downloaded_date = datetime.utcnow()
                    else:
                        track.download_status = 'failed'
                        track.download_error = message
                        failed_tracks += 1
                        
                except Exception as e:
                    track.download_status = 'failed'
                    track.download_error = str(e)
                    failed_tracks += 1
            
            # Update sync history
            sync_history.status = 'success' if failed_tracks == 0 else 'partial'
            sync_history.total_tracks = len(tracks)
            sync_history.new_tracks = new_tracks
            sync_history.updated_tracks = updated_tracks
            sync_history.failed_tracks = failed_tracks
            sync_history.end_time = datetime.utcnow()
            
            # Update playlist
            playlist.track_count = Track.query.filter_by(playlist_id=playlist_id).count()
            playlist.last_sync_time = datetime.utcnow()
            playlist.sync_status = 'success' if failed_tracks == 0 else 'partial'
            
            db.session.commit()
            
            message = f"Sync complete: {new_tracks} new tracks, {updated_tracks} already synced, {failed_tracks} failed"
            return True, message, sync_history
            
        except Exception as e:
            if 'sync_history' in locals():
                sync_history.status = 'failed'
                sync_history.error_message = str(e)
                sync_history.end_time = datetime.utcnow()
            
            if 'playlist' in locals():
                playlist.sync_status = 'failed'
            
            db.session.commit()
            return False, f"Sync error: {str(e)}", sync_history if 'sync_history' in locals() else None
    
    @staticmethod
    def sync_all_playlists(timeout: int = 300) -> Tuple[bool, str, List[SyncHistory]]:
        """
        Sync all playlists
        Returns: (success, message, list_of_sync_histories)
        """
        playlists = Playlist.query.all()
        results = []
        
        for playlist in playlists:
            success, message, history = SyncService.sync_playlist(playlist.id, timeout)
            results.append(history)
        
        message = f"Synced {len(playlists)} playlists"
        return True, message, results
    
    @staticmethod
    def get_playlist_details(playlist_id: int) -> dict:
        """Get detailed information about a playlist"""
        playlist = Playlist.query.get(playlist_id)
        if not playlist:
            return None
        
        tracks = Track.query.filter_by(playlist_id=playlist_id).all()
        
        return {
            'playlist': playlist.to_dict(),
            'tracks': [track.to_dict() for track in tracks],
            'total_tracks': len(tracks),
            'downloaded_tracks': len([t for t in tracks if t.download_status == 'completed']),
            'failed_tracks': len([t for t in tracks if t.download_status == 'failed'])
        }
    
    @staticmethod
    def delete_playlist(playlist_id: int, delete_files: bool = False) -> Tuple[bool, str]:
        """
        Delete a playlist from sync
        Args:
            playlist_id: ID of playlist to delete
            delete_files: If True, also delete downloaded files
        Returns: (success, message)
        """
        try:
            playlist = Playlist.query.get(playlist_id)
            if not playlist:
                return False, "Playlist not found"
            
            # Delete files if requested
            if delete_files and os.path.exists(playlist.folder_path):
                import shutil
                shutil.rmtree(playlist.folder_path)
            
            # Delete database records
            db.session.delete(playlist)
            db.session.commit()
            
            return True, f"Playlist '{playlist.name}' deleted successfully"
            
        except Exception as e:
            return False, f"Error deleting playlist: {str(e)}"
