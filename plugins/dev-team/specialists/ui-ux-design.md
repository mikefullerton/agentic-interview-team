# UI/UX & Design Specialist

## Role
Layout, color, typography, animation, forms, visual hierarchy, feedback patterns, state design (loading/empty/error/loaded), platform design languages, progress indication, data display, iconography, spacing, and touch targets.

## Persona
(coming)

## Cookbook Sources
- `guidelines/ui/` (15 files)
- `principles/principle-of-least-astonishment.md`
- `compliance/platform-compliance.md`

## Specialty Teams

### always-show-progress
- **Artifact**: `guidelines/ui/always-show-progress.md`
- **Worker focus**: Determinate progress (bar with percentage) when total work is known; indeterminate (spinner, skeleton, shimmer) when not; no frozen or unresponsive UI
- **Verify**: Every async operation shows progress; no blank/frozen screens; progress type matches whether work total is known

### animation-motion
- **Artifact**: `guidelines/ui/animation-motion.md`
- **Worker focus**: Purposeful motion only — guide attention, show spatial relationships, provide feedback; duration defaults by interaction type (micro 50-100ms through page transitions 300-500ms); respect reduced-motion preferences
- **Verify**: No decorative-only animations; durations fall within range for interaction type; reduced-motion replaces animations with instant changes or crossfades

### color
- **Artifact**: `guidelines/ui/color.md`
- **Worker focus**: Semantic color tokens (not hard-coded hex), limited palette (1 primary + neutrals + semantic), color never the sole state indicator, WCAG AA contrast (4.5:1 text, 3:1 large/UI), dark mode support
- **Verify**: No hard-coded hex values; color always paired with icon/shape/text for state; text contrast ≥4.5:1 normal, ≥3:1 large; dark mode tested

### data-display
- **Artifact**: `guidelines/ui/data-display.md`
- **Worker focus**: Right pattern for content type — list for sequential/scannable, table for comparable multi-attribute, cards for heterogeneous browsable, grid for visual-primary; sort/filter at 10+ items, search at 50+
- **Verify**: Display pattern matches content type and user task; collections 10+ have sort or filter; collections 50+ have search; tables sortable by column

### feedback-patterns
- **Artifact**: `guidelines/ui/feedback-patterns.md`
- **Worker focus**: Feedback weight matches action weight — inline for fields, toast for non-critical confirmations (3-5s auto-dismiss), banner for persistent warnings, dialog only for destructive/irreversible; no dialogs for success
- **Verify**: No success messages in dialogs; destructive actions require dialog with explicitly labeled action (not "OK"); default focus on safe option (Cancel); toast auto-dismisses 3-5s

### form-design
- **Artifact**: `guidelines/ui/form-design.md`
- **Worker focus**: Single-column layout, top-aligned/floating labels, validate on blur (not keystroke), full-form validation on submit, inline errors below field with color+icon+text, pre-fill defaults, mark optional not required
- **Verify**: Single-column layout; errors appear inline below field; errors use color + icon + text; no validation on keystroke; placeholder is not a label replacement

### iconography
- **Artifact**: `guidelines/ui/iconography.md`
- **Worker focus**: Platform-native icon set first (SF Symbols, Material Symbols, Segoe Fluent Icons), all action icons have text label or accessible name, consistent size and weight, minimum 24x24pt interactive, state icons paired with color AND shape
- **Verify**: No action icon without label or accessible name; icon styles consistent (not mixed outlined/filled arbitrarily); interactive icons ≥24x24pt; state icons paired with color + shape

### layout
- **Artifact**: `guidelines/ui/layout.md`
- **Worker focus**: Single-column by default, content-first decisions, consistent alignment, responsive breakpoints via platform adaptive systems (not hard-coded widths), one primary scroll direction per view
- **Verify**: No hard-coded pixel widths for breakpoints; mixed alignment not present; no nested same-direction scrolling; layout adapts from compact to expanded

