"""BDD scenarios for social media tracking in painting metadata."""

import json
import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from src.app.social.scheduler import _update_social_media_tracking

scenarios("features/metadata_tracking.feature")


@pytest.fixture
def ctx():
    return {}


# --- Given ---

@given("a painting metadata file with no social media history")
def metadata_no_history(ctx, tmp_path):
    metadata = {
        "filename_base": "test_painting",
        "title": {"selected": "Test Painting"},
        "social_media": {},
    }
    path = tmp_path / "test_painting.json"
    path.write_text(json.dumps(metadata))
    ctx["metadata_path"] = path
    ctx["metadata"] = metadata


@given(parsers.parse("a painting metadata file with mastodon post_count of {count:d}"))
def metadata_with_existing_count(ctx, tmp_path, count):
    metadata = {
        "filename_base": "test_painting",
        "title": {"selected": "Test Painting"},
        "social_media": {
            "mastodon": {
                "last_posted": "2026-01-01T10:00:00",
                "post_url": "https://mastodon.example.com/@user/old",
                "post_count": count,
            }
        },
    }
    path = tmp_path / "test_painting.json"
    path.write_text(json.dumps(metadata))
    ctx["metadata_path"] = path
    ctx["metadata"] = metadata


# --- When ---

@when(parsers.parse('a successful mastodon post is recorded with URL "{post_url}"'))
def record_mastodon_post(ctx, post_url):
    _update_social_media_tracking(ctx["metadata_path"], ctx["metadata"], "mastodon", post_url)
    with open(ctx["metadata_path"]) as f:
        ctx["metadata"] = json.load(f)


# --- Then ---

@then(parsers.parse("the mastodon post count is {count:d}"))
def mastodon_post_count(ctx, count):
    mastodon_entry = ctx["metadata"].get("social_media", {}).get("mastodon", {})
    assert mastodon_entry.get("post_count", 0) == count


@then("the mastodon last_posted date is absent")
def mastodon_last_posted_absent(ctx):
    mastodon_entry = ctx["metadata"].get("social_media", {}).get("mastodon", {})
    assert mastodon_entry.get("last_posted") is None


@then("the mastodon last_posted date is present")
def mastodon_last_posted_present(ctx):
    mastodon_entry = ctx["metadata"].get("social_media", {}).get("mastodon", {})
    assert mastodon_entry.get("last_posted") is not None


@then(parsers.parse('the mastodon post_url is "{expected_url}"'))
def mastodon_post_url(ctx, expected_url):
    mastodon_entry = ctx["metadata"].get("social_media", {}).get("mastodon", {})
    assert mastodon_entry.get("post_url") == expected_url
