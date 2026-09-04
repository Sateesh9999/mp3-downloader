"""Unified sync service for handling playlist synchronization"""
import os
import re
import json
import bson
import hashlib
import subprocess
from urllib.parse import parse_qs, urlsplit, urlunsplit
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Tuple, List, Dict, Any, Optional
from bson import ObjectId
from models import db, Playlist, Track, SyncHistory
from sources import YouTubeSource
import asyncio
from shazamio import Shazam
from dataclasses import dataclass

@dataclass
class TrackInfo:
    song_title: str
    artist_name: str
    cover_art_url: str | None
    genre: str | None
    album_name: str | None


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
    def detect_source(url: str) -> Optional[str]:
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

            existing = Playlist.getPlaylistByUrl(normalized_url)
            if existing:
                return False, f"Playlist already synced (ID: {existing['_id']})", existing

            info = YouTubeSource.get_playlist_info(normalized_url)

            if not info:
                return False, f"Failed to fetch {source} playlist information", None

            safe_name = SyncService.safe_playlist_name(info.get('name'), f'{source.title()} Playlist')
            # Human-readable names are not unique; use a stable suffix to keep
            # playlist folders separate and make file deletion safe.
            folder_key = f"{source}:{info.get('source_id') or normalized_url}"
            folder_suffix = hashlib.sha256(folder_key.encode('utf-8')).hexdigest()[:10]
            playlist_folder = dest_dir
            os.makedirs(playlist_folder, exist_ok=True)

            playlist = {
                'name': safe_name,
                'url': normalized_url,
                'source': source,
                'source_id': info.get('source_id'),
                'description': info.get('description'),
                'folder_path': playlist_folder,
                'tracks': [],
                'track_count': 0,
                'sync_status': 'pending',
                'created_at': datetime.utcnow(),
                'last_sync_time': None
            }

            # add to database
            playlist = Playlist.addPlaylist(playlist)
            
            return True, f"Playlist added successfully (ID: {playlist['_id']})", playlist
            
        except Exception as e:
            return False, f"Error adding playlist: {str(e)}", None
    
    @staticmethod
    def extract_album_name(text: str) -> str:
        # First try to find text inside double quotes
        match_quotes = re.search(r'"([^"]+)"', text)
        if match_quotes:
            return match_quotes.group(1)
        
        # If no quotes, try to find text inside parentheses
        match_parentheses = re.search(r'\(([^)]+)\)', text)
        if match_parentheses:
            return match_parentheses.group(1)
        
        # If neither found, return None
        return None


    @staticmethod
    async def get_accurate_metadata(audio_file_path):
        # Initialize the Shazam database client
        shazam = Shazam()
        
        # Generate an acoustic fingerprint and fetch matching metadata
        print(f"Analyzing audio file: {audio_file_path}...")
        track_data = await shazam.recognize(audio_file_path)
        
        # Check if a verifiable match was found
        if 'track' in track_data:
            song_title = track_data['track']['title']
            artist_name = track_data['track']['subtitle']
            cover_art_url = track_data['track']['images']['coverart'] if 'images' in track_data['track'] else None
            genre = track_data['track']['genres']['primary'] if 'genres' in track_data['track'] else None
            album_name = SyncService.extract_album_name(song_title)  # Extract album name from the title if present
            
            return TrackInfo(
                song_title=song_title,
                artist_name=artist_name,
                cover_art_url=cover_art_url,
                genre=genre,
                album_name=album_name
            )

        return None

    @staticmethod
    def sync_playlist(
        playlist_id: ObjectId,
        timeout: int = 300,
        sync_type: str = 'manual',
    ) -> Tuple[bool, str, SyncHistory]:
        """
        Sync a single playlist
        Returns: (success, message, sync_history_object)
        """
        try:
            playlist = Playlist.getPlaylistById(playlist_id)
            if not playlist:
                return False, "Playlist not found", None

            # Create sync history record
            sync_history = {
                'playlist_id': playlist_id,
                'sync_type': sync_type,
                'status': 'pending',
                'start_time': datetime.utcnow(),
                'end_time': None,
                'total_tracks': 0,
                'new_tracks': 0,
                'updated_tracks': 0,
                'failed_tracks': 0,
                'error_message': None
            }
            sync_history = SyncHistory.addSyncHistory(sync_history)
            db['Playlist'].update_one({'_id': playlist_id}, {'$set': {'sync_status': 'syncing'}})

            # Get current tracks in playlist
            tracks = YouTubeSource.get_playlist_tracks(playlist['url'])

            if not tracks:
                db['SyncHistory'].update_one({'_id': sync_history['_id']}, {'$set': {'status': 'failed'}})
                db['SyncHistory'].update_one({'_id': sync_history['_id']}, {'$set': {'error_message': f"Failed to fetch tracks from {playlist['source']}"}})
                db['SyncHistory'].update_one({'_id': sync_history['_id']}, {'$set': {'end_time': datetime.utcnow()}})
                db['Playlist'].update_one({'_id': playlist_id}, {'$set': {'sync_status': 'failed'}})
                return False, "Failed to fetch playlist tracks", sync_history

            # Track counts
            new_tracks = 0
            updated_tracks = 0
            failed_tracks = 0

            # Process each track
            for track_data in tracks:
                # Check if track already exists
                existing_track = Track.getTrackBySourceId(playlist_id, track_data['source_id'])

                if existing_track:
                    updated_tracks += 1
                    # Retry failed downloads on the next sync instead of
                    # permanently excluding the track.
                    if existing_track['download_status'] == 'failed':
                        db['Track'].update_one({'_id': existing_track['_id']}, {'$set': {'download_status': 'pending', 'download_error': None}})
                    else:
                        Playlist.addTrackToPlaylist(playlist_id, existing_track['_id'])
                    continue

                # Create new track record
                track = Track.addTrack({
                    'title': track_data['title'],
                    'artist': track_data.get('artist'),
                    'duration': track_data.get('duration'),
                    'source_id': track_data['source_id'],
                    'download_status': 'pending',
                    'album': None,
                    'cover_art': None,
                    'filename': None,
                    'file_path': None,
                    'file_size': None,
                    'added_date': datetime.utcnow(),
                    'downloaded_date': None
                })
                Playlist.addTrackToPlaylist(playlist_id, track['_id'])

                new_tracks += 1

            tracks_to_download = list(Track.getTracksPending(playlist_id, download_status='pending'))
            print(f"Tracks to download: {len(tracks_to_download)}")  # Debugging line to check the number of tracks to download

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
                            track['_id'],
                            (False, 'Download did not complete', None)
                        )

                        if success:
                            db['Track'].update_one({'_id': track['_id']}, {'$set': {
                                'download_status': 'completed',
                                'file_path': file_path,
                                'filename': os.path.basename(file_path) if file_path else None,
                                'file_size': os.path.getsize(file_path) if file_path and os.path.exists(file_path) else 0,
                                'downloaded_date': datetime.utcnow()
                            }})

                            trackInfo = asyncio.run(SyncService.get_accurate_metadata(file_path))

                            if trackInfo:
                                db['Track'].update_one({'_id': track['_id']}, {'$set': {
                                    'title': trackInfo.song_title,
                                    'artist': trackInfo.artist_name,
                                    'cover_art': trackInfo.cover_art_url,
                                    'album': trackInfo.album_name,
                                    'genre': trackInfo.genre
                                }})

                        else:
                            db['Track'].update_one({'_id': track['_id']}, {'$set': {
                                'download_status': 'failed',
                                'download_error': message or 'Download failed'
                            }})
                            failed_tracks += 1

                    except Exception as e:
                        db['Track'].update_one({'_id': track['_id']}, {'$set': {
                            'download_status': 'failed',
                            'download_error': str(e)
                        }})
                        failed_tracks += 1
            
            # Update sync history
            db['SyncHistory'].update_one({'_id': sync_history['_id']}, {
                '$set': {
                    'status': 'success' if failed_tracks == 0 else 'partial',
                    'total_tracks': len(tracks),
                    'new_tracks': new_tracks,
                    'updated_tracks': updated_tracks,
                    'failed_tracks': failed_tracks,
                    'end_time': datetime.utcnow()
                }
            })
            
            # Update playlist
            db['Playlist'].update_one({'_id': playlist_id}, {
                '$set': {
                    # 'track_count': len(list(Track.getTracksByPlaylistId(playlist_id=playlist_id))),
                    'last_sync_time': datetime.utcnow(),
                    'sync_status': 'success' if failed_tracks == 0 else 'partial'
                }
            })
            
            
            message = f"Sync complete: {new_tracks} new tracks, {updated_tracks} already synced, {failed_tracks} failed"
            return True, message, sync_history
            
        except Exception as e:
            if 'sync_history' in locals():
                db['SyncHistory'].update_one({'_id': sync_history['_id']}, {
                    '$set': {
                        'status': 'failed',
                        'error_message': str(e)
                    }
                })
                db['SyncHistory'].update_one({'_id': sync_history['_id']}, {'$set': {'end_time': datetime.utcnow()}})

            if 'playlist' in locals():
                db['Playlist'].update_one({'_id': playlist_id}, {'$set': {'sync_status': 'failed'}})

            return False, f"Sync error: {str(e)}", sync_history if 'sync_history' in locals() else None
    
    @staticmethod
    def _download_tracks_in_parallel(
        playlist: Playlist,
        tracks: List[Track],
        timeout: int = 300,
        max_workers: int = 4,
        download_func=None,
    ) -> Dict[ObjectId, Tuple[bool, str, str]]:
        """Download track files concurrently to reduce sync time."""
        tracks = list(tracks)  # Ensure we have a list in case a generator is passed
        if not tracks:
            return {}

        if download_func is None:
            def download_func(playlist_obj, track, track_timeout):
                return YouTubeSource.download_track(
                    track['source_id'],
                    playlist_obj['folder_path'],
                    track_timeout,
                )

        results: Dict[ObjectId, Tuple[bool, str, str]] = {}
        worker_count = min(max_workers, max(1, len(tracks)))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_map = {
                executor.submit(download_func, playlist, track, timeout): track
                for track in tracks
            }

            for future in as_completed(future_map):
                track = future_map[future]
                try:
                    results[track['_id']] = future.result()
                except Exception as exc:
                    results[track['_id']] = (False, str(exc), None)

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
        playlists = list(Playlist.getPlaylists())
        results = []
        failures = 0

        for playlist in playlists:
            success, message, history = SyncService.sync_playlist(
                playlist['_id'],
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
    def get_playlist_details(playlist_id: ObjectId) -> Optional[dict]:
        """Get detailed information about a playlist"""
        playlist = Playlist.getPlaylistById(playlist_id)
        if not playlist:
            return None
        
        tracks = list(Track.getTracksByPlaylistId(playlist_id))
        
        return {
            'playlist': playlist,
            'tracks': [track for track in tracks],
            'total_tracks': len(tracks),
            'downloaded_tracks': len([t for t in tracks if t['download_status'] == 'completed']),
            'failed_tracks': len([t for t in tracks if t['download_status'] == 'failed'])
        }
    
    @staticmethod
    def delete_playlist(playlist_id: ObjectId, delete_files: bool = False) -> Tuple[bool, str]:
        """
        Delete a playlist from sync
        Args:
            playlist_id: ID of playlist to delete
            delete_files: If True, also delete downloaded files
        Returns: (success, message)
        """
        try:
            playlist = Playlist.getPlaylistById(playlist_id)
            if not playlist:
                return False, "Playlist not found"
            
            # Delete database records
            playlist = Playlist.deletePlaylist(playlist_id)
            
            return True, f"Playlist '{playlist}' deleted successfully"
            
        except Exception as e:
            return False, f"Error deleting playlist: {str(e)}"
