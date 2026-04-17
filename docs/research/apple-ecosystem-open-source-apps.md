# Top MIT-licensed Open-Source Apps for Apple Platforms

**Date captured:** 2026-04-16
**Next review:** 2026-07-16 (quarterly)
**Source:** GitHub `gh search repos` with `--license=mit --archived=false --sort=stars`
**Point-in-time:** star counts and push dates change continuously; re-run to refresh.

## Criteria

- **License:** MIT
- **Platform:** ships a runnable app for at least one Apple platform (macOS, iOS, iPadOS, watchOS, tvOS, visionOS)
- **Kind:** end-user app — *not* frameworks, libraries, SDKs, or dev-only CLIs
- **Active:** last push within the previous ~12 months (on or after ~2025-04-16)
- **Ranking:** by star count, descending

## Top 10

| # | Repo | ⭐ | Last push | What it is |
|---|------|---:|-----------|------------|
| 1 | [marktext/marktext](https://github.com/marktext/marktext) | 55,279 | 2026-03-04 | Clean real-time-preview Markdown editor for macOS/Windows/Linux. |
| 2 | [tw93/Mole](https://github.com/tw93/Mole) | 47,650 | 2026-04-16 | Mac cleaner/optimizer — disk cleanup, cache purge, app uninstaller. |
| 3 | [vercel/hyper](https://github.com/vercel/hyper) | 44,613 | 2026-04-13 | Electron terminal emulator with a rich plugin ecosystem. |
| 4 | [exelban/stats](https://github.com/exelban/stats) | 37,992 | 2026-04-16 | macOS menu-bar system monitor (CPU/GPU/memory/network/battery/sensors). |
| 5 | [MonitorControl/MonitorControl](https://github.com/MonitorControl/MonitorControl) | 32,963 | 2026-02-09 | Control external-display brightness/volume from the Mac keyboard. |
| 6 | [qier222/YesPlayMusic](https://github.com/qier222/YesPlayMusic) | 32,770 | 2026-01-18 | Third-party NetEase Cloud Music desktop player for Win/macOS/Linux. |
| 7 | [DevToys-app/DevToys](https://github.com/DevToys-app/DevToys) | 31,231 | 2026-02-25 | "Swiss Army knife for developers" — 30+ offline utilities. |
| 8 | [CodeEditApp/CodeEdit](https://github.com/CodeEditApp/CodeEdit) | 22,801 | 2026-04-12 | Native Swift macOS code editor aiming for an Xcode-like feel. |
| 9 | [nikitabobko/AeroSpace](https://github.com/nikitabobko/AeroSpace) | 20,287 | 2026-04-14 | i3-like tiling window manager for macOS. |
| 10 | [ayangweb/BongoCat](https://github.com/ayangweb/BongoCat) | 20,264 | 2026-04-16 | Cross-platform interactive desktop pet that reacts to input. |

## Alternates (11–17)

| # | Repo | ⭐ | Last push | What it is |
|---|------|---:|-----------|------------|
| 11 | [super-productivity/super-productivity](https://github.com/super-productivity/super-productivity) | 18,649 | 2026-04-16 | Advanced todo app with timeboxing, time tracking, Jira/GitLab/GitHub integrations. |
| 12 | [ianyh/Amethyst](https://github.com/ianyh/Amethyst) | 16,081 | 2026-04-05 | Automatic tiling window manager for macOS, à la xmonad. |
| 13 | [Hammerspoon/hammerspoon](https://github.com/Hammerspoon/hammerspoon) | 15,245 | 2026-02-26 | macOS desktop automation scriptable with Lua. |
| 14 | [dwarvesf/hidden](https://github.com/dwarvesf/hidden) | 13,760 | 2026-03-03 | Ultra-light macOS utility that hides menu-bar icons. |
| 15 | [popcorntime/popcorntime](https://github.com/popcorntime/popcorntime) | 10,517 | 2026-04-16 | Streaming movie/TV client (note: torrent-based; legally grey). |
| 16 | [webtorrent/webtorrent-desktop](https://github.com/webtorrent/webtorrent-desktop) | 10,049 | 2026-04-13 | Streaming torrent app for Mac/Windows/Linux. |
| 17 | [Ranchero-Software/NetNewsWire](https://github.com/Ranchero-Software/NetNewsWire) | 9,930 | 2026-04-16 | Native RSS reader for macOS *and* iOS — rare dual-platform Apple app. |

## Excluded but notable

These were high-star candidates dropped by the "active" filter:

| Repo | ⭐ | Status | Reason dropped |
|------|---:|--------|----------------|
| [atom/atom](https://github.com/atom/atom) | 60,873 | Archived 2022-12 | Sunset by GitHub; would be #1 by stars. |
| [nylas/nylas-mail](https://github.com/nylas/nylas-mail) | 24,774 | Last push 2022-11 | Effectively dead; repo not marked archived but no activity in 3+ years. |
| [agalwood/Motrix](https://github.com/agalwood/Motrix) | 51,400 | Last push 2024-07 | ~21 months stale; would be #2 by stars if revived. |
| [wulkano/Kap](https://github.com/wulkano/Kap) | 19,191 | Last push 2024-11 | ~17 months stale; screen recorder. |

## Methodology

Three parallel GitHub searches:

```bash
gh search repos --topic=macos --license=mit --sort=stars --limit=60 --archived=false \
  --json fullName,stargazersCount,description,pushedAt,isArchived

gh search repos --topic=ios --license=mit --sort=stars --limit=60 --archived=false \
  --json fullName,stargazersCount,description,pushedAt,isArchived

gh search repos --topic=swift --license=mit --sort=stars --limit=40 \
  --json fullName,stargazersCount,description,language
```

Combined the result sets, de-duplicated, then filtered by hand to:

1. Exclude frameworks/libraries/SDKs (Alamofire, RxSwift, Kingfisher, SDWebImage, SwifterSwift, Hero, SnapKit, etc.).
2. Exclude cross-platform frameworks that don't themselves ship an app (react-native, Expo, Ionic, Avalonia, .NET MAUI, kivy, Quasar, Capacitor, Wails, fastlane, etc.).
3. Exclude repos whose "Apple support" is incidental (Docker images, Linux-primary tools, web-app boilerplates, theme ports).
4. Exclude apps whose last push is older than ~12 months.

Star counts and push dates in the tables above are copied verbatim from the search output on 2026-04-16; they will drift as projects evolve.
