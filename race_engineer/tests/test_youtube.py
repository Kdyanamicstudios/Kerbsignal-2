import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit

from engineer.youtube import DEFAULT_URL, YouTubeMusic, playback_url, validate_url
from engineer.voice import COMMANDS


class YouTubeTests(unittest.TestCase):
    def test_commands_route_to_browser_music(self):
        self.assertEqual(COMMANDS['engineer play focus music'],'focus_music')
        self.assertEqual(COMMANDS['engineer open youtube'],'focus_music')

    def test_default_search_and_custom_playlist_persist(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'youtube.json';opened=[]
            music=YouTubeMusic(path,opener=lambda url,**kwargs:opened.append((url,kwargs)) or True)
            music.open()
            self.assertEqual(opened[0][0],DEFAULT_URL)
            url='https://www.youtube.com/playlist?list=example_playlist'
            music.save(url)
            self.assertEqual(YouTubeMusic(path).url,url)
            music.open()
            self.assertEqual(parse_qs(urlsplit(opened[-1][0]).query)['autoplay'],['1'])
            self.assertEqual(opened[-1][1],{'new':2})

    def test_existing_autoplay_and_timestamp_are_handled(self):
        url=playback_url('https://www.youtube.com/watch?v=example&t=30&autoplay=0')
        query=parse_qs(urlsplit(url).query)
        self.assertEqual(query['autoplay'],['1']);self.assertEqual(query['t'],['30'])
        self.assertIn('autoplay=1',playback_url('https://youtu.be/example'))

    def test_non_youtube_and_executable_links_rejected(self):
        for url in ('file:///C:/Windows/cmd.exe','javascript:alert(1)','https://youtube.com.evil.example/watch?v=x','https://youtube.com@evil.example/','https://user@youtube.com/watch?v=x','https://youtube.com:999/watch?v=x','https://youtube.com/\nwatch?v=x','http://youtube.com/watch?v=x'):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):validate_url(url)

    def test_bad_settings_fallback_and_browser_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'youtube.json';path.write_text('{bad json')
            music=YouTubeMusic(path,opener=lambda *a,**kw:False)
            self.assertEqual(music.url,DEFAULT_URL);self.assertIsNotNone(music.load_error)
            with self.assertRaises(OSError):music.open()
