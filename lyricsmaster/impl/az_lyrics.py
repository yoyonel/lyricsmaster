import re
from urllib import parse

from bs4 import BeautifulSoup

from lyricsmaster.lyrics_providers import LyricsProvider
from lyricsmaster.models import Song


class AzLyrics(LyricsProvider):
    """
    Class interfacing with https://azlyrics.com .
    This class is used to retrieve lyrics from AzLyrics.

    """
    base_url = 'https://www.azlyrics.com'
    search_url = 'https://search.azlyrics.com/search.php?q='
    name = 'AzLyrics'

    def _has_lyrics(self, lyrics_page):
        """
        Checks if the lyrics provider has the lyrics for the song or not.

        :param lyrics_page: BeautifulSoup object.
        :return: bool.
        """
        if lyrics_page.find("div", {'class': 'lyricsh'}):
            return True
        else:
            return False

    def _has_artist(self, page):
        """
        Check if the artist is in the lyrics provider's database.

        :param page: BeautifulSoup object.
        :return: bool.
        """
        if page.find("div", {'id': 'listAlbum'}):
            return True
        else:
            return False

    def _has_artist_result(self, page):
        """
        Checks if the lyrics provider has the lyrics for the song or not.

        :param page: BeautifulSoup object.
        :return: bool.
        """
        artist_result = page.find("div", {'class': 'panel-heading'})
        if artist_result.find('b').text == 'Artist results:':
            return True
        else:
            return False

    def _has_song_result(self, page):
        """
        Checks if the lyrics provider has the lyrics for the song or not.

        :param page: BeautifulSoup object.
        :return: bool.
        """
        artist_result = page.find("div", {'class': 'panel-heading'})
        if artist_result.find('b').text == 'Song results:':
            return True
        else:
            return False

    def _make_artist_url(self, artist):
        """
        Builds an url for the artist page of the lyrics provider.

        :param artist: string.
        :return: string.
        """
        return self.search(artist)['url']

    def _make_search_artist_url(self, artist):
        return self.search_url + artist

    def _extract_artists_from_search(self, search_results_page):
        target_node = search_results_page.find("div", {
            'class': 'panel-heading'}).find_next_sibling("table")
        return [
            {
                'name': node_a.find('b').get_text(),
                'url': node_a.attrs['href']
            }
            for node_a in target_node.find_all('a')
            if node_a.find('b') is not None
        ]

    def get_albums(self, raw_artist_page):
        """
        Fetches the albums section in the supplied html page.

        :param raw_artist_page: Artist's raw html page.
        :return: list.
            List of BeautifulSoup objects.
        """
        artist_page = BeautifulSoup(raw_artist_page.decode('utf-8', 'ignore'),
                                    'lxml')
        albums = [tag for tag in
                  artist_page.find_all("div", {'id': 'listAlbum'})]
        return albums

    def get_album_infos(self, tag):
        """
        Extracts the Album informations from the tag

        :param tag: BeautifulSoup object.
        :return: tuple(string, string).
            Album title and release date.
        """
        album_infos = tag.find("div", {'class': 'album'}).text
        album_title = re.findall(r'"([^"]*)"', album_infos)[0]
        try:
            release_date = re.findall(r'\(([^()]+)\)', tag.text)[0]
        except ValueError:
            release_date = 'Unknown'
        return album_title, release_date

    def get_songs(self, album):
        """
        Fetches the links to the songs of the supplied album.

        :param album: BeautifulSoup object.
        :return: List of BeautifulSoup Link objects.
        """
        song_links = album.find_all('a')
        song_links = [song for song in song_links if 'href' in song.attrs]
        return song_links

    def create_song(self, link, artist, album_title):
        """
        Creates a Song object.

        :param link: BeautifulSoup Link object.
        :param artist: string.
        :param album_title: string.
        :return: models.Song object or None.
        """
        song_title = link.text
        raw_lyrics_page = self.get_lyrics_page(
            self.base_url + link.attrs['href'].replace('..', ''))
        if not raw_lyrics_page:
            return None
        lyrics_page = BeautifulSoup(raw_lyrics_page.decode('utf-8', 'ignore'),
                                    'lxml')
        lyrics = self.extract_lyrics(lyrics_page)
        writers = self.extract_writers(lyrics_page)
        song = Song(song_title, album_title, artist, lyrics, writers)
        return song

    def extract_lyrics(self, lyrics_page):
        """
        Extracts the lyrics from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string.
            Formatted lyrics.
        """
        lyric_box = lyrics_page.find("div", {"class": None, "id": None})
        lyrics = ''.join(lyric_box.strings)
        return lyrics

    def extract_writers(self, lyrics_page):
        """
        Extracts the writers from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string or None.
            Song writers or None.
        """
        writers_box = lyrics_page.find_all("div", {'class': 'smt'})
        if writers_box:
            writers = writers_box[-1].text.strip()
        else:
            writers = None
        return writers

    def _clean_string(self, text):
        """
        Cleans the supplied string and formats it to use in a url.

        :param text: string.
            Text to be cleaned.
        :return: string.
            Cleaned text.
        """
        return text
