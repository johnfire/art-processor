Feature: Post artwork to social media platforms

  Background:
    Given a painting JPEG image file exists

  Scenario: Successfully post to Mastodon
    Given Mastodon is configured with a valid instance URL and token
    And the Mastodon media upload returns media ID "media_123"
    And the Mastodon status API returns post URL "https://mastodon.example.com/@user/123"
    When I post the image to Mastodon with caption "New painting #art"
    Then the post result is successful
    And the returned post URL is "https://mastodon.example.com/@user/123"

  Scenario: Posting fails when Mastodon is not configured
    Given Mastodon has no credentials configured
    When I post the image to Mastodon with caption "New painting #art"
    Then the post result is a failure
    And the error message contains "not configured"

  Scenario: Posting fails when media upload returns no media ID
    Given Mastodon is configured with a valid instance URL and token
    And the Mastodon media upload returns a response with no media ID
    When I post the image to Mastodon with caption "New painting #art"
    Then the post result is a failure
