# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-26

### Added

- `heard transcribe` command — extract speech from video and transcribe to JSON
- `heard export` command — export transcript JSON to plain text
- faster-whisper backend with VAD silence filtering
- Support for mp4, mkv, avi, mov, wmv, flv, webm, m4v formats
- Configurable model selection (medium, large-v3-turbo, etc.)
- Chinese language transcription by default
- Rich progress bar for transcription status
