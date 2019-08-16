import os
import sys

import gevent.monkey

from lyricsmaster import AzLyrics, Genius, LyricWiki, Lyrics007, MusixMatch, models


def socket_is_patched():
    return gevent.monkey.is_module_patched('socket')


python_is_outdated = '2.7' in sys.version or '3.3' in sys.version
is_appveyor = 'APPVEYOR' in os.environ
is_travis = 'TRAVIS' in os.environ

providers = [AzLyrics(), MusixMatch(), LyricWiki(), Genius(), Lyrics007()]
# providers_with_search_engine = [
#     provider for provider in providers
#     if provider.name in ('AzLyrics', 'LyricWiki', 'Lyrics007', 'MusixMatch')
# ]
# more difficulties with 'Genius' -> it's a dynamic web site (seems to be
# Angular framework for the front).
# but Genius has an API :p
providers_with_search_engine = providers

real_singer = {
    'name': 'The Notorious B.I.G.', 'album': 'Ready to Die (1994)',
    'songs': [
        {'song': 'Things Done Changed',
         'lyrics': 'Remember back in the days...'},
        {'song': 'Things Done Changed',
         'lyrics': 'Remember back in the days...'}
    ]
}

real_fuzzy_singer = {
    'name': 'Marley Bob',
    'real name': 'Bob Marley'
}

fake_singer = {
    'name': 'Fake Rapper', 'album': "In my mom's basement",
    'song': 'I fap',
    'lyrics': 'Everyday I fap furiously...'
}

provider_strings = {
    'LyricWiki': {'artist_name': 'The_Notorious_B.I.G.',
                  'artist_url': 'http://lyrics.wikia.com/wiki/The_Notorious_B.I.G.',
                  'song_url': 'http://lyrics.wikia.com/wiki/The_Notorious_B.I.G.:Things_Done_Changed',
                  'fake_url': 'http://lyrics.wikia.com/wiki/Things_Done_Changed:Things_Done_Changed_fake_url'},
    'AzLyrics': {'artist_name': 'The Notorious B.I.G.',
                 'artist_url': 'https://www.azlyrics.com/n/notorious.html',
                 'song_url': 'https://www.azlyrics.com/lyrics/notoriousbig/thingsdonechanged.html',
                 'fake_url': 'https://www.azlyrics.com/lyrics/notoriousbig/thingsdonechanged_fake.html'},
    'Genius': {'artist_name': 'The-notorious-big',
               'artist_url': 'https://genius.com/artists/The-notorious-big',
               'song_url': 'https://genius.com/The-notorious-big-things-done-changed-lyrics',
               'fake_url': 'https://genius.com/The-notorious-big-things-done-changed-lyrics_fake'},
    'Lyrics007': {'artist_name': 'The Notorious B.I.G.',
                  'artist_url': 'https://www.lyrics007.com/artist/the-notorious-b-i-g/TVRJMk5EQT0=',
                  'song_url': 'https://www.lyrics007.com/Notorious%20B.i.g.%20Lyrics/Things%20Done%20Changed%20Lyrics.html',
                  'fake_url': 'https://www.lyrics007.com/Notorious%20B.i.g.%20Lyrics/Things%20Done%20Changed%20fake_Lyrics.html'},
    'MusixMatch': {'artist_name': 'The-Notorious-B-I-G',
                   'artist_url': 'https://www.musixmatch.com/artist/The-Notorious-B-I-G',
                   'song_url': 'https://www.musixmatch.com/lyrics/The-Notorious-B-I-G/Things-Done-Changed',
                   'fake_url': 'https://www.musixmatch.com/lyrics/The-Notorious-B-I-G/Things-Done-Changed_fake'},
}

songs = [
    models.Song(real_singer['songs'][0]['song'], real_singer['album'],
                real_singer['name'], real_singer['songs'][0]['lyrics']),
    models.Song(real_singer['songs'][1]['song'], real_singer['album'],
                real_singer['name'], real_singer['songs'][1]['lyrics'])
]
