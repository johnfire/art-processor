"""BDD scenarios for the social media post scheduler."""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from src.app.social.scheduler import Scheduler

scenarios("features/scheduler.feature")


@pytest.fixture
def ctx():
    return {}


# --- Given ---

@given("an empty schedule")
def empty_schedule(ctx, tmp_path):
    schedule_file = tmp_path / "schedule.json"
    ctx["scheduler"] = Scheduler(schedule_file=schedule_file)


@given(parsers.parse('a post for "{content_id}" on "{platform}" is scheduled at "{scheduled_time}"'))
def add_scheduled_post(ctx, content_id, platform, scheduled_time, tmp_path):
    metadata_file = tmp_path / f"{content_id}.json"
    metadata_file.write_text("{}")
    post_id = ctx["scheduler"].add_post(
        content_id=content_id,
        metadata_path=str(metadata_file),
        platform=platform,
        scheduled_time=scheduled_time,
    )
    ctx["last_post_id"] = post_id


# --- When ---

@when(parsers.parse('I schedule a post for "{content_id}" on "{platform}" at "{scheduled_time}"'))
def schedule_post(ctx, content_id, platform, scheduled_time, tmp_path):
    metadata_file = tmp_path / f"{content_id}.json"
    metadata_file.write_text("{}")
    post_id = ctx["scheduler"].add_post(
        content_id=content_id,
        metadata_path=str(metadata_file),
        platform=platform,
        scheduled_time=scheduled_time,
    )
    ctx["last_post_id"] = post_id


@when("I request posts due now")
def get_due_posts(ctx):
    ctx["due_posts"] = ctx["scheduler"].get_pending()


@when(parsers.parse('I mark the post as posted to "{post_url}"'))
def mark_posted(ctx, post_url):
    ctx["scheduler"].mark_posted(ctx["last_post_id"], post_url)


@when("I cancel the post")
def cancel_post(ctx):
    ctx["scheduler"].cancel_post(ctx["last_post_id"])


# --- Then ---

@then(parsers.parse("the schedule has {count:d} pending post"))
def schedule_has_pending(ctx, count):
    pending = [p for p in ctx["scheduler"].data["scheduled_posts"] if p["status"] == "pending"]
    assert len(pending) == count


@then(parsers.parse('the scheduled post platform is "{platform}"'))
def scheduled_post_platform(ctx, platform):
    pending = [p for p in ctx["scheduler"].data["scheduled_posts"] if p["status"] == "pending"]
    assert pending[0]["platform"] == platform


@then(parsers.re(r"(?P<count>\d+) posts? (?:is|are) due"))
def posts_due(ctx, count):
    assert len(ctx["due_posts"]) == int(count)


@then(parsers.parse('the post status is "{status}"'))
def post_status(ctx, status):
    scheduler = ctx["scheduler"]
    scheduler.data = scheduler._load()
    post = next(p for p in scheduler.data["scheduled_posts"] if p["id"] == ctx["last_post_id"])
    assert post["status"] == status


@then(parsers.parse('the stored post URL is "{expected_url}"'))
def stored_post_url(ctx, expected_url):
    scheduler = ctx["scheduler"]
    post = next(p for p in scheduler.data["scheduled_posts"] if p["id"] == ctx["last_post_id"])
    assert post["post_url"] == expected_url
