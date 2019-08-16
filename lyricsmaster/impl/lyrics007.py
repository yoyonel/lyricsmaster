from bs4 import BeautifulSoup

from lyricsmaster.lyrics_providers import LyricsProvider
from lyricsmaster.models import Song


class Lyrics007(LyricsProvider):
    """
    Class interfacing with https://www.lyrics007.com .
    This class is used to retrieve lyrics from Lyrics007.

    """
    base_url = 'https://www.lyrics007.com'
    search_url = base_url + '/search.php?category=artist&q='
    name = 'Lyrics007'

    def _has_lyrics(self, page):
        """
        Checks if the lyrics provider has the lyrics for the song or not.

        :param page: BeautifulSoup object.
        :return: bool.
        """
        if page.find("div", {'class': 'lyrics'}):
            return True
        else:
            return False

    def _has_artist(self, page):
        """
        Check if the artist is in the lyrics provider's database.

        :param page: BeautifulSoup object
        :return: bool.
        """
        if page.find("ul", {'class': 'song_title'}):
            return True
        else:
            return False

    def _has_artist_result(self, page):
        """
        Check if the artist is in the lyrics provider's database.

        :param page: BeautifulSoup object.
        :return: bool.
        """
        artist_link = page.find("div", {'id': 'search_result'}).find('a')
        if artist_link:
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
        """

        :param artist:
        :return:
        """
        artist = "".join([c if (c.isalnum() or c == '.') else "+"
                          for c in artist])
        url = self.search_url + artist
        return url

    def get_albums(self, raw_artist_page):
        """
        Fetches the albums section in the supplied html page.

        :param raw_artist_page: Artist's raw html page.
        :return: list.
            List of BeautifulSoup objects.
        """
        artist_page = BeautifulSoup(raw_artist_page.decode('utf-8', 'ignore'),
                                    'lxml')
        content = artist_page.find("div", {'class': 'content'})
        albums = [tag for tag in content.find_all('li', recursive=False)]
        return albums

    def get_album_infos(self, tag):
        """
        Extracts the Album informations from the tag

        :param tag: BeautifulSoup object.
        :return: tuple(string, string).
            Album title and release date.
        """
        infos = tag.text.split(': ')
        if len(infos) == 2:
            release_date, album_title = infos
        else:
            release_date = 'Unknown'
            album_title = infos[0]
        return album_title, release_date

    def get_songs(self, album):
        """
        Fetches the links to the songs of the supplied album.

        :param album: BeautifulSoup object.
        :return: List of BeautifulSoup Link objects.
        """
        target_node = album.find_next_sibling("ul")
        song_links = [elmt.find('a') for elmt in target_node.find_all('li') if
                      elmt.find('a')]
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
        markup = raw_lyrics_page.decode('utf-8', 'ignore')
        lyrics_page = BeautifulSoup(markup, 'lxml')
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
        lyric_box = lyrics_page.find("div", {'class': 'lyrics'})
        lyrics = '\n'.join(lyric_box.strings)
        return lyrics

    def extract_writers(self, lyrics_page):
        """
        Extracts the writers from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string.
            Song writers or None.
        """
        writers_box = [elmt for elmt in lyrics_page.strings if
                       elmt.lower().startswith(
                           'writers:') or elmt.lower().startswith('writer:')]
        if writers_box:
            writers = writers_box[0].strip()
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

    def _extract_artists_from_search(self, search_results_page):
        target_node = search_results_page.find("div", {'id': 'search_result'})
        return [{
            'url': self.base_url + node_a.attrs['href'],
            'name': node_a.get_text()}
            for node_a in map(lambda node: node.find('a'),
                              target_node.find_all('h2'))
        ]
