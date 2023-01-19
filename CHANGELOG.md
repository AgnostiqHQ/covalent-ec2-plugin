# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [UNRELEASED]

## [0.13.0] - 2023-01-19

### Changed

- Moved EC2 plugin specific validation to setup (checking key file existance)
- Parsing region and profile from boto3 session (determined by AWS Base Executor)
- Removed functional test executor instance in favour of config file configuration

## [0.12.0] - 2022-11-22

### Changed

- Removed executor defaults for boto3 session args

## [0.11.0] - 2022-11-22

### Changed

- Functional tests using pytest and .env file configuration

## [0.10.0] - 2022-10-28

### Changed

- Updated SSH plugin version to correspond with covalent >=0.202.0,<1

## [0.9.0] - 2022-10-27

### Changed

- Added Alejandro to paul blart group

## [0.8.1] - 2022-10-26

### Fixed

- Fixed a race condition that arises from running `terraform init` in an asynchronous manner from multiple electrons
## [0.8.0] - 2022-10-26

### Changed

- Bumped `covalent` version to `0.202.0`

## [0.7.0] - 2022-10-25

### Changed

- Pinned version of covalent-aws-plugins to be gt than 0.7.0rc0 & covalent-ssh-plugin to be gt than 0.15.0rc0

## [0.6.2] - 2022-10-06

### Fixed

- Store `BASE_COVALENT_AWS_PLUGINS_ONLY` in a temporary file rather than storing it as an environment variable.

### Docs

- Updated docs to include more information about required/optional config values, and provide information about each cloud resource that needs to be provisioned

## [0.6.1] - 2022-10-04

### Fixed

- Moved `infra` folder to live within `covalent_ec2_plugin` module and added missing init file to include during installation

## [0.6.0] - 2022-09-30

### Added

-  Logic to specify that only the base covalent-aws-plugins package is to be installed.

### Updated

## [0.5.1] - 2022-09-29

### Fixed

- Typo in `release.yml`

## [0.5.0] - 2022-09-29

### Added

- Added license workflow

### Changed

- Made EC2 executor async aware
- updated to be compatible with ssh plugin 0.14.0rc0
- Introduced `AWSExecutor` as a second parent to the `EC2Executor`
- Updated requirements.txt to pin aws executor plugins to pre-release version 0.1.0rc0
- Updated requirements.txt to pin ssh plugin to version 0.13.0rc0

### Tests

- Added unit tests for validating attributes and credentials
- Using DepsPip instead of DepsBash to install pip dependencies for functional tests & logging executor config
- Added requirements.txt for functional tests

## [0.4.0] - 2022-08-30

### Added

- Added unit and functional tests

### Changed

- Updated terraform provisioner script to write conda location to `/etc/environment`
- Using named conda environment and passing as `conda_env` to SSH executor instead of specifying python path
- Reusable version workflow now used

## [0.3.0] - 2022-08-30

### Changed

- Updated `teardown()` to properly destroy resources after completing workflow execution

## [0.2.0] - 2022-08-24

### Changed

- Updated python3_path -> python_path as per new ssh plugin version (0.8.0)
- Always overriding python_path to terraform defined value
- Updated provisioning script to be as minimal as possible

## [0.1.0] - 2022-08-19

### Added

- Core files for this repo.
- CHANGELOG.md to track changes (this file).
- Semantic versioning in VERSION.
- CI pipeline job to enforce versioning.
