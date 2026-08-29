"""YouTube source module - handles YouTube playlist parsing and downloading"""
import os
import subprocess
from typing import List, Dict, Tuple
import re
import json


class YouTubeSource:
    """Handles YouTube playlist parsing and track downloading using yt-dlp"""
    
    @staticmethod
    def is_youtube_url(url: str) -> bool:
        """Check if URL is a YouTube URL"""
        return 'youtube.com' in url.lower() or 'youtu.be' in url.lower()
    
    @staticmethod
    def extract_playlist_id(url: str) -> str:
        """Extract YouTube playlist ID from URL"""
        # URL format: https://www.youtube.com/playlist?list=PLAYLIST_ID
        match = re.search(r'list=([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)
        return None
    
    @staticmethod
    def get_playlist_info(url: str) -> Dict:
        """
        Get YouTube playlist information
        Returns: {name, source_id, description, track_count}
        """
        try:
            command = [
                'yt-dlp',
                '--dump-json',
                '--extract-audio',
                '--audio-format', 'mp3',
                url
            ]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    'name': data.get('title', 'YouTube Playlist'),
                    'source_id': YouTubeSource.extract_playlist_id(url),
                    'description': data.get('description', ''),
                    'track_count': len(data.get('entries', []))
                }
            else:
                return None
                
        except json.JSONDecodeError:
            print("Error parsing yt-dlp JSON output")
            return None
        except Exception as e:
            print(f"Error getting playlist info: {e}")
            return None
    
    @staticmethod
    def get_playlist_tracks(url: str) -> List[Dict]:
        """
        Get all tracks from a YouTube playlist
        Returns: List of {title, artist, source_id, duration}
        """
        try:
            command = [
                'yt-dlp',
                '--dump-json',
                '--flat-playlist',
                url
            ]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                tracks = []
                
                for entry in data.get('entries', []):
                    tracks.append({
                        'title': entry.get('title', 'Unknown'),
                        'artist': entry.get('uploader', 'Unknown'),
                        'source_id': entry.get('id'),
                        'duration': entry.get('duration')
                    })
                
                return tracks
            else:
                return []
                
        except Exception as e:
            print(f"Error getting playlist tracks: {e}")
            return []
    
    @staticmethod
    def download_track(video_id: str, output_dir: str, timeout: int = 300) -> Tuple[bool, str, str]:
        """
        Download a single track from YouTube
        Returns: (success, message, file_path)
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        try:
            # YouTube video URL from ID
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            command = [
                'yt-dlp',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '192',
                '-o', os.path.join(output_dir, '%(title)s.%(ext)s'),
                video_url
            ]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            
            # Extract downloaded file path from output
            output_lines = result.stdout.strip().split('\n')
            file_info = None
            
            for line in output_lines:
                if 'Destination:' in line:
                    file_info = line.split('Destination:')[-1].strip()
                    break
            
            if file_info and os.path.exists(file_info):
                return True, "Download successful", file_info
            else:
                # Try to find the file by searching the output directory
                mp3_files = [f for f in os.listdir(output_dir) if f.endswith('.mp3')]
                if mp3_files:
                    file_path = os.path.join(output_dir, mp3_files[-1])
                    return True, "Download successful", file_path
                
                return False, "File not found after download", None
                
        except subprocess.TimeoutExpired:
            return False, "Download timed out", None
        except subprocess.CalledProcessError as e:
            return False, f"yt-dlp error: {e.stderr}", None
        except FileNotFoundError:
            return False, "yt-dlp not found. Install with: pip install yt-dlp", None
        except Exception as e:
            return False, f"Unexpected error: {str(e)}", None
    
    @staticmethod
    def download_playlist(url: str, output_dir: str, timeout: int = 3600) -> Tuple[bool, str]:
        """
        Download entire YouTube playlist
        Returns: (success, message)
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        try:
            command = [
                'yt-dlp',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '192',
                '-o', os.path.join(output_dir, '%(title)s.%(ext)s'),
                url
            ]
            
            print(f"Downloading YouTube playlist: {url}")
            
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
            return False, f"yt-dlp failed with error: {e.stderr}"
        except FileNotFoundError:
            return False, "yt-dlp not found. Install with: pip install yt-dlp"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
