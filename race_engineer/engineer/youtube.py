"""Open a user-selected YouTube destination in the default browser."""
import json
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import webbrowser

DEFAULT_URL = 'https://www.youtube.com/results?search_query=instrumental+focus+music'
ALLOWED_HOSTS = {'youtube.com','www.youtube.com','m.youtube.com','music.youtube.com','youtu.be','www.youtu.be'}


def validate_url(value):
    value=value.strip()
    if not value or len(value)>4096 or any(ord(c)<32 or ord(c)==127 for c in value):
        raise ValueError('Enter a YouTube video, playlist, or search link.')
    try:
        parts=urlsplit(value)
        port=parts.port
    except ValueError as exc:
        raise ValueError('Invalid YouTube link.') from exc
    if parts.scheme.lower()!='https' or parts.hostname not in ALLOWED_HOSTS or parts.username or parts.password or port not in (None,443) or '\\' in value:
        raise ValueError('Use an HTTPS link on youtube.com, music.youtube.com, or youtu.be.')
    return value


def playback_url(value):
    url=validate_url(value)
    p=urlsplit(url)
    # Request autoplay on videos/playlists; browsers/YouTube can still require a click.
    if p.path in ('/watch','/playlist') or p.hostname in ('youtu.be','www.youtu.be'):
        query=[(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if k.lower()!='autoplay']
        query.append(('autoplay','1'))
        return urlunsplit((p.scheme,p.netloc,p.path,urlencode(query),p.fragment))
    return url


class YouTubeMusic:
    def __init__(self, path, opener=None):
        self.path=Path(path)
        self.opener=opener or webbrowser.open
        self.url=DEFAULT_URL
        self.load_error=None
        if self.path.exists():
            try:
                self.url=validate_url(json.loads(self.path.read_text(encoding='utf-8'))['url'])
            except (OSError,ValueError,TypeError,KeyError):
                self.load_error='Saved YouTube link could not be loaded. Using the default focus-music search.'

    def save(self,value):
        url=validate_url(value)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temporary=self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps({'url':url}),encoding='utf-8')
        temporary.replace(self.path)
        self.url=url

    def open(self):
        result=self.opener(playback_url(self.url),new=2)
        if not result:
            raise OSError('Could not launch your default browser. Check its Windows default-app setting.')
        return self.url
