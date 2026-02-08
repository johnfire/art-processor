# Art Processor v4 - Changelog

## Changes from v3

### AI Analysis Now Uses Instagram Version
- **Changed**: System now analyzes the Instagram version (smaller file) instead of the big version
- **Why**: Claude API has a 5MB limit per image - Instagram versions are typically under this limit
- **Behavior**:
  - Analyzes Instagram version for title generation and description
  - Still renames BOTH big and Instagram versions to match
  - Fallback to big version if Instagram version doesn't exist
- **Metadata**: Tracks which version was analyzed in `analyzed_from` field

### How It Works

**File Pairing:**
```
/my-paintings-big/new-paintings/img001.jpg       (e.g., 8MB)
/my-paintings-instagram/new-paintings/img001.jpg (e.g., 2MB)
```

**Processing:**
1. System finds matching pairs
2. Uses Instagram version (2MB) to send to Claude API
3. Generates titles and description
4. Renames both files to: `bavarian_twilight.jpg`

**Result:**
```
/my-paintings-big/new-paintings/bavarian_twilight.jpg       (8MB, renamed)
/my-paintings-instagram/new-paintings/bavarian_twilight.jpg (2MB, renamed)
```

### Metadata Output

```json
{
  "files": {
    "big": "/path/to/my-paintings-big/new-paintings/bavarian_twilight.jpg",
    "instagram": "/path/to/my-paintings-instagram/new-paintings/bavarian_twilight.jpg"
  },
  "analyzed_from": "instagram",
  ...
}
```

### Error Handling

If Instagram version is missing:
- System warns: "No Instagram version found - using big version for analysis"
- Proceeds with big version (may fail if > 5MB)
- Still works, just records `analyzed_from: "big"`

## All Previous Features Retained

- Manual width/height/depth input
- Configurable units (cm/in)
- Separate substrate and medium
- Subject, style, collection metadata
- Single folder processing (new-paintings only)
- All extensible configuration lists

## Usage

```bash
# Ensure both folders have matching files:
# Pictures/my-paintings-big/new-paintings/img001.jpg
# Pictures/my-paintings-instagram/new-paintings/img001.jpg

python main.py process
```

System will:
1. Find all painting pairs
2. Analyze Instagram versions (smaller files)
3. Process interactively
4. Rename BOTH versions to match the selected title
