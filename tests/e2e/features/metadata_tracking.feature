Feature: Track social media posting history in painting metadata

  Scenario: A new painting has zero posts recorded
    Given a painting metadata file with no social media history
    Then the mastodon post count is 0
    And the mastodon last_posted date is absent

  Scenario: Tracking is updated after a successful post
    Given a painting metadata file with no social media history
    When a successful mastodon post is recorded with URL "https://mastodon.example.com/@user/1"
    Then the mastodon post count is 1
    And the mastodon post_url is "https://mastodon.example.com/@user/1"
    And the mastodon last_posted date is present

  Scenario: Post count accumulates across multiple posts
    Given a painting metadata file with mastodon post_count of 2
    When a successful mastodon post is recorded with URL "https://mastodon.example.com/@user/3"
    Then the mastodon post count is 3
