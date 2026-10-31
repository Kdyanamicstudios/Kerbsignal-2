"""Load validated map geometry by exact internal SDK TrackName only.

Separators and case are equivalent SDK path spellings. Venue/display names,
different scan years and different layout names are never aliases.
"""
from collections.abc import Mapping
import gzip
import json
import math
from pathlib import Path
import re
import zlib


MAX_INDEX_BYTES = 1_000_000
MAX_MAP_BYTES = 2_000_000
MAX_POINTS = 10_000


def _finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def normalize_track_name(value):
    """Return an exact SDK key, or None for an unsafe/absent identity."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if any(part in ('.', '..') for part in re.split(r'[\\/]', value)):
        return None
    key = value.replace(' ', '_').replace('\\', '_').replace('/', '_').lower()
    if not key or not re.fullmatch(r'[a-z0-9][a-z0-9_.-]*', key):
        return None
    return key


def validate_map(payload):
    """Validate the schema consumed by PositionTracker; return an error or None."""
    if not isinstance(payload, dict):
        return 'map is not an object'
    if not isinstance(payload.get('source'), str) or not payload['source'].strip():
        return 'map source is missing'
    points = payload.get('points')
    if not isinstance(points, list) or not 6 <= len(points) <= MAX_POINTS:
        return 'map needs 6–10,000 points'
    previous = -1.0
    for point in points:
        if not isinstance(point, (list, tuple)) or len(point) != 3:
            return 'map point must contain lap fraction, latitude and longitude'
        if any(not _finite_number(v) for v in point):
            return 'map coordinates must be finite numbers'
        fraction, lat, lon = point
        if not 0 <= fraction <= 1 or not -90 <= lat <= 90 or not -180 <= lon <= 180:
            return 'map coordinate is out of range'
        if fraction <= previous:
            return 'map lap fractions must be strictly increasing'
        previous = fraction
    if points[0][0] > .05 or points[-1][0] < .95:
        return 'map does not span a complete lap'
    if max(p[1] for p in points) - min(p[1] for p in points) <= 1e-4 and max(p[2] for p in points) - min(p[2] for p in points) <= 1e-4:
        return 'map has no usable geographic extent'
    return None


class MapAtlas:
    def __init__(self, folder=None):
        self.folder = Path(folder) if folder else Path(__file__).with_name('maps')

    def index(self):
        """Read the small index safely; invalid indexes yield no matches."""
        try:
            with (self.folder / 'index.json').open('rb') as stream:
                raw = stream.read(MAX_INDEX_BYTES + 1)
            if len(raw) > MAX_INDEX_BYTES:
                return {}
            result = json.loads(raw.decode('utf-8'))
            return result if isinstance(result, dict) else {}
        except (OSError, ValueError, TypeError, RecursionError):
            return {}

    def inspect(self, meta):
        """Return (map, reason) so audit/UI can distinguish absent/broken data."""
        name = normalize_track_name(meta.get('track_name')) if isinstance(meta, Mapping) else None
        if not name:
            return None, 'exact SDK track name unavailable'
        filename = self.index().get(name)
        if filename is None:
            return None, 'no exact bundled map'
        if not isinstance(filename, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]*\.json\.gz', filename):
            return None, 'unsafe map index filename'
        try:
            root = self.folder.resolve()
            path = (root / filename).resolve()
            if path.parent != root:
                return None, 'map file is outside atlas'
            with gzip.open(path, 'rb') as stream:
                raw = stream.read(MAX_MAP_BYTES + 1)
            if len(raw) > MAX_MAP_BYTES:
                return None, 'map exceeds size limit'
            payload = json.loads(raw.decode('utf-8'))
            error = validate_map(payload)
            return (None, error) if error else (payload, None)
        except (OSError, ValueError, TypeError, EOFError, zlib.error, RecursionError):
            return None, 'map file is unreadable'

    def load(self, meta):
        return self.inspect(meta)[0]
