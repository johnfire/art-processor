"""BDD scenarios for Flickr posting workflows."""

import json
import pytest
from unittest.mock import patch, MagicMock
from pytest_bdd import scenarios, given, when, then, parsers

from src.app.social.flickr import FlickrPlatform

scenarios("features/flickr_posting.feature")


@pytest.fixture
def ctx():
    return {}


# --- Given ---

@given("a painting JPEG image file exists for Flickr")
def painting_image_file_flickr(ctx, tmp_path):
    img = tmp_path / "autumn_landscape.jpg"
    img.write_bytes(b"\xff\xd8\xff\xe0fake jpeg")
    ctx["image_path"] = img


@given("Flickr is configured with valid API credentials")
def configured_flickr(ctx):
    platform = FlickrPlatform()
    platform.api_key = "test_api_key"
    platform.api_secret = "test_api_secret"
    platform.oauth_token = "test_oauth_token"
    platform.oauth_token_secret = "test_oauth_secret"
    ctx["flickr"] = platform


@given("Flickr has no credentials configured")
def unconfigured_flickr(ctx):
    platform = FlickrPlatform()
    platform.api_key = ""
    platform.api_secret = ""
    platform.oauth_token = ""
    platform.oauth_token_secret = ""
    ctx["flickr"] = platform


@given(parsers.parse('the Flickr upload API returns photo ID "{photo_id}"'))
def upload_returns_photo_id(ctx, photo_id):
    ctx["mock_photo_id"] = photo_id


@given(parsers.parse('the Flickr login API returns user NSID "{nsid}"'))
def login_returns_nsid(ctx, nsid):
    ctx["mock_nsid"] = nsid


@given(parsers.parse('the Flickr upload API returns an error "{error_msg}"'))
def upload_returns_error(ctx, error_msg):
    ctx["mock_upload_error"] = error_msg


# --- When ---

@when(parsers.parse('I post the image to Flickr with title "{title}" and description "{description}"'))
def post_to_flickr(ctx, title, description):
    flickr = ctx["flickr"]
    image_path = ctx["image_path"]

    if "mock_upload_error" in ctx:
        error_xml = (
            f'<?xml version="1.0" encoding="utf-8"?>'
            f'<rsp stat="fail"><err code="100" msg="{ctx["mock_upload_error"]}" /></rsp>'
        ).encode("utf-8")
        upload_resp = _mock_response(error_xml)
        with patch("src.app.social.flickr.urlopen", return_value=upload_resp):
            result = flickr.post_image(image_path, description, title)
    elif "mock_photo_id" in ctx:
        success_xml = (
            f'<?xml version="1.0" encoding="utf-8"?>'
            f'<rsp stat="ok"><photoid>{ctx["mock_photo_id"]}</photoid></rsp>'
        ).encode("utf-8")
        upload_resp = _mock_response(success_xml)
        nsid = ctx.get("mock_nsid", "")
        login_json = json.dumps({
            "stat": "ok",
            "user": {"id": nsid, "nsid": nsid},
        }).encode("utf-8")
        login_resp = _mock_response(login_json)
        with patch("src.app.social.flickr.urlopen", side_effect=[upload_resp, login_resp]):
            result = flickr.post_image(image_path, description, title)
    else:
        result = flickr.post_image(image_path, description, title)

    ctx["result"] = result


@when('I post the image to Flickr with no title and description "A fine painting"')
def post_to_flickr_no_title(ctx):
    flickr = ctx["flickr"]
    image_path = ctx["image_path"]

    success_xml = (
        f'<?xml version="1.0" encoding="utf-8"?>'
        f'<rsp stat="ok"><photoid>{ctx["mock_photo_id"]}</photoid></rsp>'
    ).encode("utf-8")
    upload_resp = _mock_response(success_xml)
    nsid = ctx.get("mock_nsid", "")
    login_json = json.dumps({
        "stat": "ok",
        "user": {"id": nsid, "nsid": nsid},
    }).encode("utf-8")
    login_resp = _mock_response(login_json)

    with patch("src.app.social.flickr.urlopen", side_effect=[upload_resp, login_resp]):
        result = flickr.post_image(image_path, "A fine painting", "")  # empty alt_text

    ctx["result"] = result


@when("I verify Flickr credentials")
def verify_flickr_credentials(ctx):
    flickr = ctx["flickr"]

    if "mock_nsid" in ctx:
        nsid = ctx["mock_nsid"]
        login_json = json.dumps({
            "stat": "ok",
            "user": {"id": nsid, "nsid": nsid},
        }).encode("utf-8")
        login_resp = _mock_response(login_json)
        with patch("src.app.social.flickr.urlopen", return_value=login_resp):
            ctx["verify_result"] = flickr.verify_credentials()
    else:
        ctx["verify_result"] = flickr.verify_credentials()


# --- Then ---

@then("the Flickr post result is successful")
def flickr_post_successful(ctx):
    assert ctx["result"].success is True, f"Expected success, got error: {ctx['result'].error}"


@then("the Flickr post result is a failure")
def flickr_post_failure(ctx):
    assert ctx["result"].success is False


@then(parsers.parse('the returned Flickr URL contains "{fragment}"'))
def flickr_url_contains(ctx, fragment):
    assert ctx["result"].post_url is not None
    assert fragment in ctx["result"].post_url


@then(parsers.parse('the Flickr error message contains "{text}"'))
def flickr_error_contains(ctx, text):
    assert ctx["result"].error is not None
    assert text in ctx["result"].error


@then("Flickr credential verification returns True")
def flickr_verify_true(ctx):
    assert ctx["verify_result"] is True


@then("Flickr credential verification returns False")
def flickr_verify_false(ctx):
    assert ctx["verify_result"] is False


@then(parsers.parse('the Flickr user NSID is cached as "{nsid}"'))
def flickr_nsid_cached(ctx, nsid):
    assert ctx["flickr"]._user_nsid == nsid


# --- Helpers ---

def _mock_response(data: bytes) -> MagicMock:
    r = MagicMock()
    r.status = 200
    r.read.return_value = data
    r.__enter__ = lambda s: s
    r.__exit__ = MagicMock(return_value=False)
    return r
