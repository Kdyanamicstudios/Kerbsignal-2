import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from engineer.map_atlas import MAX_MAP_BYTES, MapAtlas, normalize_track_name, validate_map
from engineer.track_coverage import CATALOG, TrackCoverage, audit_coverage, catalog_entries


def geometry():
    return {'source': 'test survey', 'points': [[i / 10, 50 + i * .001, 6 + i * .001] for i in range(11)]}


class AtlasValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.atlas = MapAtlas(self.folder)
        (self.folder / 'index.json').write_text(json.dumps({'spa_2024_up': 'layout.json.gz'}), encoding='utf-8')
        self.write(geometry())

    def write(self, payload):
        with gzip.open(self.folder / 'layout.json.gz', 'wt', encoding='utf-8') as stream:
            json.dump(payload, stream)

    def test_exact_path_separator_and_case_equivalence(self):
        self.assertEqual(normalize_track_name(' SPA\\2024\\UP '), 'spa_2024_up')
        self.assertIsNotNone(self.atlas.load({'track_name': 'SPA/2024/UP'}))
        self.assertIsNone(self.atlas.load({'track_name': 'spa_up'}))
        self.assertIsNone(self.atlas.load({'track': 'Spa', 'config': 'Grand Prix'}))

    def test_corrupt_and_wrong_schema_maps_are_unavailable(self):
        for payload in ([], {}, {'source': 'x', 'points': []}, {'points': geometry()['points']}):
            with self.subTest(payload=payload):
                self.write(payload)
                self.assertIsNone(self.atlas.load({'track_name': 'spa_2024_up'}))
        (self.folder / 'layout.json.gz').write_bytes(b'not gzip')
        self.assertIsNone(self.atlas.load({'track_name': 'spa_2024_up'}))

    def test_invalid_point_values_and_fraction_order_rejected(self):
        for point in ([.5, float('nan'), 6], [.5, 91, 6], [.5, 50, 181], [.5, True, 6], [.5, 50], [.5, '50', 6], [.5, 10 ** 1000, 6]):
            with self.subTest(point=point):
                payload = geometry()
                payload['points'][5] = point
                self.assertIsNotNone(validate_map(payload))
        payload = geometry()
        payload['points'][5][0] = .4
        self.assertIn('increasing', validate_map(payload))
        payload = geometry()
        payload['points'] = payload['points'][2:8]
        self.assertIn('complete lap', validate_map(payload))

    def test_flat_geometry_and_oversized_payload_rejected(self):
        payload = geometry()
        payload['points'] = [[p, 50, 6] for p, lat, lon in payload['points']]
        self.assertIn('extent', validate_map(payload))
        payload = geometry()
        payload['padding'] = 'a' * MAX_MAP_BYTES
        self.write(payload)
        self.assertIn('size limit', self.atlas.inspect({'track_name': 'spa_2024_up'})[1])

    def test_unsafe_index_and_nonobject_metadata_do_not_load(self):
        for filename in ('../outside.json.gz', '..\\outside.json.gz', '/outside.json.gz', 'C:\\outside.json.gz', [], 1):
            with self.subTest(filename=filename):
                (self.folder / 'index.json').write_text(json.dumps({'spa_2024_up': filename}), encoding='utf-8')
                self.assertIsNone(self.atlas.load({'track_name': 'spa_2024_up'}))
        (self.folder / 'index.json').write_text('[]', encoding='utf-8')
        self.assertEqual(self.atlas.index(), {})
        for meta in (None, [], 'Spa'):
            self.assertIsNone(self.atlas.load(meta))
        for name in ('../outside', '..\\outside', '../../outside', '', None):
            self.assertIsNone(normalize_track_name(name))


