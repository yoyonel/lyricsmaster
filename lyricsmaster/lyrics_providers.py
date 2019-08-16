from abc import ABCMeta, abstractmethod
from typing import Dict
from urllib.parse import urlsplit, quote, urlunsplit

import certifi
import gevent.monkey
import urllib3
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from gevent.pool import Pool

from lyricsmaster.models import Album, Discography
from lyricsmaster.utils import logger


class LyricsProvider:
    """
    This is the base class for all Lyrics Providers.
    If you wish to subclass this class,
    you must implement all the methods defined in this class
    to be compatible with the LyricsMaster API.
    Requests to fetch songs are executed asynchronously for better performance.
    Tor anonymisation is provided if tor is installed on the system and
    a TorController is passed at instance creation.

    :param tor_controller: TorController Object.

    """
    __metaclass__ = ABCMeta
    name = ''

    def __init__(self, tor_controller=None):
        if not self.__socket_is_patched():
            gevent.monkey.patch_socket()
        self.tor_controller = tor_controller
        if not self.tor_controller:
            user_agent = {
                'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
            }
            self.session = urllib3.PoolManager(maxsize=10,
                                               cert_reqs='CERT_REQUIRED',
                                               ca_certs=certifi.where(),
                                               headers=user_agent)
        else:
            self.session = self.tor_controller.get_tor_session()
        self.__tor_status__()

    def __repr__(self):
        return '{0}.{1}({2})'.format(__name__, self.__class__.__name__,
                                     self.tor_controller.__repr__())

    def __tor_status__(self):
        """
        Informs the user of the Tor status.

        """
        if not self.tor_controller:
            logger.info('Anonymous requests disabled. '
                        'The connexion will not be anonymous.')
        elif self.tor_controller and not self.tor_controller.controlport:
            logger.info('Anonymous requests enabled. '
                        'The Tor circuit will change according to '
                        'the Tor network defaults.')
        else:
            logger.info('Anonymous requests enabled. '
                        'The Tor circuit will change for each album.')

    def __socket_is_patched(self):
        """
        Checks if the socket is patched or not.

        :return: bool.
        """
        return gevent.monkey.is_module_patched('socket')

    @abstractmethod
    def _has_lyrics(self, page):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Checks if the lyrics provider has the lyrics for the song or not.

        :param page: BeautifulSoup object.
        :return: bool.
        """
        pass

    @abstractmethod
    def _has_artist(self, page):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Check if the artist is in the lyrics provider's database.

        :param page: BeautifulSoup object.
        :return: bool.
        """
        pass

    @abstractmethod
    def _make_artist_url(self, artist):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Builds an url for the artist page of the lyrics provider.

        :param artist: string.
        :return: string or None.
        """
        pass

    @abstractmethod
    def _make_search_artist_url(self, artist):
        """

        :param artist:
        :return:
        """
        raise NotImplementedError()

    @abstractmethod
    def _clean_string(self, text):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Formats the text to conform to the lyrics provider formatting.

        :param text:
        :return: string or None.
        """
        pass

    @abstractmethod
    def get_albums(self, raw_artist_page):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Fetches the albums section in the supplied html page.

        :param raw_artist_page: Artist's raw html page.
        :return: list.
            List of BeautifulSoup objects.
        """
        pass

    @abstractmethod
    def get_album_infos(self, tag):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Extracts the Album informations from the tag

        :param tag: BeautifulSoup object.
        :return: tuple(string, string).
            Album title and release date.
        """
        pass

    @abstractmethod
    def get_songs(self, album):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Fetches the links to the songs of the supplied album.

        :param album: BeautifulSoup object.
        :return: List of BeautifulSoup Link objects.
        """
        pass

    @abstractmethod
    def create_song(self, link, artist, album_title):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Creates a Song object.

        :param link: BeautifulSoup Link object.
        :param artist: string.
        :param album_title: string.
        :return: models.Song object or None.
        """
        pass

    @abstractmethod
    def extract_lyrics(self, lyrics_page):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Extracts the lyrics from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string or None.
            Formatted lyrics.
        """
        pass

    @abstractmethod
    def extract_writers(self, lyrics_page):
        """
        Must be implemented by children classes conforming to the LyricsMaster API.

        Extracts the writers from the lyrics page of the supplied song.

        :param lyrics_page: BeautifulSoup Object.
            BeautifulSoup lyrics page.
        :return: string or None.
            Song writers.
        """
        pass

    @abstractmethod
    def _extract_artists_from_search(self, search_results_page):
        """

        :param search_results_page:
        :return:
        """
        raise NotImplementedError()

    def get_page(self, url):
        """
        Fetches the supplied url and returns a request object.

        :param url: string.
        :return: urllib3.response.HTTPResponse Object or None.
        """
        if not self.__socket_is_patched():
            gevent.monkey.patch_socket()
        try:
            split_url = list(urlsplit(url))
            split_url[2:] = [quote(elmt, safe='/=+&%') for elmt in
                             split_url[2:]]
            url = urlunsplit(split_url)
            req = self.session.request('GET', url, retries=30)
        except Exception as e:
            logger.exception(e)
            req = None
            logger.warning('Unable to download url ' + url)
        return req

    def get_artist_page(self, artist):
        """
        Fetches the web page for the supplied artist.

        :param artist: string.
            Artist name.
        :return: string or None.
            Artist's raw html page. None if the artist page was not found.
        """
        artist = self._clean_string(artist)
        url = self._make_artist_url(artist)
        if not url:
            return None
        raw_html = self.get_page(url).data
        artist_page = BeautifulSoup(raw_html.decode('utf-8', 'ignore'), 'lxml')
        if not self._has_artist(artist_page):
            return None
        return raw_html

    def get_lyrics_page(self, url):
        """
        Fetches the web page containing the lyrics at the supplied url.

        :param url: string.
            Lyrics url.
        :return: string or None.
            Lyrics's raw html page. None if the lyrics page was not found.
        """
        try:
            raw_html = self.get_page(url).data
        except AttributeError:
            return None
        lyrics_page = BeautifulSoup(raw_html.decode('utf-8', 'ignore'), 'lxml')
        if not self._has_lyrics(lyrics_page):
            return None
        return raw_html

    def get_lyrics(self, artist, album=None, song=None, pool_size=None):
        """
        This is the main method of this class.
        Connects to the Lyrics Provider and downloads lyrics for all the albums of
        the supplied artist and songs.
        Returns a Discography Object or None if the artist was not found on the
        Lyrics Provider.

        :param artist: string.
            Artist name.
        :param album: string.
            Album title.
        :param song: string.
            Song title.
        :param pool_size: int.
            Pool size.
        :return: models.Discography object or None.
        """
        raw_html = self.get_artist_page(artist)
        if not raw_html:
            logger.warning(
                '{0} was not found on {1}'.format(artist, self.name))
            return None
        albums = self.get_albums(raw_html)
        if album:
            # If user supplied a specific album
            albums = [elmt for elmt in albums if
                      album.lower() in self.get_album_infos(elmt)[0].lower()]
        album_objects = []
        for elmt in albums:
            try:
                album_title, release_date = self.get_album_infos(elmt)
            except ValueError as e:
                logger.warning(
                    'Error {0} while downloading {1}'.format(e, elmt))
                continue
            song_links = self.get_songs(elmt)
            song_links = [link for link in song_links if link]
            if song:
                # If user supplied a specific song
                song_links = [link for link in song_links if
                              song.lower() in link.text.lower()]
            if self.tor_controller and self.tor_controller.controlport:
                # Renew Tor circuit before starting downloads.
                self.tor_controller.renew_tor_circuit()
                self.session = self.tor_controller.get_tor_session()
            if song_links:
                logger.info('Downloading {0}'.format(album_title))
                # Sets the worker pool for async requests.
                # 25 is a nice value to not annoy site owners ;)
                pool_size = 25 if pool_size is None else pool_size
                logger.debug("pool_size: %d", pool_size)
                pool = Pool(size=pool_size)
                results = [
                    pool.spawn(self.create_song, *(link, artist, album_title))
                    for link in song_links
                ]
                pool.join()  # Gathers results from the pool
                songs = [song.value for song in results if song.value]
                if songs:
                    album_obj = Album(album_title, artist, songs, release_date)
                    album_objects.append(album_obj)
                    logger.info(
                        '{0} successfully downloaded'.format(album_title))
                else:
                    logger.info(
                        'Skipped downloading {0} as no lyrics matched.'.format(
                            album_title))
        discography = Discography(artist, album_objects)
        return discography

    @staticmethod
    def _compute_score(_found_artists: Dict, _artist: str) -> int:
        """

        :param _found_artists:
        :param _artist:
        :return:
        """
        return fuzz.token_set_ratio(_found_artists['name'],
                                    _artist.replace('_', ' '))

    def search(self, artist) -> Dict:
        """
        Searches for the artist in the supplier's database.

        :param artist: Artist's name.
        :return: url or None.
            Url to the artist's page if found. None if not Found.
        """
        url = self._make_search_artist_url(artist)
        markup = self.get_page(url).data.decode('utf-8', 'ignore')
        search_results_page = BeautifulSoup(markup, 'lxml')

        sorted_founded_artists = sorted(
            self._extract_artists_from_search(search_results_page),
            key=lambda found_artist: self._compute_score(found_artist, artist),
            reverse=True,
        )
        # TODO: Improve this definition of 'best_match'
        best_match = sorted_founded_artists[0]
        return best_match
