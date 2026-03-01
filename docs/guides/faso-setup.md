# FASO Login Test - Setup Guide

## Step 1: Add Your Credentials

Edit `config/settings.py` or `.env` file:

### Option A: In .env file (recommended)
```bash
FASO_EMAIL=your-email@example.com
FASO_PASSWORD=your-password-here
```

### Option B: Directly in settings.py
```python
FASO_EMAIL = "your-email@example.com"
FASO_PASSWORD = "your-password-here"
```

## Step 2: Install Playwright Browsers

```bash
# Activate venv
source venv/bin/activate

# Install Playwright browsers (only needed once)
playwright install chromium
```

## Step 3: Run the Test

```bash
python main.py test-faso-login
```

## What the Test Does

1. Opens a Chrome browser (visible, not headless)
2. Goes to https://data.fineartstudioonline.com/login/
3. Types your email slowly (100ms between keystrokes)
4. Types your password slowly
5. Clicks submit
6. Waits for login to complete
7. Looks for "Works" in the left menu
8. Clicks "Works"
9. Looks for "Add New Artwork" link
10. Clicks "Add New Artwork"
11. Takes screenshots at each step
12. Pauses 10 seconds so you can see the form
13. Closes browser

## Watch For

- **If it stops at login**: Check if CAPTCHA appeared, credentials wrong
- **If it can't find "Works"**: Check debug_after_login.png screenshot
- **If it can't find "Add New Artwork"**: Check debug_works_page.png screenshot
- **If successful**: You'll see add_artwork_form.png screenshot

## Debug Screenshots

The test creates these screenshots:
- `debug_after_login.png` - Right after login
- `debug_works_page.png` - On the Works page
- `add_artwork_form.png` - The Add Artwork form (success!)
- `debug_error.png` - If an error occurs

## Next Steps

Once we can reach the Add Artwork form:
1. We'll inspect the form fields
2. Map them to our metadata
3. Build the upload function
4. Test uploading a painting!

## Troubleshooting

### "playwright: command not found"
```bash
pip install playwright
playwright install chromium
```

### "FASO credentials not configured"
Add them to `.env` or `settings.py` (see Step 1)

### CAPTCHA appears
- The typing is already slow (100ms between keys)
- If CAPTCHA still appears, we may need to add more delays
- Or use a different approach (cookies/session persistence)

### Browser doesn't open
Make sure you're not in headless mode. The test uses `headless=False` by default.
