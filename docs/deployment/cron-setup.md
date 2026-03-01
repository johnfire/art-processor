# Daily Automated Posting - Cron Job Setup

This guide shows you how to set up automated daily posting to all social media platforms at 8:30 AM.

## How It Works

The `daily-post` command:
1. Randomly selects one painting that hasn't been posted in the current round
2. Ensures a 200-character short description exists
3. Posts to all 9 platforms: Mastodon, Bluesky, Instagram, Threads, Cara, Pixelfed, TikTok, Facebook, LinkedIn
4. Updates metadata for each platform (post_count, last_posted, post_url)
5. Uses "rounds" logic: When all paintings have been posted once, starts round 2

## Prerequisites

Before setting up the cron job:

1. **Configure platform credentials** in `.env`:
   ```bash
   # Already configured:
   MASTODON_INSTANCE_URL=https://mastodon.social
   MASTODON_ACCESS_TOKEN=your_token

   # Add these as you get credentials:
   BLUESKY_USERNAME=
   BLUESKY_PASSWORD=

   INSTAGRAM_USERNAME=
   INSTAGRAM_PASSWORD=

   THREADS_USERNAME=
   THREADS_PASSWORD=

   # ... etc for each platform
   ```

2. **Test manual posting**:
   ```bash
   python main.py daily-post
   ```

   This will show you what happens and verify everything works.

## Cron Job Setup

### Step 1: Edit your crontab

```bash
crontab -e
```

### Step 2: Add the daily posting job

Add this line to post every day at 8:30 AM:

```bash
30 8 * * * cd /home/christopher/programming/theo-van-gogh && /usr/bin/python3 main.py daily-post >> /home/christopher/logs/daily-post.log 2>&1
```

**Explanation:**
- `30 8 * * *` = Run at 8:30 AM every day
- `cd /home/christopher/programming/theo-van-gogh` = Change to project directory
- `/usr/bin/python3` = Full path to Python (use `which python3` to find yours)
- `main.py daily-post` = Run the daily post command
- `>> /home/christopher/logs/daily-post.log` = Append output to log file
- `2>&1` = Redirect errors to the log file too

### Step 3: Create log directory

```bash
mkdir -p /home/christopher/logs
```

### Step 4: Verify cron job is scheduled

```bash
crontab -l
```

You should see your new cron entry.

## Alternative: Systemd Timer (More Modern)

If you prefer systemd over cron:

### 1. Create service file

Create `/etc/systemd/system/theo-daily-post.service`:

```ini
[Unit]
Description=Theo-van-Gogh Daily Social Media Post
After=network.target

[Service]
Type=oneshot
User=christopher
WorkingDirectory=/home/christopher/programming/theo-van-gogh
Environment="PATH=/usr/bin:/bin"
ExecStart=/usr/bin/python3 /home/christopher/programming/theo-van-gogh/main.py daily-post
StandardOutput=append:/home/christopher/logs/daily-post.log
StandardError=append:/home/christopher/logs/daily-post.log

[Install]
WantedBy=multi-user.target
```

### 2. Create timer file

Create `/etc/systemd/system/theo-daily-post.timer`:

```ini
[Unit]
Description=Run Theo-van-Gogh daily post at 8:30 AM
Requires=theo-daily-post.service

[Timer]
OnCalendar=*-*-* 08:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

### 3. Enable and start the timer

```bash
sudo systemctl daemon-reload
sudo systemctl enable theo-daily-post.timer
sudo systemctl start theo-daily-post.timer
```

### 4. Check timer status

```bash
systemctl list-timers --all | grep theo
systemctl status theo-daily-post.timer
```

## Monitoring and Logs

### View recent logs

```bash
tail -f /home/christopher/logs/daily-post.log
```

### View last 100 lines

```bash
tail -n 100 /home/christopher/logs/daily-post.log
```

### Check if posting succeeded

```bash
grep -i "succeeded" /home/christopher/logs/daily-post.log | tail -n 10
```

### Check for errors

```bash
grep -i "failed\|error" /home/christopher/logs/daily-post.log | tail -n 20
```

## Manual Testing

Before relying on automation, test manually:

```bash
# Test once
python main.py daily-post

# Check rounds status
cat ~/ai-workzone/processed-metadata/rounds.json

# Check a painting's metadata to see post counts
cat ~/ai-workzone/processed-metadata/some-folder/some-painting.json | grep -A 20 social_media
```

## Troubleshooting

### Cron job not running?

1. **Check cron is running:**
   ```bash
   systemctl status cron
   ```

2. **Check logs:**
   ```bash
   tail -f /var/log/syslog | grep CRON
   ```

3. **Test with simpler time:**
   Temporarily change to run every 5 minutes for testing:
   ```bash
   */5 * * * * cd /home/christopher/programming/theo-van-gogh && /usr/bin/python3 main.py daily-post >> /home/christopher/logs/daily-post.log 2>&1
   ```

### Environment variables not loading?

Cron doesn't load your normal environment. Make sure:

1. Paths are absolute
2. `.env` file is in the project directory
3. Python can find all modules

### Still not working?

Run this diagnostic script:

```bash
# Save as test-cron-env.sh
#!/bin/bash
cd /home/christopher/programming/theo-van-gogh
echo "Current directory: $(pwd)"
echo "Python version: $(python3 --version)"
echo "User: $(whoami)"
echo "Environment:"
env | sort
echo "---"
python3 main.py daily-post
```

Then add to cron:
```bash
30 8 * * * /path/to/test-cron-env.sh >> /home/christopher/logs/cron-diagnostic.log 2>&1
```

## Platform Configuration Checklist

Before the cron job can post, you need credentials for each platform:

- [ ] Mastodon (configured ✓)
- [ ] Bluesky
- [ ] Instagram
- [ ] Threads
- [ ] Cara
- [ ] Pixelfed
- [ ] TikTok
- [ ] Facebook
- [ ] LinkedIn

**Note:** Platforms without credentials will be skipped but still counted (to keep post_count in sync across all platforms).

## Success!

Once set up, your system will:
- Post one random painting every day at 8:30 AM
- Rotate through all paintings before repeating
- Keep track of how many times each painting has been posted
- Log all activity for monitoring

Check your logs daily for the first week to ensure everything is working smoothly!
