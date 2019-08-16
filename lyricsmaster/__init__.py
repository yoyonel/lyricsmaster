# -*- coding: utf-8 -*-

"""Top-level package for LyricsMaster."""

__author__ = """SekouD"""
__email__ = 'sekoud.python@gmail.com'
__version__ = '2.8.1'

from lyricsmaster.impl.musix_match import MusixMatch
from lyricsmaster.impl.lyrics007 import Lyrics007
from lyricsmaster.impl.genius import Genius
from lyricsmaster.impl.az_lyrics import AzLyrics
from lyricsmaster.impl.lyrics_wiki import LyricWiki
from .utils import TorController

__all__ = [
    'MusixMatch', 'Lyrics007', 'Genius', 'AzLyrics', 'LyricWiki'
]

CURRENT_PROVIDERS = {
    'lyricwiki': LyricWiki,
    'azlyrics': AzLyrics,
    'genius': Genius,
    'musixmatch': MusixMatch,
    'lyrics007': Lyrics007,
}
