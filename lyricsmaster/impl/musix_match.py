import re

from bs4 import BeautifulSoup

from lyricsmaster.lyrics_providers import LyricsProvider
from lyricsmaster.models import Song


class MusixMatch(LyricsProvider):
    """
    Class interfacing with https://www.musixmatch.com .
    This class is used to retrieve lyrics from MusixMatch.

    """
    base_url = 'https://www.musixmatch.com'
    search_url = base_url + '/search/{0}/artists'
    name = 'MusixMatch'

    def _has_lyrics(self, page):
        """
        Checks if the lyrics provider has the lyrics for the song or not.

        :param page: BeautifulSoup object.
        :return: bool.
        """
        if page.find("div", {'class': 'mxm-lyrics'}):
            return True
        else:
            return False

    def _has_artist(self, page):
        """
        Check if the artist is in the lyrics provider's database.

        :param page: BeautifulSoup object.
        :return: bool.
        """
        if page.find("div", {'class': 'artist-page main-wrapper'}):
            return True
        else:
            return False

    def _make_artist_url(self, artist):
        """
        Builds an url for the artist page of the lyrics provider.

        :param artist: string.
        :return: string.
        """
        # return self.base_url + '/artist/' + artist
        return self.search(artist)['url']

    def _make_search_artist_url(self, artist):
        """

        :param artist:
        :return:
        """
        return self.search_url.format(artist)

    def get_albums(self, raw_artist_page):
        """
        Fetches the albums section in the supplied html page.

        :param raw_artist_page: Artist's raw html page.
        :return: list.
            List of BeautifulSoup objects.
        """
        artist_page = BeautifulSoup(raw_artist_page.decode('utf-8', 'ignore'),
                                    'lxml')
        albums_link = artist_page.find("li", {'id': 'albums'})
        albums_link = albums_link.find('a').attrs['href']
        albums_page = BeautifulSoup(
            self.get_page(self.base_url + albums_link).data.decode('utf-8',
                                                                   'ignore'),
            'lxml')
        albums = [tag for tag in
                  albums_page.find_all("div", {'class': 'media-card-text'})]
        return albums

    def get_album_infos(self, tag):
        """
        Extracts the Album informations from the tag

        :param tag: BeautifulSoup object.
        :return: tuple(string, string).
            Album title and release date.
        """
        album_title = tag.find('h2').text
        try:
            release_date = tag.find('h3').text
        except AttributeError:
            release_date = 'Unknown'
        return album_title, release_date

    def get_songs(self, album):
        """
        Fetches the links to the songs of the supplied album.

        :param album: BeautifulSoup object.
        :return: List of BeautifulSoup Link objects.
        """
        album_page = BeautifulSoup(self.get_page(
            self.base_url + album.find('a').attrs['href']).data.decode('utf-8',
                                                                       'ignore'),
                                   'lxml')
        album_div = album_page.find("div", {
            'class': 'mxm-album__tracks mxm-collection-container'})
        song_links = album_div.find_all("li", {
            'class': re.compile("^mui-collection__item")})
        song_links = [song.find('a') for song in song_links]
        return song_links

    def create_song(self, link, artist, album_title):
        """
        Creates a Song object.

        :param link: BeautifulSoup Link object.
        :param artist: string.
        :param album_title: string.
        :return: models.Song object or None.
        """
        if not link.attrs['href'].startswith(self.base_url):
            song_url = self.base_url + link.attrs['href']
        else:
            song_url = link.attrs['href']
        song_title = link.text
        raw_lyrics_page = self.get_lyrics_page(song_url)
        if not raw_lyrics_page:
            return None
        lyrics_page = BeautifulSoup(raw_lyrics_page.decode('utf-8', 'ignore'),
                                    'lxml')
        lyrics = self.extract_lyrics(lyrics_page)
        if not lyrics:
            return None
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
        lyric_box = lyrics_page.find_all("p", {
            'class': re.compile("^mxm-lyrics__content")})
        if lyric_box:
            lyrics = '\n'.join((elmt.string for elmt in lyric_box))
        else:
            lyrics = None
        return lyrics

    def extract_writers(self, lyrics_page):
        """
        Extracts the writers from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string.
            Song writers or None.
        """
        writers_box = lyrics_page.find("p", {
            'class': re.compile("^mxm-lyrics__copyright")})
        if writers_box:
            writers = writers_box.text.strip()
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
        text = text.replace(' ', '-').replace('.', '-')
        if text[-1] == '-':
            text = text[:-1]
        return text

    def _extract_artists_from_search(self, search_results_page):
        target_node = search_results_page.find(
            "div", {"class": "box-content"}).find_all(
            "div", {"class": "media-card-body"})
        return [
            {
                'name': node_a.get_text(),
                'url': self.base_url + node_a.attrs['href']
            }
            for node_a in map(
                lambda node: node.find("a", {"class": "cover"}),
                target_node
            )
        ]
