# Smart Folder Watch

**Priority:** 8
**Difficulty:** Medium
**Impact:** Medium

## Summary

Monitor source folders for changes and automatically repack the atlas when files are added, removed, or modified. This enables a live workflow where artists save sprites and the atlas updates in the background.

## How It Works

1. User adds a folder to Spriteful
2. Spriteful watches that folder using filesystem events
3. When a file is added, removed, or modified:
   - Update the image list
   - Repack the atlas
   - Optionally auto-export to the last export path

## Implementation

- Use `QFileSystemWatcher` (built into PySide6) to monitor directories
- On change detected, diff the current file list against the folder contents
- Add/remove entries and trigger `_repack()`
- Add a toggle: "Auto-export on change" with a configured output path

## GUI Changes

- Add a "Watch" toggle button next to "Add Folder"
- Status indicator showing watch state (watching / not watching)
- "Auto-export" checkbox with path selector
