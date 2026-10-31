"""Reproduce the offline map/path audit; no network or simulator required.

Run from the repository root with Python 3.10+:
    python windows_build/audit_track_coverage.py
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'race_engineer'))
from engineer.track_coverage import AUDIT_SUMMARY, CATALOG, MAP_SOURCE_URL, audit_coverage


TARGETS = (
    ('Road Atlanta', 'roadatlanta'), ('Le Mans', 'lemans'),
    ('Daytona, including road layouts', 'daytona'), ('Spa', 'spa'),
    ('Monza', 'monza'), ('COTA', 'cota'), ('Nürburgring', 'nurburgring'),
    ('Tsukuba', 'tsukuba'), ('Oulton Park', 'oulton'),
)


def markdown(report):
    summary = report['summary']
    rows = report['official_paths']
    lines = [
        '# Track and layout coverage audit', '',
        'Audit retrieved October 31, 2026. Source validation only; live iRacing position and driver acceptance are not established by this report.', '',
        f"Official path source: [{summary['source_modified']} article snapshot]({summary['source_url']}). The article is older than this audit and does not establish exhaustive current service coverage.", '',
        f"The snapshot contains **{summary['source_rows']} rows / {summary['distinct_paths']} distinct paths**. After grouping repeated paths, **{summary['layout_paths']} paths are classified as layouts**, **{summary['container_paths']} as venue/container directories**, and **{summary['ambiguous_paths']} remain ambiguous**. These classifications describe the article, not a verified service inventory.", '',
        f"All **{summary['bundled_valid_maps']} of {summary['bundled_index_entries']} indexed gzip maps** pass schema, finite-coordinate/range, complete lap-fraction span, strictly increasing fraction and geographic-extent checks. Each currently contains 1,000 points. These checks detect broken data; they cannot prove the source survey follows the current track scan.", '',
        f"Among definite layout paths: **{summary['exact_layout_valid_maps']} exact valid maps**, **{summary['layout_identity_reviews']} identity/path spelling reviews**, **{summary['layout_missing_exact_maps']} other missing exact maps**, **{summary['layouts_with_invalid_maps']} invalid exact maps**. No suspected identity match is enabled as an alias.", '',
        '## Named checklist venues (TEL-03)', '',
        '| Venue | Definite layout paths in snapshot | Exact valid map | Identity review | Other missing |',
        '|---|---:|---:|---:|---:|',
    ]
    for label, prefix in TARGETS:
        selected = [row for row in rows if row['kind'] == 'layout' and (row['key'] == prefix or row['key'].startswith(prefix + '_'))]
        lines.append(f"| {label} | {len(selected)} | {sum(row['map_status'] == 'exact_map_valid' for row in selected)} | {sum(row['map_status'] == 'identity_review_no_exact_map' for row in selected)} | {sum(row['map_status'] == 'missing_exact_map' for row in selected)} |")
    lines += [
        '', 'Daytona counts include ovals, road, moto, short and rallycross entries. Current/legacy road entries are matched separately. Map availability does not establish aligned coaching or reference availability for any of these layouts.', '',
        '## Definite layouts without an exact validated map', '',
        '| Official layout | Official path key | Status | Unverified source-key leads |',
        '|---|---|---|---|',
    ]
    for row in rows:
        if row['kind'] == 'layout' and row['map_status'] != 'exact_map_valid':
            leads = ', '.join(row['identity_review_candidates']) or '—'
            lines.append(f"| {row['official_name']} | `{row['key']}` | {row['map_status']} | {leads} |")
    lines += [
        '', 'Newer scan keys (including Charlotte 2025, Zolder 2024 and Sonoma 2025) remain separate from legacy bundled maps. Missing geometry is not filled using a different scan or a similar name. The recorded GPS-route fallback requires valid telemetry and a driven route; it is not preloaded coverage.', '',
        '## Ambiguous article paths', '',
    ]
    for row in rows:
        if row['kind'] == 'needs_review':
            lines.append(f"- `{row['key']}` — {row['official_name']}; repeated identical root name plus child layout. Excluded from the definite-layout denominator; direct SDK lookup can still load its exact bundled map.")
    lines += [
        '', '## Bundled keys not present as exact paths in the snapshot', '',
        ', '.join('`' + key + '`' for key in summary['bundled_keys_not_in_official_paths']), '',
        'These may include article omissions, older layouts or different source names. They remain visible and are never silently reassigned to current layouts. For example, the article lists Mugello Short but omits the bundled Mugello GP key.', '',
        '## Geometry, coaching and live acceptance', '',
        f'Bundled geometry derives from [SIMRacingAppsServer track data]({MAP_SOURCE_URL}); Copyright © 2015–2024 Jeffrey Gilliam, Apache License 2.0. Original source data and notices are preserved in the source handoff.', '',
        '- “Surveyed lap fraction” and “GPX distance estimate” describe source positioning. GPX fractions can differ from SDK lap fractions. Prefer live SDK GPS; projection by lap distance is explicitly an estimated XY position.',
        '- A map is not a fastest line, expert braking guide, verified turn-name catalogue or car-specific reference. A compatible clean lap/imported guide must pass the runtime car, exact layout, length, conditions and provenance gates.',
        '- Live detection, map alignment, start/finish orientation, GPS projection error, position freshness and coaching timing still require Windows/iRacing tests for each supported identity.', '',
        '## Reproduction and files', '',
        'Run `python windows_build/audit_track_coverage.py` from the repository root (or use the packaged Python). This performs no network requests. Results are deterministic for the same catalog/maps.', '',
        '- `race_engineer/engineer/catalog/iracing_tracks_2025-12-09.json`: all 536 factual name/path rows, source URL, source line numbers and source/retrieval dates. No HTML or support-page boilerplate.',
        '- `race_engineer/engineer/catalog/map_coverage_summary.json`: compact audited metadata for the in-app Help panel.',
        '- `docs/TRACK_COVERAGE.json`: every official unique path, classification, exact map status, identity-review leads, and every bundled map validation result.',
        '- `docs/TRACK_COVERAGE.csv`: the same per-path statuses for filtering.', '',
        'To refresh the snapshot, consult the official article, preserve its factual rows and modification/retrieval dates, review container classification and path spelling differences, then rerun the audit. Independently verify service additions missing from that article; do not rename or reuse an old map merely to increase the count.', '',
    ]
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify checked-in outputs match; do not write files.')
    args = parser.parse_args()
    report = audit_coverage()
    report['summary']['catalog_sha256'] = hashlib.sha256(CATALOG.read_bytes()).hexdigest()
    report['summary']['map_source_url'] = MAP_SOURCE_URL
    fields = ('key', 'official_name', 'official_path', 'kind', 'map_status', 'map_file', 'map_source', 'map_points', 'identity_review_candidates', 'source_lines', 'reference_status')
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    for row in report['official_paths']:
        flat = {key: row[key] for key in fields}
        flat['identity_review_candidates'] = ';'.join(flat['identity_review_candidates'])
        flat['source_lines'] = ';'.join(map(str, flat['source_lines']))
        writer.writerow(flat)
    summary = dict(report['summary'])
    summary.pop('caveats', None)
    summary.pop('bundled_keys_not_in_official_paths', None)
    outputs = {
        ROOT / 'docs/TRACK_COVERAGE.json': json.dumps(report, ensure_ascii=False, indent=2) + '\n',
        ROOT / 'docs/TRACK_COVERAGE.csv': stream.getvalue(),
        ROOT / 'docs/TRACK_COVERAGE.md': markdown(report),
        AUDIT_SUMMARY: json.dumps(summary, ensure_ascii=False, indent=2) + '\n',
    }
    mismatches = []
    for path, content in outputs.items():
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8') != content:
                mismatches.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8', newline='\n')
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True))
    if mismatches:
        print('Stale audit outputs: ' + ', '.join(mismatches), file=sys.stderr)
        return 1
    if report['summary']['bundled_invalid_maps'] or not report['summary']['catalog_available']:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
