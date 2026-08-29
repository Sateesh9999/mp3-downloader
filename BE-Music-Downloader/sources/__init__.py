"""Sources package for handling different music sources"""
from .spotify import SpotifySource
from .youtube import YouTubeSource

__all__ = ['SpotifySource', 'YouTubeSource']
