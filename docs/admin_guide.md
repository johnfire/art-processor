# Theo-van-Gogh — Admin Menu Guide

A plain-language explanation of every option in the admin menu.
Access the admin menu by running `python main.py admin` or selecting it at startup.

---

## Option 1 — Edit Anthropic API Key

**What it does:**
Updates the `ANTHROPIC_API_KEY` in your `.env` file. This key is required for the AI to generate painting titles and descriptions.

**When to use it:**
When you first set up the system, or when your API key expires or is rotated. The current key is displayed masked (first 8 characters only) so you can confirm which key is active.

**What it changes:**
The `ANTHROPIC_API_KEY` line in your `.env` file. Nothing else is touched.

---

## Option 2 — Edit File Paths

**What it does:**
Updates the three main folder paths in your `.env` file:
- **Big paintings folder** — where your full-resolution painting images are stored
- **Instagram paintings folder** — where your square/cropped versions are stored
- **Metadata output folder** — where the generated JSON and text metadata files are saved

**When to use it:**
When you move your painting folders to a new location, or when setting up the system on a new machine.

**What it changes:**
`PAINTINGS_BIG_PATH`, `PAINTINGS_INSTAGRAM_PATH`, and `METADATA_OUTPUT_PATH` in your `.env` file.

---

## Option 3 — Edit Dimension Unit

**What it does:**
Sets whether painting dimensions are recorded in centimetres (`cm`) or inches (`in`). This affects how dimensions appear in metadata and on gallery sites.

**When to use it:**
Once at setup, depending on your preference or which gallery sites you primarily sell through. Can be changed later but note that existing metadata will still show the old unit — only new paintings pick up the change automatically.

**What it changes:**
The `DIMENSION_UNIT` value in `config/settings.py`.

---

## Option 4 — Add to Lists

**What it does:**
Adds new entries to the dropdown lists used when processing paintings. The lists are:
- **Substrates** — e.g. Canvas, Linen, Panel, Paper
- **Mediums** — e.g. Oil, Acrylic, Watercolour
- **Subjects** — e.g. Landscape, Portrait, Still Life
- **Styles** — e.g. Realism, Impressionism, Abstract
- **Collections** — named groups of paintings (e.g. "Sea Beasties from Titan")

**When to use it:**
Whenever you start working in a new medium, develop a new collection, or need a subject or style that isn't in the list yet.

**What it changes:**
The relevant list in `config/settings.py`. New entries appear immediately next time you process a painting.

---

## Option 5 — Manage Social Media Platforms

**What it does:**
Views the list of social media platforms currently tracked in the upload tracker and allows you to add new ones. This is a legacy option from the original upload tracking system.

**When to use it:**
Rarely needed now — the platform list is managed through `config/settings.py` and the social media framework. Use this only if directed to by a support note.

---

## Option 6 — Sync Collection Folders

**What it does:**
Scans your configured collections list and creates any missing folders in your paintings directories. For example, if "Surreal Botanicals" is in your collections list but the folder doesn't exist yet on disk, this creates it.

**When to use it:**
After adding a new collection via Option 4, or after moving your paintings to a new drive. Safe to run any time — it only creates folders, never deletes anything.

**What it changes:**
Creates new directories inside `PAINTINGS_BIG_PATH` and `PAINTINGS_INSTAGRAM_PATH`. No existing files are touched.

---

## Option 7 — View Current Settings

**What it does:**
Displays a summary of your current configuration: the Anthropic API key (masked), the dimension unit, and the number of entries in each list (substrates, mediums, subjects, styles, collections).

**When to use it:**
To quickly confirm the system is configured correctly, or to check how many items are in your lists before adding more.

**What it changes:**
Nothing — read-only.

---

## Option 8 — Generate Skeleton Metadata

**What it does:**
Scans your paintings folders for image files that do not yet have a metadata JSON file and creates a minimal stub file for each one. The stub contains the filename and placeholder values for all required fields.

**When to use it:**
When you have existing paintings on disk that were never run through the full `process` command. The stubs let you manually fill in metadata without going through the interactive AI workflow.

**What it changes:**
Creates new `.json` stub files in your metadata output folder. Existing metadata files are not overwritten.

---

## Option 9 — Edit Metadata

**What it does:**
Opens an interactive browser for your metadata files. You can navigate through paintings by collection, select a painting, and edit individual fields (title, description, price, medium, dimensions, etc.) directly without running the full process command.

