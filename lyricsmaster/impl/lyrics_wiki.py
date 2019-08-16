import re
from urllib import parse

from bs4 import BeautifulSoup

from lyricsmaster.lyrics_providers import LyricsProvider
from lyricsmaster.models import Song
from lyricsmaster.utils import logger


class LyricWiki(LyricsProvider):
    """
    Class interfacing with http://lyrics.wikia.com .
    This class is used to retrieve lyrics from LyricWiki.

    """
    base_url = 'http://lyrics.wikia.com'
    name = 'LyricWiki'

    def _has_lyrics(self, lyrics_page):
        """
        Checks if the lyrics provider has the lyrics for the song or not.

        :param lyrics_page: BeautifulSoup object.
        :return: bool.
        """
        return not lyrics_page.find("div", {'class': 'noarticletext'})

    _has_artist = _has_lyrics

    def _make_artist_url(self, artist):
        """
        Builds an url for the artist page of the lyrics provider.

        :param artist: string.
        :return: string.
        """
        return self.search(artist)['url']

    def _make_search_artist_url(self, artist):
        """

        :param artist:
        :return:
        """
        return "{}{}{}".format(self.base_url,
                               '/wiki/Special:Search?query=%3Aartist+',
                               self._clean_string(artist))

    def get_album_page(self, artist, album):
        """
        Fetches the album page for the supplied artist and album.

        :param artist: string.
            Artist name.
        :param album: string.
            Album title.
        :return: string or None.
            Album's raw html page. None if the album page was not found.
        """
        artist = self._clean_string(artist)
        album = self._clean_string(album)
        url = self.base_url + '/wiki/' + artist + ':' + album
        raw_html = self.get_page(url).data
        album_page = BeautifulSoup(raw_html.decode('utf-8', 'ignore'), 'lxml')
        if album_page.find("div", {'class': 'noarticletext'}):
            return None
        return raw_html

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
                  artist_page.find_all("span", {'class': 'mw-headline'}) if
                  tag.attrs['id'] not in ('Additional_information',
                                          'External_links')]
        return albums

    def get_album_infos(self, tag):
        """
        Extracts the Album informations from the tag

        :param tag: BeautifulSoup object.
        :return: tuple(string, string).
            Album title and release date.
        """
        try:
            i = tag.text.index(' (')
            release_date = re.findall(r'\(([^()]+)\)', tag.text)[0]
        except ValueError:
            i = -1
            release_date = 'Unknown'
        album_title = tag.text[:i]

        return album_title, release_date

    def get_songs(self, album):
        """
        Fetches the links to the songs of the supplied album.

        :param album: BeautifulSoup object.
        :return: List of BeautifulSoup Link objects.
        """
        parent_node = album.parent
        while parent_node.name != 'ol':
            parent_node = parent_node.next_sibling
        song_links = [elmt.find('a') for elmt in parent_node.find_all('li')]
        return song_links

    def create_song(self, link, artist, album_title):
        """
        Creates a Song object.

        :param link: BeautifulSoup Link object.
        :param artist: string.
        :param album_title: string.
        :return: models.Song object or None.
        """
        song_title = link.attrs['title']
        song_title = song_title[song_title.index(':') + 1:]
        if '(page does not exist' in song_title:
            logger.warning(song_title)
            return None
        if not link.attrs['href'].startswith(self.base_url):
            song_url = self.base_url + link.attrs['href']
        else:
            song_url = link.attrs['href']
        raw_lyrics_page = self.get_lyrics_page(song_url)
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
        :return: string or None.
            Formatted lyrics.
        """
        lyric_box = lyrics_page.find("div", {'class': 'lyricbox'})
        lyrics = '\n'.join(lyric_box.strings)
        return lyrics

    def extract_writers(self, lyrics_page):
        """
        Extracts the writers from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string or None.
            Song writers.
        """
        writers_box = lyrics_page.find("table", {'class': 'song-credit-box'})
        if writers_box:
            writers = writers_box.find_all('p')[-1].text.strip()
        else:
            writers = None
        return writers

    def _extract_artists_from_search(self, search_results_page):
        def _extract_artist_name(artist_url):
            # https://docs.python.org/3/library/urllib.parse.html
            url_path = parse.urlsplit(artist_url).path
            url_tag = url_path.split('/')[-1]
            url_artist_name = url_tag.split(':')[0]
            # https://docs.python.org/3/library/urllib.parse.html#urllib.parse.unquote
            return " ".join(parse.unquote(url_artist_name).split('_'))

        return [
            {
                'name': _extract_artist_name(artist_url),
                'url': artist_url
            }
            for artist_url in map(
                lambda li_node: li_node.find("a").attrs["href"],
                search_results_page.find(
                    "div", {'class': 'results-wrapper grid-3 alpha'}).find(
                    "ul", {'class': 'Results'}).find_all(
                    "li", {'class': 'result'})
            )
        ]

    def _clean_string(self, text):
        """
        Cleans the supplied string and formats it to use in a url.

        :param text: string.
            Text to be cleaned.
        :return: string.
            Cleaned text.
        """
        for elmt in [('#', 'Number_'), ('[', '('), (']', ')'), ('{', '('),
                     ('}', ')'), (' ', '_')]:
            text = text.replace(*elmt)
        return text
