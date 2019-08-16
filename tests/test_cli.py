from click.testing import CliRunner

from lyricsmaster import cli


class TestCli:
    """Tests for Command Line Interface."""

    def test_command_line_interface(self):
        artist = 'Reggie Watts'
        runner = CliRunner()
        result = runner.invoke(cli.main, [artist, '-a', 'Why $#!+ So Crazy?', '-s', 'Fuck Shit Stack'])
        assert result.exit_code == 0
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert 'Show this message and exit.' in help_result.output
