# Changelog

## Pending
### Fixed
- Shared logger provider being closed prematurely (#32)
- Ensure `handling_log` set to false if emit fails

### Changed
- Drop Python 3.9 support, add Python 3.13 and 3.14 support (#33)

## [1.0.2] 2025-12-05
### Changed
- Rename `scout_request_id` log attribute to `scout_transaction_id` for compatibility (#28)

## [1.0.1] 2024-09-12
### Added
- Django configuration compatibility (#24)
- Update package name in documentation (#22)

## [1.0.0] 2024-09-10
### Added
- Rename handler class to `ScoutLogHandler` for clarity (#19)

## [0.1.2] 2024-09-05
### Added
- Update readme with installation instructions (#17)
- Setting controller endpoint on log records (#15)
- Release workflow for automated publishing (#13)
- Attach controller endpoint to log entries (#11)
- Tests and GitHub Actions CI (#7)
- Scout Request Context integration (#5)
- Initial logging handler implementation (#3)
- OpenTelemetry logger integration (#1)
- Initial commit
