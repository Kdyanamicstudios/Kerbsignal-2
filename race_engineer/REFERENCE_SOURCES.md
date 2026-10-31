# Reference data status

## Available in this development build

- Your recorded clean laps, matched to exact SDK car/layout IDs and weather/aid context.
- Native `.ibt` imports: recorded SessionTime, exact SDK metadata, incident/off-track validation and complete-lap selection. No upload or provider account is required.
- Garage 61 API integration: fastest clean, downloadable lap visible to the user's access token, with exact car/layout mapping. Tokens stay in memory.
- JSON reference exchange for complete, matched recordings.

## Timing quality

Native recordings retain recorded timestamps. Garage 61 CSV lacks a timestamp column in the inspected native export, so its timing is reconstructed from distance/speed and checked against declared lap time. Reconstructed timing is now explicitly marked estimated; spoken feedback avoids presenting estimated corner-loss decimals as exact. Distances and pedal differences remain position aligned.

## Provider access and coverage

The official Garage 61 OpenAPI specification states that default lap-search and CSV access is limited to the authenticated user and teammates, subject to privacy settings. Broader visible-data access requires provider approval. The application does not redistribute downloaded private telemetry or label accessible laps as world records.

A comprehensive licensed expert-lap catalogue for every iRacing car/layout remains unavailable to this project. Local IBT imports expand usable references; they do not establish global optimality or universal expert coverage.

Primary sources reviewed October 30, 2026:
- https://garage61.net/api/openapi/v1.json
- https://garage61.net/developer/endpoints/v1/getLapCSV
- https://garage61.net/docs/usage/filtering
- https://github.com/kutu/pyirsdk/blob/master/irsdk.py (IBT binary structure reference; this importer is implemented in the app's existing read-only SDK style)
