# FASO Login - Cloudflare Challenge Solution

## The Issue
FASO uses **Cloudflare** bot protection, not regular CAPTCHA. Cloudflare actively detects automation tools like Playwright.

## Updated Approach

### New Stealth Features Added:
- ✅ Hides `navigator.webdriver` property
- ✅ Removes Playwright markers
- ✅ Fakes Chrome plugins
- ✅ Sets realistic geolocation
- ✅ Adds proper headers

### Best Strategy: Manual Login Helper

Since Cloudflare is very aggressive, use the manual login helper:

```bash
# 1. Copy files
cp manual_login.py .
cp faso_client.py src/

# 2. Login manually (bypasses Cloudflare)
python manual_login.py
```

**In the browser that opens:**
- Login with your credentials
- Cloudflare will verify you're human (may take a few seconds)
- Wait until you see your FASO dashboard
- Press Enter in terminal
- Cookies saved!

```bash
# 3. Run automation (uses saved session)
python main.py test-faso-login
```

## Why This Works

Cloudflare lets you through because:
1. You're a real human logging in
2. Your session cookies prove you passed verification
3. Automation reuses your authenticated session
4. Cloudflare sees a valid session, not a new bot

## Alternative: Try Stealth Mode First

The updated files have anti-detection features. You can try:

```bash
python main.py test-faso-login
```

If Cloudflare still blocks it, fall back to manual login helper.

## Pro Tip

Cloudflare sessions last days/weeks. Login manually once, use automation for weeks!

## Files

- `manual_login.py` - Manual login helper (top folder)
- `faso_client.py` - Updated with Cloudflare stealth (src/ folder)

Both now hide automation markers to avoid Cloudflare detection.
