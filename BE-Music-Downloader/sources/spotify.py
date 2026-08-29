"""Spotify source module - handles Spotify playlist parsing and downloading"""
import os
import subprocess
from typing import List, Dict, Tuple
import re


class SpotifySource:
    """Handles Spotify playlist parsing and track downloading using spotdl"""
    
    @staticmethod
    def is_spotify_url(url: str) -> bool:
        """Check if URL is a Spotify URL"""
        return 'spotify.com' in url.lower()
    
    @staticmethod
    def extract_playlist_id(url: str) -> str:
        """Extract Spotify playlist ID from URL"""
        # URL format: https://open.spotify.com/playlist/PLAYLIST_ID?si=...
        match = re.search(r'playlist/([a-zA-Z0-9]+)', url)
        if match:
            return match.group(1)
        return None
    
    @staticmethod
    def get_playlist_info(url: str) -> Dict:
        """
        Get Spotify playlist information
        Returns: {name, source_id, description, track_count}
        """
        try:
            # Use spotdl to fetch playlist info
            result = subprocess.run(
                ['spotdl', '--info', url],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse output (spotdl info returns JSON or text format)
                # For now, return basic info
                return {
                    'name': 'Spotify Playlist',
                    'source_id': SpotifySource.extract_playlist_id(url),
                    'description': '',
                    'track_count': 0
                }
            else:
                raise Exception(f"spotdl info failed: {result.stderr}")
                
        except Exception as e:
            print(f"Error getting playlist info: {e}")
            return None
    
    @staticmethod
    def get_playlist_tracks(url: str) -> List[Dict]:
        """
        Get all tracks from a Spotify playlist
        Returns: List of {title, artist, source_id, duration}
        """
        try:
            # Use spotdl to fetch track list
            # This would require parsing spotdl output or using Spotify API
            # For now, return empty list (will be enhanced with actual API)
            return []
            
        except Exception as e:
            print(f"Error getting playlist tracks: {e}")
            return []
    
    @staticmethod
    def download_track(spotify_uri: str, output_dir: str, timeout: int = 300) -> Tuple[bool, str, str]:
        """
        Download a single track from Spotify
        Returns: (success, message, file_path)
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        try:
            command = [
                'spotdl',
                'download',
                spotify_uri,
                '--output',
                output_dir
            ]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            
            # spotdl returns the file path in output
            output_lines = result.stdout.strip().split('\n')
            file_path = output_lines[-1] if output_lines else None
            
            if os.path.exists(file_path):
                return True, "Download successful", file_path
            else:
                return False, "File not found after download", None
                
        except subprocess.TimeoutExpired:
            return False, "Download timed out", None
        except subprocess.CalledProcessError as e:
            return False, f"spotdl error: {e.stderr}", None
        except FileNotFoundError:
            return False, "spotdl not found. Install with: pip install spotdl", None
        except Exception as e:
            return False, f"Unexpected error: {str(e)}", None
    
    @staticmethod
    def download_playlist(url: str, output_dir: str, timeout: int = 600) -> Tuple[bool, str]:
        """
        Download entire Spotify playlist
        Returns: (success, message)
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        try:
            command = [
                'spotdl',
                'download',
                url,
                '--output',
                output_dir
            ]
            
            print(f"Downloading Spotify playlist: {url}")
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            
            return True, "Playlist downloaded successfully"
            
        except subprocess.TimeoutExpired:
            return False, "Download timed out (exceeded time limit)"
        except subprocess.CalledProcessError as e:
            return False, f"spotdl failed with error: {e.stderr}"
        except FileNotFoundError:
            return False, "spotdl not found. Install with: pip install spotdl"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
