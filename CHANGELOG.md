# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project partially comply with [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-16

### Added

- support for unixbench as external benchmark
- environment variable to turn off monitors
- rocksdb auto-generated benchmarks

### Changed

- bm-generator optimized
- bm-generator support networking syscalls
- flamegraph selection added to bm-generator pipeline
- update mySQL benchmarks including networking syscalls

## [0.1.0] - 2026-02-04

### Added

- prototype bm-runner python framework for running benchmarks
- prototype bench set of C benchmarks
- prototype bm-generator experimental tooling for generating syscalls benchmarks