### platform-design-languages
- **Artifact**: `guidelines/ui/platform-design-languages.md`
- **Worker focus**: Defer to platform HIG (Apple HIG, Material 3, Fluent 2, WCAG 2.1) before applying defaults; use platform-prescribed values for spacing, type size, target size
- **Verify**: Platform HIG values used where prescribed; no gaps in coverage without justified defaults; correct design language applied per target platform

### previews
- **Artifact**: `guidelines/ui/previews.md`
- **Worker focus**: All UI components include preview declarations covering all significant states (default, loading, error, empty, populated); Swift uses `#Preview`, Kotlin uses `@Preview`
- **Verify**: Every component has previews; previews cover all 5 states; previews render/compile without errors

### spacing
- **Artifact**: `guidelines/ui/spacing.md`
- **Worker focus**: 4px base unit (8px primary grid), all spacing on scale 4/8/12/16/24/32/48/64, no arbitrary values (5px, 13px, 37px)
- **Verify**: No spacing values off the 4px scale; screen/container edge padding is 16px; no arbitrary values in padding/margin/gap

### state-design
- **Artifact**: `guidelines/ui/state-design.md`
- **Worker focus**: All four states explicit — loading (skeleton for content-heavy, spinner for actions), empty (icon + message + CTA), error (problem + reason + recovery action, no raw codes), loaded; empty and error designed with same care as loaded
- **Verify**: All four states present for every data-loading view; no blank screen on empty; no raw error codes or stack traces shown to user; empty state has CTA; error state has recovery action

### touch-click-targets
- **Artifact**: `guidelines/ui/touch-click-targets.md`
- **Worker focus**: Platform minimums — iOS 44x44pt, Android 48x48dp, Windows 32x32epx (40 recommended), Web 24x24px (44 recommended); visual element can be smaller than hit area; 8px minimum spacing between adjacent targets
- **Verify**: All interactive elements meet platform minimum target size; adjacent targets have ≥8px spacing; hit area ≥ visual element size

### typography
- **Artifact**: `guidelines/ui/typography.md`
- **Worker focus**: Platform system font (SF Pro, Roboto, Segoe UI Variable, system-ui), body 14-17pt (16px default), minimum 11-12pt for captions, line height 1.4x-1.5x, 2-3 font weights per screen, 45-75 character paragraph width
- **Verify**: System font used (not custom fonts without justification); body text ≥14pt; captions ≥11pt; no more than 3 weights per screen; no all-caps for more than a few words

### visual-hierarchy
- **Artifact**: `guidelines/ui/visual-hierarchy.md`
- **Worker focus**: One primary action/focal point per screen, size and weight (not just color) for heading levels, proximity for grouping, interactive elements visually distinguishable from static, disabled elements muted but discoverable
- **Verify**: One primary CTA per screen identifiable; heading levels use size/weight not color alone; interactive vs. static elements visually distinct; disabled states visible but muted

### least-astonishment
- **Artifact**: `principles/principle-of-least-astonishment.md`
- **Worker focus**: UI behavior matches user expectations — names deliver the behavior they imply, side effects are obvious, no surprising outcomes from standard interactions
- **Verify**: Action labels accurately describe what happens; no hidden side effects from primary actions; UI state after action matches what a reasonable user would predict

### platform-compliance
- **Artifact**: `compliance/platform-compliance.md`
- **Worker focus**: Platform design language followed (HIG/Material/Fluent), native controls preferred, platform touch targets met, platform theming supported (dark mode, high contrast, accent colors), minimum permissions requested
- **Verify**: Each compliance check has status (passed/failed/partial/n-a) with evidence; platform-design-language, native-controls-preference, platform-touch-targets, platform-theming checks all addressed

## Exploratory Prompts

1. What if your most common user action had zero feedback? What would the ripple effects be?

2. Imagine your app is used with poor connectivity. How would that change your approach to feedback, validation, and error messaging?

3. If you removed all "Are you sure?" dialogs, what would actually break? Which destructive actions are truly worth the confirmation friction?

4. What if a user is interrupted mid-task (phone call, app switch)? When they come back, what state are they in?

5. How do platform design languages (HIG, Material, Fluent) influence your decisions? Where do you follow conventions, where do you break them?
