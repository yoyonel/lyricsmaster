import codecs
import os

from lyricsmaster import models
from lyricsmaster.utils import normalize
from tests.conftest import real_singer, songs


class TestDiscography:
    """Tests for Discography Class."""

    albums = [models.Album(real_singer['album'], real_singer['name'], songs, '2017'),
              models.Album(real_singer['album'], real_singer['name'], songs, '2017')]
    discography = models.Discography(real_singer['name'], albums)

    def test_discography(self):
        assert self.discography.__repr__() == 'lyricsmaster.models.Discography({0})'.format(
            real_singer['name'])

    def test_discography_isiter(self):
        assert self.discography.__idx__ == 0
        assert len(self.discography) == 2
        assert [elmt for elmt in self.discography] == self.albums
        for x, y in zip(reversed(self.discography),
                        reversed(self.discography.albums)):
            assert x == y

    def test_discography_save(self):
        self.discography.save()
        for album in self.albums:
            for song in album.songs:
                artist = normalize(song.artist)
                album = normalize(song.album)
                title = normalize(song.title)
                path = os.path.join(os.path.expanduser("~"), 'Documents',
                                    'LyricsMaster', artist, album,
                                    title + '.txt')
                assert os.path.exists(path)
                with codecs.open(path, 'r', encoding='utf-8') as file:
                    assert song.lyrics == '\n'.join(file.readlines())
