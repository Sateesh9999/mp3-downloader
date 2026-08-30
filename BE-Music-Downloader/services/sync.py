"""Unified sync service for handling playlist synchronization"""
import os
import re
import hashlib
from urllib.parse import parse_qs, urlsplit, urlunsplit
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Tuple, List, Dict, Any
from models import db, Playlist, Track, SyncHistory
from sources import YouTubeSource


class SyncService:
    """Manages playlist synchronization from various sources"""

    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize URLs before duplicate checks and storage."""
        if not url:
            return ''
        value = str(url).strip()
        try:
            parsed = urlsplit(value)
            host = (parsed.hostname or '').lower()
            path = parsed.path.rstrip('/')
            query = parse_qs(parsed.query)

            # Playlist IDs are the stable identifier.  Drop sharing/tracking
            # parameters so the same playlist cannot be added twice.
            if host == 'youtube.com' or host.endswith('.youtube.com'):
                playlist_id = query.get('list', [None])[0]
                return urlunsplit(('https', host, path, f'list={playlist_id}' if playlist_id else '', ''))
            if host == 'youtu.be':
                return urlunsplit(('https', host, path, '', ''))
        except ValueError:
            pass
        return value.rstrip('/')

    @staticmethod
    def safe_playlist_name(name: str, fallback: str = 'Playlist') -> str:
        """Create a safe folder name from metadata, even if the source returns odd characters."""
        raw_name = str(name or '').strip()
        if not raw_name:
            return fallback

        cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', '-', raw_name)
        cleaned = cleaned.strip(' .')
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned or fallback

    @staticmethod
    def detect_source(url: str) -> str:
        """Detect if URL is from YouTube"""
        if YouTubeSource.is_youtube_url(url):
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
            normalized_url = SyncService.normalize_url(url)
            if not normalized_url:
                return False, "Playlist URL is required", None

            source = SyncService.detect_source(normalized_url)
            if not source:
                return False, "URL is not a valid YouTube URL", None

            existing = Playlist.query.filter_by(url=normalized_url).first()
            if existing:
                return False, f"Playlist already synced (ID: {existing.id})", existing

            info = YouTubeSource.get_playlist_info(normalized_url)

            if not info:
                return False, f"Failed to fetch {source} playlist information", None

            safe_name = SyncService.safe_playlist_name(info.get('name'), f'{source.title()} Playlist')
            # Human-readable names are not unique; use a stable suffix to keep
            # playlist folders separate and make file deletion safe.
            folder_key = f"{source}:{info.get('source_id') or normalized_url}"
            folder_suffix = hashlib.sha256(folder_key.encode('utf-8')).hexdigest()[:10]
            playlist_folder = os.path.join(dest_dir, f'{safe_name} [{folder_suffix}]')
            os.makedirs(playlist_folder, exist_ok=True)

            playlist = Playlist(
                name=safe_name,
                url=normalized_url,
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
    def sync_playlist(
        playlist_id: int,
        timeout: int = 300,
        sync_type: str = 'manual',
    ) -> Tuple[bool, str, SyncHistory]:
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
                sync_type=sync_type,
                status='pending'
            )
            db.session.add(sync_history)
            playlist.sync_status = 'syncing'
            db.session.commit()
            
            # Get current tracks in playlist
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
                    # Retry failed downloads on the next sync instead of
                    # permanently excluding the track.
                    if existing_track.download_status == 'failed':
                        existing_track.download_status = 'pending'
                        existing_track.download_error = None
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
            
            tracks_to_download = Track.query.filter_by(
                playlist_id=playlist_id,
                download_status='pending'
            ).all()

            if tracks_to_download:
                download_results = SyncService._download_tracks_in_parallel(
                    playlist,
                    tracks_to_download,
                    timeout=timeout,
                    max_workers=min(8, max(1, len(tracks_to_download)))
                )

                for track in tracks_to_download:
                    try:
                        success, message, file_path = download_results.get(
                            track.id,
                            (False, 'Download did not complete', None)
                        )

                        if success:
                            track.download_status = 'completed'
                            track.file_path = file_path
                            track.filename = os.path.basename(file_path)
                            track.file_size = os.path.getsize(file_path) if file_path and os.path.exists(file_path) else 0
                            track.downloaded_date = datetime.utcnow()
                        else:
                            track.download_status = 'failed'
                            track.download_error = message or 'Download failed'
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
    def _download_tracks_in_parallel(
        playlist: Playlist,
        tracks: List[Track],
        timeout: int = 300,
        max_workers: int = 4,
        download_func=None,
    ) -> Dict[int, Tuple[bool, str, str]]:
        """Download track files concurrently to reduce sync time."""
        if not tracks:
            return {}

        if download_func is None:
            def download_func(playlist_obj, track, track_timeout):
                return YouTubeSource.download_track(
                    track.source_id,
                    playlist_obj.folder_path,
                    track_timeout,
                )

        results: Dict[int, Tuple[bool, str, str]] = {}
        worker_count = min(max_workers, max(1, len(tracks)))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_map = {
                executor.submit(download_func, playlist, track, timeout): track
                for track in tracks
            }

            for future in as_completed(future_map):
                track = future_map[future]
                try:
                    results[track.id] = future.result()
                except Exception as exc:
                    results[track.id] = (False, str(exc), None)

        return results

    @staticmethod
    def sync_all_playlists(
        timeout: int = 300,
        sync_type: str = 'manual',
    ) -> Tuple[bool, str, List[SyncHistory]]:
        """
        Sync all playlists
        Returns: (success, message, list_of_sync_histories)
        """
        playlists = Playlist.query.all()
        results = []
        failures = 0
        
        for playlist in playlists:
            success, message, history = SyncService.sync_playlist(
                playlist.id,
                timeout,
                sync_type=sync_type,
            )
            results.append(history)
            if not success:
                failures += 1
        
        message = f"Synced {len(playlists)} playlists"
        if failures:
            message += f"; {failures} failed"
        return failures == 0, message, results
    
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
