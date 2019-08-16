import codecs
import os

from lyricsmaster import models
from lyricsmaster.utils import normalize
from tests.conftest import real_singer, songs


class TestAlbums:
    """Tests for Album Class."""

    album = models.Album(real_singer['album'], real_singer['name'], songs, '2017')

    def test_album(self):
        assert self.album.__idx__ == 0
        assert self.album.title == real_singer['album']
        assert self.album.artist == real_singer['name']
        assert self.album.__repr__() == 'lyricsmaster.models.Album({0}, {1})'.format(
            real_singer['album'],
            real_singer['name'])

    def test_album_isiter(self):
        assert len(self.album) == 2
        assert [elmt for elmt in self.album] == songs
        for x, y in zip(reversed(self.album), reversed(self.album.songs)):
            assert x == y

    def test_album_save(self):
        self.album.save()
        for song in self.album.songs:
            artist = normalize(song.artist)
            album = normalize(song.album)
            title = normalize(song.title)
            path = os.path.join(os.path.expanduser("~"), 'Documents',
                                'LyricsMaster', artist, album, title + '.txt')
            assert os.path.exists(path)
            with codecs.open(path, 'r', encoding='utf-8') as file:
                assert song.lyrics == '\n'.join(file.readlines())
