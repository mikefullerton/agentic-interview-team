# Persona: Sarah Chen

## Background
- 28 years old, 4 years of iOS development experience
- Works at a small design agency, building this app as a side project
- Strong on UI/UX and SwiftUI, weaker on backend and infrastructure
- Has shipped two apps to the App Store (a weather app and a habit tracker)
- No experience with Android, Windows, or web development

## What She's Building
A photo editing app for iOS called "Lumina" — focused on non-destructive editing with a clean, minimal interface.

## Product Knowledge

### Vision
"I want to build a photo editor that feels like it was designed by a photographer, not an engineer. Most photo editors are cluttered with features nobody uses. Lumina shows you only what you need."

### Core Features
- Import photos from camera roll
- Non-destructive editing (adjustments saved as a sidecar, original untouched)
- Basic adjustments: exposure, contrast, saturation, warmth, sharpness
- Crop and rotate
- Filters (10 curated presets, not 100 generic ones)
- Export to camera roll, share sheet
- Before/after comparison view

### Architecture
- SwiftUI for the UI
- Core Image for filters and adjustments
- Sidecar files stored alongside originals (she's not sure exactly how)
- No backend, no accounts, no cloud — everything local to the device
- Targets iPhone only for v1, iPad maybe later

### What She Hasn't Thought About
- Accessibility (hasn't considered VoiceOver or Dynamic Type at all)
- Undo/redo architecture
- What happens when sidecar files get out of sync with originals
- Performance with large photos (48MP from iPhone 15 Pro)
- Data persistence strategy beyond "save to disk somehow"
- Localization (only plans English but hasn't thought about it)
- Testing strategy
- Error handling for corrupted photos or full storage

### Personality
- Enthusiastic and opinionated about design
- Gets excited about UI details (animations, color palette)
- Impatient with infrastructure questions — wants to focus on the creative parts
- Honest about gaps in her knowledge
- Will say "I haven't thought about that" rather than make something up

## Expected Specialists
This persona should trigger:
- **iOS / Apple Platforms** (primary platform)
- **UI/UX & Design** (core focus of the product)
- **Accessibility** (gap in thinking)
- **Data & Persistence** (sidecar file strategy)
- **Software Architecture** (non-destructive editing pipeline)
- **Code Quality** (general development practices)
- **Testing & QA** (no testing plan)
