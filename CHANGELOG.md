# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Guide]

* **Added** for new features
* **Changed** for changes in existing functionality.
* **Deprecated** for soon-to-be removed features.
* **Removed** for now removed features.
* **Fixed** for any bug fixes.
* **Security** in case of vulnerabilities

## [0.2.0] - 2026-07-16

### Added

* Added new features to the dashboard.
    * Users are now able to view metadata information about their samples.
    * Live monitoring view shows for 1 hr, with capability to select start and end times for viewing.
* Updates to data query as we modified how collections on MongoDB are formatted.
    * Collections now correspond to data source (metadata, timeseries, etc) instead of actuator data.

## [0.1.0] - 2025-07-30

### Added

* `README.md` for dashboard usage and package installation
* `CHANGELOG.md` to keep track of dashboard changes
* `requirements.txt` list of necessary packages to install for dashboard
* `\src` scripts to run the dashboard (`app.py` `config.py` `plots.py` `query.py`)
