import time
import urllib
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from lyricsmaster.lyrics_providers import LyricsProvider
from lyricsmaster.models import Song
# from lyricsmaster.utils import normalize


class Genius(LyricsProvider):
    """
    Class interfacing with https://genius.com .
    This class is used to retrieve lyrics from Genius.

    """
    base_url = 'https://genius.com'
    search_url = base_url + '/search?q='
    name = 'Genius'

    def _has_lyrics(self, page):
        """
        Checks if the lyrics provider has the lyrics for the song or not.

        :param page: BeautifulSoup object.
        :return: bool.
        """
        if page.find("div", {'class': 'song_body-lyrics'}):
            return True
        else:
            return False

    def _has_artist(self, page):
        """
        Check if the artist is in the lyrics provider's database.

        :param page: BeautifulSoup object.
        :return: bool.
        """
        if not page.find("div", {'class': 'render_404'}):
            return True
        else:
            return False

    def _make_artist_url(self, artist):
        """
        Builds an url for the artist page of the lyrics provider.

        :param artist: string.
        :return: string.
        """

        # url = self.base_url + '/artists/' + artist
        # return url
        # return self.search(artist)['url']

        # Genius API:
        # https://docs.genius.com/#/getting-started-h1
        # https://github.com/johnwmillr/LyricsGenius/blob/master/lyricsgenius/api.py
        def _get_item_from_search_response(response, type_):
            """ Returns either a Song or Artist result from search_genius_web """
            # Convert list to dictionary
            hits = response['sections'][0]['hits']
            if hits:
                tophit = hits[0]
                if tophit['type'] == type_:
                    return tophit['result']

            # Check rest of results if top hit wasn't the search type
            sections = sorted(response['sections'],
                              key=lambda sect: sect['type'] == type_,
                              reverse=True)
            for section in sections:
                hits = [hit for hit in section['hits'] if hit['type'] == type_]
                if hits:
                    return hits[0]['result']

        def search_genius_web(search_term, per_page=5):
            """Use the web-version of Genius search"""
            endpoint = "search/multi?"
            params = {'per_page': per_page, 'q': search_term}

            # This endpoint is not part of the API, requires different formatting
            url = "https://genius.com/api/" + endpoint + urlencode(params)
            _SLEEP_MIN = 0.2
            timeout = 5
            sleep_time = 0.5
            response = requests.get(url, timeout=timeout)
            time.sleep(max(_SLEEP_MIN, sleep_time))
            return response.json()['response'] if response else None

        found_artist = _get_item_from_search_response(
            response=search_genius_web(artist),
            type_="artist"
        )

        return found_artist['url']

    def _make_search_artist_url(self, artist):
        """

        :param artist:
        :return:
        """
        return "{}{}".format(self.search_url, artist)

    def get_albums(self, raw_artist_page):
        """
        Fetches the albums section in the supplied html page.

        :param raw_artist_page: Artist's raw html page.
        :return: list.
            List of BeautifulSoup objects.
        """
        artist_page = BeautifulSoup(raw_artist_page.decode('utf-8', 'ignore'),
                                    'lxml')
        albums_link = artist_page.find("a", {'class': 'full_width_button'})
        albums_link = albums_link.attrs['href'].replace('songs?', 'albums?')
        albums_page = BeautifulSoup(
            self.get_page(self.base_url + albums_link).data.decode('utf-8',
                                                                   'ignore'),
            'lxml')
        albums = [tag for tag in
                  albums_page.find_all("a", {'class': 'album_link'})]
        return albums

    def get_album_infos(self, tag):
        """
        Extracts the Album informations from the tag

        :param tag: BeautifulSoup object.
        :return: tuple(string, string).
            Album title and release date.
        """
        album_title = tag.text
        album_page = BeautifulSoup(
            self.get_page(self.base_url + tag.attrs['href']).data.decode(
                'utf-8', 'ignore'), 'lxml')
        info_box = album_page.find("div", {
            'class': 'header_with_cover_art-primary_info'})
        metadata = [elmt for elmt in
                    info_box.find_all("div", {'class': 'metadata_unit'}) if
                    elmt.text.startswith('Released')]
        try:
            release_date = metadata[0].text
        except IndexError:
            release_date = 'Unknown'
        except ValueError:
            release_date = 'Unknown'
        return album_title, release_date

    def get_songs(self, album):
        """
        Fetches the links to the songs of the supplied album.

        :param album: BeautifulSoup object.
        :return: List of BeautifulSoup Link objects.
        """
        album_page = BeautifulSoup(
            self.get_page(self.base_url + album.attrs['href']).data.decode(
                'utf-8', 'ignore'), 'lxml')
        song_links = album_page.find_all("div", {
            'class': 'chart_row chart_row--light_border chart_row--full_bleed_left chart_row--align_baseline chart_row--no_hover'})
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
        song_title = link.text.strip('\n').split('\n')[0].lstrip()
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
        :return: string.
            Formatted lyrics.
        """
        lyric_box = lyrics_page.find("div", {"class": 'lyrics'})
        lyrics = ''.join(lyric_box.strings)
        return lyrics

    def extract_writers(self, lyrics_page):
        """
        Extracts the writers from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string.
            Song writers or None.
        """
        writers_box = [elmt for elmt in lyrics_page.find_all("span", {
            'class': 'metadata_unit-label'}) if elmt.text == "Written By"]
        if writers_box:
            target_node = writers_box[0].find_next_sibling("span", {
                'class': 'metadata_unit-info'})
            writers = target_node.text.strip()
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
        # text = normalize(text).lower().capitalize()
        # text = urllib.parse.quote(text)
        return text

    def _extract_artists_from_search(self, search_results_page):
        target_node = search_results_page.find("div", {'id': 'search_result'})
        return [{
            'url': self.base_url + node_a.attrs['href'],
            'name': node_a.get_text()}
            for node_a in map(lambda node: node.find('a'),
                              target_node.find_all('h2'))
        ]
