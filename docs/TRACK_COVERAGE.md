# Track and layout coverage audit

Audit retrieved October 31, 2026. Source validation only; live iRacing position and driver acceptance are not established by this report.

Official path source: [2025-12-09 article snapshot](https://support.iracing.com/support/solutions/articles/31000176962-filepath-for-active-iracing-tracks). The article is older than this audit and does not establish exhaustive current service coverage.

The snapshot contains **536 rows / 523 distinct paths**. After grouping repeated paths, **436 paths are classified as layouts**, **86 as venue/container directories**, and **1 remain ambiguous**. These classifications describe the article, not a verified service inventory.

All **417 of 417 indexed gzip maps** pass schema, finite-coordinate/range, complete lap-fraction span, strictly increasing fraction and geographic-extent checks. Each currently contains 1,000 points. These checks detect broken data; they cannot prove the source survey follows the current track scan.

Among definite layout paths: **371 exact valid maps**, **14 identity/path spelling reviews**, **51 other missing exact maps**, **0 invalid exact maps**. No suspected identity match is enabled as an alias.

## Named checklist venues (TEL-03)

| Venue | Definite layout paths in snapshot | Exact valid map | Identity review | Other missing |
|---|---:|---:|---:|---:|
| Road Atlanta | 3 | 3 | 0 | 0 |
| Le Mans | 2 | 2 | 0 | 0 |
| Daytona, including road layouts | 11 | 11 | 0 | 0 |
| Spa | 7 | 7 | 0 | 0 |
| Monza | 9 | 9 | 0 | 0 |
| COTA | 3 | 3 | 0 | 0 |
| Nürburgring | 12 | 12 | 0 | 0 |
| Tsukuba | 7 | 6 | 1 | 0 |
| Oulton Park | 8 | 8 | 0 | 0 |

Daytona counts include ovals, road, moto, short and rallycross entries. Current/legacy road entries are matched separately. Map availability does not establish aligned coaching or reference availability for any of these layouts.

## Definite layouts without an exact validated map

| Official layout | Official path key | Status | Unverified source-key leads |
|---|---|---|---|
| Adelaide Street Circuit | `adelaide` | missing_exact_map | — |
| Bark River International Raceway | `barkriver` | missing_exact_map | — |
| Auto Club Speedway - Interior | `california_interior` | identity_review_no_exact_map | california_interiora |
| Charlotte Motor Speedway - Legends Oval | `charlotte_2025_legendsoval` | missing_exact_map | — |
| Charlotte Motor Speedway - Legends RC Oval Medium | `charlotte_2025_legendsrc2025` | missing_exact_map | — |
| Charlotte Motor Speedway - Legends RC Oval Long | `charlotte_2025_legendsrclong` | missing_exact_map | — |
| Charlotte Motor Speedway - Legends RC Oval Short | `charlotte_2025_legendsrcshort` | missing_exact_map | — |
| Charlotte Motor Speedway - Oval - 2018 | `charlotte_2025_oval` | missing_exact_map | — |
| Charlotte Motor Speedway - Rallycross | `charlotte_2025_rallycrosslong` | missing_exact_map | — |
| Charlotte Motor Speedway - Roval - 2018 | `charlotte_2025_roval2019` | missing_exact_map | — |
| Charlotte Motor Speedway - Roval | `charlotte_2025_roval2025` | missing_exact_map | — |
| Charlotte Motor Speedway - Roval Long | `charlotte_2025_rovalnochicanes` | missing_exact_map | — |
| Crandon International Raceway - Full | `crandon` | identity_review_no_exact_map | crandon_full |
| World Wide Technology Raceway (Gateway) - 2025 - Oval | `gateway_2025_oval` | missing_exact_map | — |
| Hockenheimring Baden-Württemberg - PEC - East | `hockenheim_peceast` | identity_review_no_exact_map | hockenheim_pec_peceast |
| Hockenheimring Baden-Württemberg - PEC - Handling | `hockenheim_pechandling` | identity_review_no_exact_map | hockenheim_pec_pechandling |
| Hockenheimring Baden-Württemberg - PEC - Outer | `hockenheim_pecouter` | identity_review_no_exact_map | hockenheim_pec_pecouter |
| Hockenheimring Baden-Württemberg - PEC - West | `hockenheim_pecwest` | identity_review_no_exact_map | hockenheim_pec_pecwest |
| Huset's Speedway | `husets` | missing_exact_map | — |
| Iowa Speedway - Oval | `iowa_2025_oval` | missing_exact_map | — |
| Iowa Speedway - Infield Road Course | `iowa_infroad` | missing_exact_map | — |
| Circuit de Nevers Magny-Cours - Grand Prix | `magnycours_grandprix` | identity_review_no_exact_map | magnycours_gp |
| Autódromo Hermanos Rodríguez (Mexico City) - EV Circuit | `mexicocity_ev` | missing_exact_map | — |
| Autódromo Hermanos Rodríguez (Mexico City) - Grand Prix | `mexicocity_gp` | missing_exact_map | — |
| Autódromo Hermanos Rodríguez (Mexico City) - Grand Prix Historic | `mexicocity_gphistoric` | missing_exact_map | — |
| Autódromo Hermanos Rodríguez (Mexico City) - National | `mexicocity_national` | missing_exact_map | — |
| Autódromo Hermanos Rodríguez (Mexico City) - National Historic | `mexicocity_nationalhistoric` | missing_exact_map | — |
| Autódromo Hermanos Rodríguez (Mexico City) - Oval | `mexicocity_oval` | missing_exact_map | — |
| Autódromo Hermanos Rodríguez (Mexico City) - Oval Stadium | `mexicocity_ovalstadium` | missing_exact_map | — |
| Miami International Autodrome - Extended Marina Loop | `miami_exmarinaloop` | missing_exact_map | — |
| Miami International Autodrome - Extended MIA Loop | `miami_extendedmialoop` | missing_exact_map | — |
| Miami International Autodrome - Grand Prix | `miami_gp` | missing_exact_map | — |
| Miami International Autodrome - Marina Loop | `miami_marinaloop` | missing_exact_map | — |
| Miami International Autodrome - MIA Loop | `miami_mialoop` | missing_exact_map | — |
| [Legacy] Michigan International Speedway - 2009 | `michigan2014` | identity_review_no_exact_map | michigan, michigan_2015 |
| Michigan International Speedway | `michigan2018` | identity_review_no_exact_map | michigan_2018 |
| North Wilkesboro Speedway | `northwilkesboro_2025` | missing_exact_map | — |
| Oswego Speedway - Dirt | `oswego_dirtoval` | identity_review_no_exact_map | oswego_dirt |
| Portland International Raceway - Full | `portland_full` | missing_exact_map | — |
| Portland International Raceway - No Chicane | `portland_nochicane` | missing_exact_map | — |
| Richmond Raceway | `richmond_2025` | missing_exact_map | — |
| Rockingham Speedway - Oval | `rockingham_2025_oval` | missing_exact_map | — |
| Centripetal Circuit | `skidpad` | missing_exact_map | — |
| Sonoma Raceway - Open Wheel pre-2008 | `sonoma_2025_irl05` | missing_exact_map | — |
| Sonoma Raceway - Open Wheel 2008-2011 | `sonoma_2025_irl08` | missing_exact_map | — |
| Sonoma Raceway - Open Wheel 2012-2018 | `sonoma_2025_irl12` | missing_exact_map | — |
| Sonoma Raceway - NASCAR Long | `sonoma_2025_nascarlong` | missing_exact_map | — |
| Sonoma Raceway - NASCAR Short | `sonoma_2025_nascarshort` | missing_exact_map | — |
| Summit Point Raceway - Oval | `summit_summit_oval` | missing_exact_map | — |
| Shell V-Power Motorsport Park at The Bend - East Circuit | `thebend_east` | missing_exact_map | — |
| Shell V-Power Motorsport Park at The Bend - GT Circuit | `thebend_gt` | missing_exact_map | — |
| Shell V-Power Motorsport Park at The Bend - International Circuit | `thebend_international` | missing_exact_map | — |
| Shell V-Power Motorsport Park at The Bend - South-West Circuit | `thebend_southwest` | missing_exact_map | — |
| Shell V-Power Motorsport Park at The Bend - Sprint Circuit | `thebend_sprint` | missing_exact_map | — |
| Shell V-Power Motorsport Park at The Bend - West Circuit | `thebend_west` | missing_exact_map | — |
| Shell V-Power Motorsport Park at The Bend - West Plus Circuit | `thebend_westplus` | missing_exact_map | — |
| Thruxton Circuit | `thruxton` | missing_exact_map | — |
| Tsukuba Circuit - 1000 - Reverse | `tsukuba_1kreverse` | identity_review_no_exact_map | tsukuba_1kfullreverse |
| Lucas Oil Speedway - Off Road | `wheatland_road` | missing_exact_map | — |
| Wild West Motorsports Park | `wildwest` | identity_review_no_exact_map | wildwest_full |
| Willow Springs International Raceway | `willow` | identity_review_no_exact_map | willow_international |
| Winton Motor Raceway - Rallycross | `winton_rallycross` | missing_exact_map | — |
| Circuit Zandvoort - Oostelijk | `zandvoort_2023_ostelijk` | identity_review_no_exact_map | zandvoort_2023_oostelijk |
| Circuit Zolder - Alternate | `zolder_2024_alt` | missing_exact_map | — |
| Circuit Zolder - Grand Prix | `zolder_2024_gp` | missing_exact_map | — |

Newer scan keys (including Charlotte 2025, Zolder 2024 and Sonoma 2025) remain separate from legacy bundled maps. Missing geometry is not filled using a different scan or a similar name. The recorded GPS-route fallback requires valid telemetry and a driven route; it is not preloaded coverage.

## Ambiguous article paths

- `lagunaseca` — WeatherTech Raceway Laguna Seca; repeated identical root name plus child layout. Excluded from the definite-layout denominator; direct SDK lookup can still load its exact bundled map.

## Bundled keys not present as exact paths in the snapshot

`california_interiora`, `charlotte_2018_fullroadcourse`, `crandon_full`, `hockenheim_pec_peceast`, `hockenheim_pec_pechandling`, `hockenheim_pec_pecouter`, `hockenheim_pec_pecwest`, `limerock_chicane`, `limerock_full`, `limerock_full_school`, `magnycours_gp`, `michigan`, `michigan_2015`, `michigan_2018`, `mugello_gp`, `oswego_dirt`, `oxford_short`, `phoenix_2012`, `phoenix_2012_oval`, `phoenix_2012_ovalopen`, `richmond`, `slinger_figure8jump`, `tsukuba_1kfullreverse`, `virginia_east`, `virginia_full`, `virginia_north`, `virginia_patriot`, `virginia_patriot_rev`, `virginia_south`, `virginia_west`, `watkinsglen_classic`, `watkinsglen_cupcircuit`, `watkinsglen_fullcourse`, `watkinsglen_fullnoloop`, `wildwest_full`, `willow_international`, `zandvoort_2023_national`, `zandvoort_2023_oostelijk`

These may include article omissions, older layouts or different source names. They remain visible and are never silently reassigned to current layouts. For example, the article lists Mugello Short but omits the bundled Mugello GP key.

## Geometry, coaching and live acceptance

Bundled geometry derives from [SIMRacingAppsServer track data](https://github.com/SIMRacingApps/SIMRacingAppsServer); Copyright © 2015–2024 Jeffrey Gilliam, Apache License 2.0. Original source data and notices are preserved in the source handoff.

- “Surveyed lap fraction” and “GPX distance estimate” describe source positioning. GPX fractions can differ from SDK lap fractions. Prefer live SDK GPS; projection by lap distance is explicitly an estimated XY position.
- A map is not a fastest line, expert braking guide, verified turn-name catalogue or car-specific reference. A compatible clean lap/imported guide must pass the runtime car, exact layout, length, conditions and provenance gates.
- Live detection, map alignment, start/finish orientation, GPS projection error, position freshness and coaching timing still require Windows/iRacing tests for each supported identity.

## Reproduction and files

Run `python windows_build/audit_track_coverage.py` from the repository root (or use the packaged Python). This performs no network requests. Results are deterministic for the same catalog/maps.

- `race_engineer/engineer/catalog/iracing_tracks_2025-12-09.json`: all 536 factual name/path rows, source URL, source line numbers and source/retrieval dates. No HTML or support-page boilerplate.
- `race_engineer/engineer/catalog/map_coverage_summary.json`: compact audited metadata for the in-app Help panel.
- `docs/TRACK_COVERAGE.json`: every official unique path, classification, exact map status, identity-review leads, and every bundled map validation result.
- `docs/TRACK_COVERAGE.csv`: the same per-path statuses for filtering.

To refresh the snapshot, consult the official article, preserve its factual rows and modification/retrieval dates, review container classification and path spelling differences, then rerun the audit. Independently verify service additions missing from that article; do not rename or reuse an old map merely to increase the count.
