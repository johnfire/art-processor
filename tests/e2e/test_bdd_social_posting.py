"""BDD scenarios for social media posting workflows."""

import json
import pytest
from unittest.mock import patch, MagicMock
from pytest_bdd import scenarios, given, when, then, parsers

from src.app.social.mastodon import MastodonPlatform

scenarios("features/social_posting.feature")


@pytest.fixture
def ctx():
    return {}


# --- Given ---

@given("a painting JPEG image file exists")
def painting_image_file(ctx, tmp_path):
    img = tmp_path / "painting.jpg"
    img.write_bytes(b"\xff\xd8\xff\xe0fake jpeg")
    ctx["image_path"] = img


@given("Mastodon is configured with a valid instance URL and token")
def configured_mastodon(ctx):
    platform = MastodonPlatform()
    platform.instance_url = "https://mastodon.example.com"
    platform.access_token = "test_token_123"
    ctx["mastodon"] = platform


@given("Mastodon has no credentials configured")
def unconfigured_mastodon(ctx):
    platform = MastodonPlatform()
    platform.instance_url = ""
    platform.access_token = ""
    ctx["mastodon"] = platform


@given(parsers.parse('the Mastodon media upload returns media ID "{media_id}"'))
def media_upload_returns_id(ctx, media_id):
    ctx["mock_media_id"] = media_id


@given(parsers.parse('the Mastodon status API returns post URL "{post_url}"'))
def status_api_returns_url(ctx, post_url):
    ctx["mock_post_url"] = post_url


@given("the Mastodon media upload returns a response with no media ID")
def media_upload_no_id(ctx):
    ctx["mock_no_media_id"] = True


# --- When ---

@when(parsers.parse('I post the image to Mastodon with caption "{caption}"'))
def post_to_mastodon(ctx, caption):
    mastodon = ctx["mastodon"]
    image_path = ctx["image_path"]

    side_effects = []

    if "mock_media_id" in ctx:
        side_effects.append(_mock_response(json.dumps({"id": ctx["mock_media_id"]}).encode()))
    elif "mock_no_media_id" in ctx:
        side_effects.append(_mock_response(json.dumps({}).encode()))

    if "mock_post_url" in ctx:
        side_effects.append(_mock_response(json.dumps({"url": ctx["mock_post_url"]}).encode()))

    with patch("src.app.social.mastodon.urlopen", side_effect=side_effects):
        result = mastodon.post_image(image_path, caption)

    ctx["result"] = result


# --- Then ---

@then("the post result is successful")
def post_result_successful(ctx):
    assert ctx["result"].success is True


@then("the post result is a failure")
def post_result_failure(ctx):
    assert ctx["result"].success is False


@then(parsers.parse('the returned post URL is "{expected_url}"'))
def post_url_matches(ctx, expected_url):
    assert ctx["result"].post_url == expected_url


@then(parsers.parse('the error message contains "{text}"'))
def error_contains(ctx, text):
    assert text in ctx["result"].error


# --- Helpers ---

def _mock_response(data: bytes) -> MagicMock:
    r = MagicMock()
    r.status = 200
    r.read.return_value = data
    r.__enter__ = lambda s: s
    r.__exit__ = MagicMock(return_value=False)
    return r
