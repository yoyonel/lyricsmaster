try:
    basestring  # Python 2.7 compatibility
except NameError:
    basestring = str

import sys

import pytest
from bs4 import BeautifulSoup, Tag

from lyricsmaster import models
from tests.conftest import (fake_singer, is_appveyor, provider_strings, providers,
                            providers_with_search_engine, real_fuzzy_singer,
                            real_singer)


class TestLyricsProviders:
    """Tests for LyricWiki Class."""

    @pytest.mark.skipif(is_appveyor and '3.3' in sys.version,
                        reason="[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:548) on Appveyor 3.3.")
    @pytest.mark.parametrize('provider', providers)
    def test_get_page(self, provider):
        # Generates unreproducebale errors when when the server does not exist
        # url = 'http://non-existent-url.com'
        # request = provider.get_page(url)
        # assert request is None
        request = provider.get_page('http://www.google.com')
        assert request.status == 200

    @pytest.mark.parametrize('provider', providers)
    def test_clean_string(self, provider):
        assert provider._clean_string(real_singer['name']) == \
               provider_strings[provider.name]['artist_name']

    @pytest.mark.parametrize('provider', providers)
    def test_has_artist(self, provider):
        clean = provider._clean_string
        url = provider._make_artist_url(clean(real_singer['name']))
        page = BeautifulSoup(provider.get_page(url).data, 'lxml')
        assert provider._has_artist(page)
        url = provider._make_artist_url(clean(fake_singer['name']))
        if not url:
            assert url is None
        else:
            page = BeautifulSoup(provider.get_page(url).data, 'lxml')
            assert not provider._has_artist(page)
        pass

    @pytest.mark.parametrize('provider', providers)
    def test_make_artist_url(self, provider):
        clean = provider._clean_string
        assert provider._make_artist_url(clean(real_singer['name'])) == \
               provider_strings[provider.name]['artist_url']

    @pytest.mark.parametrize('provider', providers)
    def test_get_artist_page(self, provider):
        page = provider.get_artist_page(real_singer['name'])
        assert '<!doctype html>' in str(page).lower()
        page = provider.get_artist_page(fake_singer['name'])
        assert page is None

    @pytest.mark.parametrize('provider', providers)
    def test_get_album_page(self, provider):
        if provider.name in ('AzLyrics', 'Genius', 'Lyrics007', 'MusixMatch'):
            return
        else:
            page = provider.get_album_page(real_singer['name'],
                                           fake_singer['album'])
            assert page is None
            page = provider.get_album_page(fake_singer['name'],
                                           fake_singer['album'])
            assert page is None
            page = provider.get_album_page(real_singer['name'],
                                           real_singer['album'])
            assert '<!doctype html>' in str(page).lower()

    @pytest.mark.parametrize('provider', providers)
    def test_has_lyrics(self, provider):
        url = provider_strings[provider.name]['song_url']
        page = BeautifulSoup(provider.get_page(url).data, 'lxml')
        assert provider._has_lyrics(page)
        url = provider_strings[provider.name]['fake_url']
        page = BeautifulSoup(provider.get_page(url).data, 'lxml')
        assert not provider._has_lyrics(page)

    @pytest.mark.parametrize('provider', providers)
    def test_get_lyrics_page(self, provider):
        page = provider.get_lyrics_page(
            provider_strings[provider.name]['song_url'])
        assert '<!doctype html>' in str(page).lower()
        page = provider.get_lyrics_page(
            provider_strings[provider.name]['fake_url'])
        assert page is None

    @pytest.mark.parametrize('provider', providers)
    def test_get_albums(self, provider):
        url = provider_strings[provider.name]['artist_url']
        page = provider.get_page(url).data
        albums = provider.get_albums(page)
        for album in albums:
            assert isinstance(album, Tag)

    @pytest.mark.parametrize('provider', providers)
    def test_get_album_infos(self, provider):
        url = provider_strings[provider.name]['artist_url']
        page = provider.get_page(url).data
        album = provider.get_albums(page)[0]
        album_title, release_date = provider.get_album_infos(album)
        assert isinstance(release_date, basestring)
        # assert album_title.lower() in real_singer['album'].lower() or \
        #        album_title.lower() in 'Demo Tape'.lower() or 'notorious themes' in \
        #        album_title.lower() or 'greatest hits' in album_title.lower()

    @pytest.mark.parametrize('provider', providers)
    def test_extract_lyrics(self, provider):
        page = provider.get_lyrics_page(
            provider_strings[provider.name]['song_url'])
        lyrics_page = BeautifulSoup(page, 'lxml')
        lyrics = provider.extract_lyrics(lyrics_page)
        assert isinstance(lyrics, basestring)
        assert 'Remember back in the days'.lower() in lyrics.lower()
        assert "Don't ask me why I'm".lower() in lyrics.lower()

    @pytest.mark.parametrize('provider', [prov for prov in providers if
                                          not prov.name in ('Lyrics007',
                                                            'LyricWiki')])
    def test_extract_writers(self, provider):
        page = provider.get_lyrics_page(
            provider_strings[provider.name]['song_url'])
        lyrics_page = BeautifulSoup(page, 'lxml')
        writers = provider.extract_writers(lyrics_page)
        assert isinstance(writers, basestring)
        assert "c. wallace" in writers.lower() or "notorious" in writers.lower() \
               or "christopher wallace" in writers.lower() or writers == ''

    @pytest.mark.parametrize('provider', providers)
    def test_get_songs(self, provider):
        artist_page = provider.get_artist_page(real_singer['name'])
        album = provider.get_albums(artist_page)[0]
        song_links = provider.get_songs(album)
        for link in song_links:
            assert isinstance(link, Tag)

    @pytest.mark.parametrize('provider', providers)
    def test_create_song(self, provider):
        artist_page = provider.get_artist_page(real_singer['name'])
        album = provider.get_albums(artist_page)[0]
        song_links = provider.get_songs(album)
        song_links[-1].attrs['href'] = provider_strings[provider.name]['fake_url']
        fail_song = provider.create_song(song_links[-1], real_singer['name'],
                                         real_singer['album'])
        assert fail_song is None
        good_song = provider.create_song(song_links[0], real_singer['name'],
                                         real_singer['album'])
        assert isinstance(good_song, models.Song)
        assert isinstance(good_song.title, basestring)
        assert good_song.album == real_singer['album']
        assert good_song.artist == real_singer['name']
        assert isinstance(good_song.lyrics, basestring)
        # Tests existing song with known empty lyrics
        if provider.name == 'LyricWiki':
            tag = '<a href="http://lyrics.wikia.com/wiki/Reggie_Watts:Feel_The_Same" class="new" title="Reggie Watts:Feel The Same (page does not exist)">Feel the Same</a>'
            page = BeautifulSoup(tag, 'lxml')
            page.attrs[
                'title'] = "Reggie Watts:Feel The Same (page does not exist)"
            page.attrs[
                'href'] = "http://lyrics.wikia.com/wiki/Reggie_Watts:Feel_The_Same"
            non_existent_song = provider.create_song(page, real_singer['name'],
                                                     real_singer['album'])
            assert non_existent_song is None

    @pytest.mark.parametrize('provider', providers)
    def test_get_lyrics(self, provider):
        discography = provider.get_lyrics(fake_singer['name'])
        discography2 = provider.get_lyrics('Reggie Watts', 'Why $#!+ So Crazy?',
                                           'Fuck Shit Stack')
        assert discography is None
        discography = provider.get_lyrics('Reggie Watts', 'Why $#!+ So Crazy?')
        if provider.name == 'AzLyrics':
            assert discography is None
            assert discography2 is None
        else:
            assert isinstance(discography, models.Discography)
            assert isinstance(discography2, models.Discography)

    @pytest.mark.parametrize('provider',
                             providers,
                             ids=[provider.name for provider in providers])
    def test_get_artist_from_fuzzy_name(self, provider):
        fuzzy_artist_name = real_fuzzy_singer['name']
        artist_page = provider.get_artist_page(fuzzy_artist_name)
        if provider in providers_with_search_engine:
            assert '<!doctype html>' in str(artist_page).lower()
        else:
            assert artist_page is None

    @pytest.mark.parametrize('provider',
                             providers_with_search_engine,
                             ids=[provider.name for provider in
                                  providers_with_search_engine])
    def test_get_songs_from_search_artist(self, provider):
        fuzzy_artist_name = real_fuzzy_singer['name']
        artist_page = provider.get_artist_page(fuzzy_artist_name)
        album = provider.get_albums(artist_page)[0]
        song_links = provider.get_songs(album)
        for link in song_links:
            assert isinstance(link, Tag)
