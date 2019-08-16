import codecs
import os

from lyricsmaster.utils import normalize
from tests.conftest import real_singer, songs


class TestSongs:
    """Tests for Song Class."""
    song = songs[0]

    def test_song(self):
        assert self.song.__repr__() == 'lyricsmaster.models.Song({0}, {1}, {2})'.format(
            real_singer['songs'][0]['song'],
            real_singer['album'],
            real_singer['name'])

    def test_song_save(self):
        self.song.save()
        path = os.path.join(os.path.expanduser("~"), 'Documents',
                            'LyricsMaster', normalize(real_singer['name']),
                            normalize(real_singer['album']),
                            'Things-Done-Changed.txt')
        assert os.path.exists(path)
        folder = os.path.join(os.path.expanduser("~"), 'Documents',
                              'test_lyricsmaster_save')
        self.song.save(folder)
        path = os.path.join(folder, 'LyricsMaster',
                            normalize(real_singer['name']),
                            normalize(real_singer['album']),
                            'Things-Done-Changed.txt')
        assert os.path.exists(path)
        with codecs.open(path, 'r', encoding='utf-8') as file:
            assert self.song.lyrics == file.readlines()[0]
