"""Offline, exact-path map coverage; geometry is not a coaching reference.

The official filepath article mixes venue directories, layout rows, duplicate
rows and naming inconsistencies. Keep those separate rather than declaring
every directory a missing playable layout or silently adding guessed aliases.
"""
from collections import defaultdict
from collections.abc import Mapping
from copy import deepcopy
import json
from pathlib import Path

from .map_atlas import MapAtlas, normalize_track_name


CATALOG = Path(__file__).with_name('catalog') / 'iracing_tracks_2025-12-09.json'
AUDIT_SUMMARY = CATALOG.with_name('map_coverage_summary.json')
MAP_SOURCE_URL = 'https://github.com/SIMRacingApps/SIMRacingAppsServer'
CAVEATS = (
    'Official filepath snapshot modified December 9, 2025; retrieved October 31, 2026. It is not a verified exhaustive current service catalogue.',
    'Directory/container rows and duplicate paths are excluded from the definite layout count. Uncertain root paths remain visible for review.',
    'Exact SDK TrackName only. Different scan years, similar display names and suspected path spelling differences are not aliases.',
    'Maps provide geometry, not expert guides, verified turn names or fastest racing lines. GPX lap fractions are estimates; live SDK GPS is preferred.',
    'Coaching needs a valid reference or authored guide matching car, exact layout and conditions. Its availability must be checked against the current session.',
)

# Review leads only: never used by MapAtlas/status_for to select geometry.
# Verify actual source geometry and live SDK identity before adding any alias.
IDENTITY_REVIEW = {
    'california_interior': ('california_interiora',),
    'crandon': ('crandon_full',),
    'hockenheim_peceast': ('hockenheim_pec_peceast',),
    'hockenheim_pechandling': ('hockenheim_pec_pechandling',),
    'hockenheim_pecouter': ('hockenheim_pec_pecouter',),
    'hockenheim_pecwest': ('hockenheim_pec_pecwest',),
    'magnycours_grandprix': ('magnycours_gp',),
    'michigan2014': ('michigan', 'michigan_2015'),
    'michigan2018': ('michigan_2018',),
    'oswego_dirtoval': ('oswego_dirt',),
    'tsukuba_1kreverse': ('tsukuba_1kfullreverse',),
    'wildwest': ('wildwest_full',),
    'willow': ('willow_international',),
    'zandvoort_2023_ostelijk': ('zandvoort_2023_oostelijk',),
}


def filepath_key(path):
    """Official installation paths omit the SDK underscore serialization."""
    return normalize_track_name(path.strip('\\/')) if isinstance(path, str) else None


def catalog_entries(catalog):
    """Group duplicate paths and identify explicit layouts vs containers.

    A path containing children is a container unless a distinct row at that
    same path explicitly names a layout. Laguna Seca's identical repeated name
    at the root plus School child is ambiguous in the article: keep it out of
    both definite-layout and container denominators. This is a transparent
    article classification, not verification of an exhaustive layout catalogue.
    """
    if not isinstance(catalog, dict) or not isinstance(catalog.get('rows'), list):
        raise ValueError('Track catalog needs an object with rows')
    groups = defaultdict(list)
    for row in catalog['rows']:
        if not isinstance(row, dict) or not isinstance(row.get('name'), str) or not isinstance(row.get('path'), str) or not isinstance(row.get('source_line'), int):
            raise ValueError('Invalid track catalog row')
        if filepath_key(row['path']) is None:
            raise ValueError('Invalid official filepath')
        path = row['path'].strip('\\/').lower().replace('\\', '/')
        groups[path].append(row)
    result = []
    for path, rows in groups.items():
        descendants = any(other.startswith(path + '/') for other in groups)
        names = list(dict.fromkeys(row['name'] for row in rows))
        kind = 'container' if descendants else 'layout'
        if descendants and len(names) > 1:
            kind = 'layout'
        elif descendants and len(rows) > 1:
            kind = 'needs_review'
        result.append({
            'key': filepath_key(path), 'official_path': rows[0]['path'],
            'official_name': max(names, key=len), 'source_names': names,
            'source_lines': [row['source_line'] for row in rows], 'kind': kind,
        })
    return sorted(result, key=lambda entry: entry['key'])


