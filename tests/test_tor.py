import pytest
from click.testing import CliRunner

from lyricsmaster import TorController, LyricWiki, models, cli
from tests.conftest import python_is_outdated, is_appveyor, is_travis


# If tests involving Tor are run first, the following tests fail with error: 'an integer is required (got type object)'
class TestTor:
    """Tests for Tor functionality."""
    tor_basic = TorController()
    if is_travis or (is_appveyor and python_is_outdated):
        tor_advanced = TorController(controlport='/var/run/tor/control',
                                     password='password')
    else:
        tor_advanced = TorController(controlport=9051, password='password')

    non_anon_provider = LyricWiki()
    provider = LyricWiki(tor_basic)
    provider2 = LyricWiki(tor_advanced)

    @pytest.mark.skipif(is_appveyor,
                        reason="Tor error on ApppVeyor.")
    def test_anonymisation(self):
        real_ip = self.non_anon_provider.get_page("http://httpbin.org/ip").data
        anonymous_ip = self.provider.get_page("http://httpbin.org/ip").data
        assert real_ip != anonymous_ip

    # this function is tested out in travis using a unix path as a control port instead of port 9051.
    # for now gets permission denied on '/var/run/tor/control' in Travis CI
    @pytest.mark.skipif(is_travis or is_appveyor,
                        reason="Tor error on CI.")
    def test_renew_tor_session(self):
        real_ip = self.non_anon_provider.get_page("http://httpbin.org/ip").data
        anonymous_ip = self.provider2.get_page("http://httpbin.org/ip").data
        assert real_ip != anonymous_ip
        new_tor_circuit = self.provider2.tor_controller.renew_tor_circuit()
        real_ip2 = self.non_anon_provider.get_page("http://httpbin.org/ip").data
        anonymous_ip2 = self.provider2.get_page("http://httpbin.org/ip").data
        assert real_ip2 != anonymous_ip2
        assert new_tor_circuit is True

    @pytest.mark.skipif(is_appveyor,
                        reason="Tor error on ApppVeyor.")
    def test_get_lyrics_tor_basic(self):
        discography = self.provider.get_lyrics(
            'Reggie Watts', 'Why $#!+ So Crazy?',
            'Fuck Shit Stack')  # put another realsinger who has not so many songs to speed up testing.
        assert isinstance(discography, models.Discography)

    @pytest.mark.skipif(is_appveyor or is_travis,
                        reason="Tor error on CI.")
    def test_get_lyrics_tor_advanced(self):
        discography = self.provider2.get_lyrics(
            'Reggie Watts', 'Why $#!+ So Crazy?', 'Fuck Shit Stack')
        assert isinstance(discography, models.Discography)

    @pytest.mark.skipif(is_appveyor,
                        reason="Tor error on ApppVeyor.")
    def test_command_line_interface_tor(self):
        artist = 'Reggie Watts'
        runner = CliRunner()
        result_tor1 = runner.invoke(cli.main,
                                    [artist, '-a', 'Why $#!+ So Crazy?', '-s',
                                     'Fuck Shit Stack', '--tor', '127.0.0.1',
                                     '--controlport', '9051', '--password',
                                     'password'])
        assert result_tor1.exit_code == 0

    @pytest.mark.skipif(is_appveyor,
                        reason="Tor error on ApppVeyor.")
    def test_command_line_interface_tor(self):
        artist = 'Reggie Watts'
        runner = CliRunner()
        result_tor = runner.invoke(cli.main, [artist, '-a', 'Why $#!+ So Crazy?', '-s',
                                              'Fuck Shit Stack', '--tor', '127.0.0.1'])
        assert result_tor.exit_code == 0
