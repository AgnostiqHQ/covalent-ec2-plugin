# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [UNRELEASED]

### Updated

- Made EC2 executor async aware
- updated to be compatible with ssh plugin 0.14.0rc0
- Introduced `AWSExecutor` as a second parent to the `EC2Executor`
- Updated requirements.txt to pin aws executor plugins to pre-release version 0.1.0rc0
- Updated requirements.txt to pin ssh plugin to version 0.13.0rc0

### Tests

- Added unit tests for validating attributes and credentials

### Tests

- Using DepsPip instead of DepsBash to install pip dependencies for functional tests & logging executor config
- Added requirements.txt for functional tests

## [0.4.0] - 2022-08-30

### Added

- Added unit and functional tests

### Updated

- Updated terraform provisioner script to write conda location to `/etc/environment`
- Using named conda environment and passing as `conda_env` to SSH executor instead of specifying python path

### Operations

- Reusable version workflow now used

## [0.3.0] - 2022-08-30

### Changed

- Updated `teardown()` to properly destroy resources after completing workflow execution

## [0.2.0] - 2022-08-24

### Changed

- Updated python3_path -> python_path as per new ssh plugin version (0.8.0)
- Always overriding python_path to terraform defined value

### Updated

- Updated provisioning script to be as minimal as possible

## [0.1.0] - 2022-08-19

### Added

- Core files for this repo.
- CHANGELOG.md to track changes (this file).
- Semantic versioning in VERSION.
- CI pipeline job to enforce versioning.
