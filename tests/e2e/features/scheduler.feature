Feature: Schedule and execute social media posts

  Scenario: Schedule a new post
    Given an empty schedule
    When I schedule a post for "sunset_lake" on "mastodon" at "2099-06-01T12:00:00"
    Then the schedule has 1 pending post
    And the scheduled post platform is "mastodon"

  Scenario: Past-due posts are returned when checking for pending work
    Given an empty schedule
    And a post for "morning_mist" on "mastodon" is scheduled at "2020-01-01T10:00:00"
    When I request posts due now
    Then 1 post is due

  Scenario: Future posts are not returned when checking for pending work
    Given an empty schedule
    And a post for "evening_glow" on "mastodon" is scheduled at "2099-01-01T10:00:00"
    When I request posts due now
    Then 0 posts are due

  Scenario: Marking a post as successfully posted
    Given an empty schedule
    And a post for "blue_hills" on "mastodon" is scheduled at "2020-01-01T10:00:00"
    When I mark the post as posted to "https://mastodon.example.com/@user/99"
    Then the post status is "posted"
    And the stored post URL is "https://mastodon.example.com/@user/99"

  Scenario: Cancelling a pending post
    Given an empty schedule
    And a post for "red_valley" on "mastodon" is scheduled at "2099-01-01T10:00:00"
    When I cancel the post
    Then the post status is "cancelled"
