# Project conventions

- Maintain one source tree. Use version.py and CHANGELOG.md for 0.11, 0.12 and later versions. Do not create version-numbered source directories or launchers.
- Start.cmd is the stable user entry point. Preserve existing task data and download paths during upgrades.
- Tests must use generated content and isolated temporary data, never modify or delete personal downloads.
- Run tests/test_integration.py for engine or streaming changes. Use tests/test_playback.py for decoder/playback changes.
- Keep user torrents, task databases, downloaded media, environments and private tracker information out of version control.