**When to use it:**
To correct a mistake in a painting's metadata, update a price, improve a description, or fill in fields that were left blank during initial processing.

**What it changes:**
Writes changes directly to the painting's `.json` metadata file.

---

## Option 10 — Sync Instagram Folders

**What it does:**
Reorganises the instagram-paintings folder so its subfolder structure matches the big-paintings folder. If you have moved paintings into collection subfolders in the big folder, this creates the matching subfolders in the instagram folder and moves the corresponding images.

**When to use it:**
After reorganising your big-paintings folders, or after running Option 6 to create new collection folders, to keep both folder trees in sync.

**What it changes:**
Creates subfolders and moves image files within `PAINTINGS_INSTAGRAM_PATH`. Does not touch the big-paintings folder.

---

## Option 11 — Upload to FASO

**What it does:**
Opens a Chromium browser and uploads paintings to your Fine Art Studio Online (FASO) gallery. For each painting, it navigates to the upload page, uploads the image file, and fills in the metadata form (title, medium, substrate, dimensions, subject, style, collection, price, and description) automatically.

**When to use it:**
Whenever you have new paintings ready to go on your FASO site. The system shows you a list of paintings that haven't been uploaded yet and lets you choose which ones to upload.

**Requires:**
A valid FASO browser session. If you haven't logged in recently, run Option 17 first.

**What it changes:**
Uploads images and metadata to your FASO account. After a successful upload, marks the painting as uploaded in its local metadata JSON.

---

## Option 12 — Find Painting

**What it does:**
Searches for a painting by name across both the big-paintings and instagram-paintings folders. The search is fuzzy — it ignores case, dashes, underscores, and trailing numbers, so "black palm" finds "Black_Palm_1.jpg" and similar variations.

**When to use it:**
When you want to find where a painting file is stored on disk, or confirm that both the big and instagram versions exist.

**What it changes:**
Nothing — read-only search.

---

## Option 13 — Post to Social Media

**What it does:**
Posts a painting to one of your social media accounts. Shows you a list of configured platforms, lets you choose one, then shows the paintings that haven't been posted there yet. You select a painting, preview the post text, and confirm before it posts.

**Supported platforms:**
Mastodon, Bluesky, Pixelfed, Flickr, Cara (and others as they are implemented).

**When to use it:**
Whenever you want to share a painting with your social media audience.

**What it changes:**
Creates a post on the selected platform and updates `last_posted`, `post_url`, and `post_count` in the painting's metadata JSON.

---

## Option 14 — Schedule Posts

**What it does:**
Schedules a painting post for a specific future date and time. You choose the platform, the painting, and when to post. The system saves the schedule entry and executes it automatically when the time arrives (via a cron job running `python main.py check-schedule`).

**When to use it:**
When you want to plan your social media content in advance — for example, posting every Monday at 9am without having to do it manually.

**What it changes:**
Adds an entry to the schedule file (`schedule.json`). No post is made immediately.

---

## Option 15 — View Schedule

**What it does:**
Displays two lists: upcoming scheduled posts (not yet due) and recent posting history (completed and failed posts). Shows the painting name, platform, scheduled time, and status for each entry.

**When to use it:**
To review what's coming up, confirm a schedule entry was created correctly, or check whether a scheduled post succeeded or failed.

**What it changes:**
Nothing — read-only.

---

## Option 16 — Migrate Tracking Data

**What it does:**
A one-time migration tool. Moves upload tracking data from the old `upload_status.json` file into each painting's individual metadata JSON file (under `gallery_sites` and `social_media` fields). This was run once when the tracking system was upgraded.

**When to use it:**
Only if you are upgrading from a very early version of the system that still uses `upload_status.json`. Safe to run again — it is idempotent — but has no effect if migration was already completed.

**What it changes:**
Updates `gallery_sites` and `social_media` fields in individual metadata JSON files.

---

## Option 17 — Manual Site Login

**What it does:**
Opens a real browser window so you can log into FASO or Cara manually. Once logged in, the session is saved to a persistent browser profile so future uploads and posts can run without you having to log in again. Also records the login timestamp so the system can warn you when the session is getting old.

**When to use it:**
- First time setting up FASO or Cara
- After the system warns you that a session has expired
- Approximately every 30 days for platforms that time out

**What it changes:**
Saves browser session data to `~/.config/theo-van-gogh/cookies/`. Records login timestamp in `login_status.json`.

---

## Option 0 — Exit Admin Mode

Returns to the main command line.