class TrackCoverage:
    def __init__(self, atlas=None, catalog_path=None):
        self.atlas = atlas or MapAtlas()
        self.catalog_path = Path(catalog_path) if catalog_path else CATALOG
        self._catalog = None
        self._entries = None

    def _read(self):
        if self._catalog is None:
            try:
                self._catalog = json.loads(self.catalog_path.read_text(encoding='utf-8'))
                self._entries = {row['key']: row for row in catalog_entries(self._catalog)}
            except (OSError, ValueError, KeyError, TypeError):
                self._catalog = {}
                self._entries = {}
        return self._catalog, self._entries

    def summary(self):
        """Cheap UI summary. Deep geometry checks are in the offline audit CLI."""
        catalog, entries = self._read()
        index = self.atlas.index()
        layouts = [row for row in entries.values() if row['kind'] == 'layout']
        result = {
            'catalog_available': bool(entries),
            'source_url': catalog.get('source_url', ''),
            'source_modified': catalog.get('source_modified', ''),
            'retrieved': catalog.get('retrieved', ''),
            'source_rows': len(catalog.get('rows', [])),
            'distinct_paths': len(entries),
            'layout_paths': len(layouts),
            'container_paths': sum(row['kind'] == 'container' for row in entries.values()),
            'ambiguous_paths': sum(row['kind'] == 'needs_review' for row in entries.values()),
            'bundled_index_entries': len(index),
            'exact_layout_index_matches': sum(row['key'] in index for row in layouts),
            'reference_status': 'requires matching runtime reference or guide',
            'caveats': list(CAVEATS),
        }
        # Saved audit is not this installation's health. Selected-layout
        # availability below always checks the actual selected gzip file.
        if self.catalog_path == CATALOG:
            try:
                audit = json.loads(AUDIT_SUMMARY.read_text(encoding='utf-8'))
                if isinstance(audit, dict):
                    result['saved_audit'] = audit
            except (OSError, ValueError, TypeError):
                pass
        return result

    def status_for(self, meta):
        """Selected exact SDK identity; never infer runtime coaching readiness."""
        _, entries = self._read()
        name = normalize_track_name(meta.get('track_name')) if isinstance(meta, Mapping) else None
        entry = entries.get(name)
        payload, error = self.atlas.inspect(meta)
        return {
            'track_key': name,
            'map_status': 'available' if payload else 'unavailable',
            'map_reason': error or 'validated exact bundled map',
            'map_source': payload['source'] if payload else '',
            'map_point_count': len(payload['points']) if payload else 0,
            'official_match': bool(entry),
            'official_name': entry['official_name'] if entry else '',
            'official_path_kind': entry['kind'] if entry else 'not in snapshot',
            'reference_status': 'requires matching runtime reference or guide',
            'fallback': '' if payload else 'observed GPS route after valid telemetry',
        }

    def layouts(self):
        """All catalog paths with kind + index availability; no gzip scan.

        The exact_index_match flag says only that an entry exists, not that
        its file is valid. Call status_for on selection to validate one map.
        Returning fresh nested values keeps UI filtering from mutating cache.
        """
        _, entries = self._read()
        index = self.atlas.index()
        rows = deepcopy(list(entries.values()))
        for row in rows:
            row['exact_index_match'] = row['key'] in index
            row['identity_review_candidates'] = list(IDENTITY_REVIEW.get(row['key'], ()))
        return rows


def audit_coverage(atlas=None, catalog_path=None):
    """Validate every indexed gzip and retain one result per official path."""
    coverage = TrackCoverage(atlas, catalog_path)
    catalog, entries = coverage._read()
    index = coverage.atlas.index()
    maps = {}
    for key in sorted(index):
        payload, error = coverage.atlas.inspect({'track_name': key})
        maps[key] = {
            'filename': index[key], 'valid': payload is not None,
            'error': error, 'points': len(payload['points']) if payload else 0,
            'source': payload['source'] if payload else '',
        }
    rows = []
    for entry in entries.values():
        row = dict(entry)
        mapped = maps.get(row['key'])
        candidates = [key for key in IDENTITY_REVIEW.get(row['key'], ()) if key in maps]
        if row['kind'] == 'container':
            status = 'container_not_layout'
        elif row['kind'] == 'needs_review':
            status = 'layout_classification_review'
        elif mapped:
            status = 'exact_map_valid' if mapped['valid'] else 'exact_map_invalid'
        elif candidates:
            status = 'identity_review_no_exact_map'
        else:
            status = 'missing_exact_map'
        row.update(map_status=status, map_file=mapped['filename'] if mapped else '',
                   map_source=mapped['source'] if mapped else '',
                   map_points=mapped['points'] if mapped else 0,
                   identity_review_candidates=candidates,
                   reference_status='requires matching runtime reference or guide')
        rows.append(row)
    summary = coverage.summary()
    summary.pop('saved_audit', None)
    summary.update(
        bundled_valid_maps=sum(row['valid'] for row in maps.values()),
        bundled_invalid_maps=sum(not row['valid'] for row in maps.values()),
        exact_layout_valid_maps=sum(row['map_status'] == 'exact_map_valid' for row in rows),
        layout_identity_reviews=sum(row['map_status'] == 'identity_review_no_exact_map' for row in rows),
        layout_missing_exact_maps=sum(row['map_status'] == 'missing_exact_map' for row in rows),
        layouts_with_invalid_maps=sum(row['map_status'] == 'exact_map_invalid' for row in rows),
        bundled_keys_not_in_official_paths=sorted(set(index) - set(entries)),
    )
    return {'schema': 'kerbsignal-track-coverage-v1', 'summary': summary,
            'official_paths': rows, 'bundled_maps': maps}