class CoverageTests(unittest.TestCase):
    def test_containers_deduplicated_shared_layout_path_and_ambiguity_separate(self):
        catalog = {'rows': [
            {'name': 'Venue', 'path': '\\venue', 'source_line': 1},
            {'name': 'Venue - GP', 'path': '\\venue\\gp', 'source_line': 2},
            {'name': 'Oval', 'path': '\\oval', 'source_line': 3},
            {'name': 'Oval - Dual pits', 'path': '\\oval', 'source_line': 4},
            {'name': 'Oval - Single pit', 'path': '\\oval\\single', 'source_line': 5},
            {'name': 'Ambiguous', 'path': '\\ambiguous', 'source_line': 6},
            {'name': 'Ambiguous', 'path': '\\ambiguous', 'source_line': 7},
            {'name': 'Ambiguous - School', 'path': '\\ambiguous\\school', 'source_line': 8},
        ]}
        entries = {entry['key']: entry for entry in catalog_entries(catalog)}
        self.assertEqual(len(entries), 6)
        self.assertEqual(entries['venue']['kind'], 'container')
        self.assertEqual(entries['oval']['kind'], 'layout')
        self.assertEqual(entries['oval']['source_lines'], [3, 4])
        self.assertEqual(entries['ambiguous']['kind'], 'needs_review')

    def test_selected_map_does_not_imply_coaching_or_alias_new_scan(self):
        coverage = TrackCoverage()
        spa = coverage.status_for({'track_name': 'spa_2024_up'})
        self.assertEqual(spa['map_status'], 'available')
        self.assertEqual(spa['map_point_count'], 1000)
        self.assertEqual(spa['reference_status'], 'requires matching runtime reference or guide')
        zolder = coverage.status_for({'track_name': 'zolder_2024_gp'})
        self.assertEqual(zolder['map_status'], 'unavailable')
        self.assertTrue(zolder['official_match'])
        spelling = coverage.status_for({'track_name': 'tsukuba_1kreverse'})
        self.assertEqual(spelling['map_status'], 'unavailable')
        self.assertEqual(coverage.status_for({'track': 'Spa'})['track_key'], None)

    def test_catalog_integrity_and_all_bundled_geometry(self):
        catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
        self.assertEqual(len(catalog['rows']), 536)
        self.assertEqual([row['source_line'] for row in catalog['rows']], list(range(19, 555)))
        self.assertEqual(catalog['source_modified'], '2025-12-09')
        report = audit_coverage()
        summary = report['summary']
        self.assertEqual(summary['distinct_paths'], 523)
        self.assertEqual(summary['bundled_valid_maps'], 417)
        self.assertEqual(summary['bundled_invalid_maps'], 0)
        self.assertEqual(summary['layout_paths'], summary['exact_layout_valid_maps'] + summary['layout_identity_reviews'] + summary['layout_missing_exact_maps'] + summary['layouts_with_invalid_maps'])
        rows = {row['key']: row for row in report['official_paths']}
        self.assertEqual(rows['spa']['map_status'], 'container_not_layout')
        self.assertEqual(rows['tsukuba_1kreverse']['map_status'], 'identity_review_no_exact_map')
        self.assertEqual(rows['charlotte_2025_roval2025']['map_status'], 'missing_exact_map')
        self.assertEqual(rows['lagunaseca']['map_status'], 'layout_classification_review')

    def test_missing_catalog_is_exposed_and_selected_map_still_checks_file(self):
        with tempfile.TemporaryDirectory() as temp:
            coverage = TrackCoverage(catalog_path=Path(temp) / 'missing.json')
            self.assertFalse(coverage.summary()['catalog_available'])
            self.assertEqual(coverage.status_for({'track_name': 'spa_2024_up'})['map_status'], 'available')

    def test_summary_and_search_list_never_decompress_maps(self):
        coverage = TrackCoverage()
        with patch.object(coverage.atlas, 'inspect', side_effect=AssertionError('Unexpected gzip scan')):
            summary = coverage.summary()
            rows = coverage.layouts()
        self.assertEqual(summary['bundled_index_entries'], 417)
        self.assertEqual(len(rows), 523)
        spa = next(row for row in rows if row['key'] == 'spa_2024_up')
        self.assertTrue(spa['exact_index_match'])
        spa['source_names'].append('mutated UI copy')
        spa['kind'] = 'changed'
        fresh = next(row for row in coverage.layouts() if row['key'] == 'spa_2024_up')
        self.assertNotIn('mutated UI copy', fresh['source_names'])
        self.assertEqual(fresh['kind'], 'layout')

    def test_corrupt_catalog_rows_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'catalog.json'
            for data in ([], {'rows': None}, {'rows': [None]}, {'rows': [{'path': 1, 'name': 'x', 'source_line': 1}]}):
                with self.subTest(data=data):
                    path.write_text(json.dumps(data), encoding='utf-8')
                    self.assertFalse(TrackCoverage(catalog_path=path).summary()['catalog_available'])


if __name__ == '__main__':
    unittest.main()
