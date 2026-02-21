Feature: Post artwork to Flickr

  Background:
    Given a painting JPEG image file exists for Flickr

  Scenario: Successfully upload a photo to Flickr
    Given Flickr is configured with valid API credentials
    And the Flickr upload API returns photo ID "98765"
    And the Flickr login API returns user NSID "12345678@N01"
    When I post the image to Flickr with title "Autumn Landscape" and description "Oil on canvas, 50x60cm"
    Then the Flickr post result is successful
    And the returned Flickr URL contains "flickr.com/photos/12345678@N01/98765"

  Scenario: Upload fails when Flickr is not configured
    Given Flickr has no credentials configured
    When I post the image to Flickr with title "Test" and description "Test"
    Then the Flickr post result is a failure
    And the Flickr error message contains "not configured"

  Scenario: Upload fails when Flickr API returns an error
    Given Flickr is configured with valid API credentials
    And the Flickr upload API returns an error "Invalid API Key"
    When I post the image to Flickr with title "Test" and description "Test"
    Then the Flickr post result is a failure
    And the Flickr error message contains "Invalid API Key"

  Scenario: Title defaults to filename when alt_text is empty
    Given Flickr is configured with valid API credentials
    And the Flickr upload API returns photo ID "11111"
    And the Flickr login API returns user NSID "99999@N00"
    When I post the image to Flickr with no title and description "A fine painting"
    Then the Flickr post result is successful

  Scenario: Verify credentials returns True for valid credentials
    Given Flickr is configured with valid API credentials
    And the Flickr login API returns user NSID "12345678@N01"
    When I verify Flickr credentials
    Then Flickr credential verification returns True
    And the Flickr user NSID is cached as "12345678@N01"

  Scenario: Verify credentials returns False when not configured
    Given Flickr has no credentials configured
    When I verify Flickr credentials
    Then Flickr credential verification returns False
