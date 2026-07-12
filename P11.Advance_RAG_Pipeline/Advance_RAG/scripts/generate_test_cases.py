"""One-off generator for testcase/test_cases.csv — 5000 synthetic JIRA-format QA test cases."""
import csv
import random
from pathlib import Path

random.seed(42)

MODULES = [
    "Authentication", "Booking CRUD", "Search & Filters", "Payment & Checkout",
    "Notifications", "User Profile", "Admin Dashboard", "API Integration",
    "Performance", "Security", "Mobile App", "Accessibility", "Localization",
    "Reporting & Analytics", "File Upload", "Session Management", "Rate Limiting",
    "Data Validation", "Third-Party Integration", "Regression Suite",
]

PRIORITIES = ["Blocker", "Critical", "High", "Medium", "Low"]
PRIORITY_WEIGHTS = [3, 10, 30, 42, 15]

ACTIONS = {
    "Authentication": [
        "log in with valid username and password",
        "log in with an expired session token",
        "log in with SQL injection payload in the password field",
        "reset password using a valid email link",
        "reset password using an expired reset link",
        "log in with a locked-out account after 5 failed attempts",
        "log out and verify the session token is invalidated",
        "refresh an access token using a valid refresh token",
        "access a protected endpoint without an auth header",
        "log in via SSO with an expired identity provider certificate",
    ],
    "Booking CRUD": [
        "create a new booking with valid guest details",
        "create a booking with a check-out date earlier than check-in",
        "update an existing booking's room type",
        "delete a booking using a valid booking ID",
        "delete a booking using a non-existent booking ID",
        "fetch a booking by ID and verify all fields",
        "create a booking with missing required fields",
        "create 100 concurrent bookings for the same room",
        "update a booking's authentication token mid-transaction",
        "cancel a booking within the free-cancellation window",
    ],
    "Search & Filters": [
        "search test cases by keyword in the title",
        "filter results by priority and module simultaneously",
        "search with an empty query string",
        "search with special characters in the query",
        "paginate through 500+ results at 50 per page",
        "sort search results by relevance score",
        "apply a date-range filter to search results",
        "search using a misspelled keyword and verify fuzzy match",
        "clear all filters and verify the full result set returns",
        "search across multiple modules at once",
    ],
    "Payment & Checkout": [
        "complete checkout with a valid credit card",
        "complete checkout with an expired credit card",
        "apply a valid discount coupon at checkout",
        "apply an expired discount coupon at checkout",
        "process a refund for a cancelled order",
        "attempt checkout with insufficient funds",
        "verify tax calculation for an international order",
        "verify currency conversion for a multi-currency cart",
        "retry a failed payment gateway timeout",
        "verify PCI-compliant masking of card numbers in logs",
    ],
    "Notifications": [
        "send a booking confirmation email after successful checkout",
        "send an SMS reminder 24 hours before check-in",
        "verify push notification delivery on booking cancellation",
        "verify notification preferences are respected (opt-out)",
        "send a password-reset email and verify link expiry",
        "verify email template renders correctly in dark mode clients",
        "verify notification retry logic on delivery failure",
        "verify batched digest notifications are deduplicated",
        "verify notification is localized to the user's language",
        "verify webhook fires on order-status change",
    ],
    "User Profile": [
        "update profile name and verify persistence",
        "upload a profile photo larger than the 5MB limit",
        "change email address and verify re-verification flow",
        "delete a user account and verify data purge",
        "view another user's profile without permission",
        "update profile with an invalid phone number format",
        "verify profile changes are audit-logged",
        "merge two duplicate user accounts",
        "verify GDPR data-export request returns complete profile",
        "verify profile picture CDN fallback on upload failure",
    ],
    "Admin Dashboard": [
        "verify admin can view all bookings across regions",
        "verify a non-admin user cannot access the admin dashboard",
        "export dashboard metrics to CSV",
        "verify real-time booking count updates on the dashboard",
        "revoke a user's admin privileges",
        "verify audit log entries for all admin actions",
        "bulk-approve pending refund requests",
        "verify dashboard graceful degradation when analytics service is down",
        "filter dashboard data by date range and region",
        "verify role-based access control for dashboard widgets",
    ],
    "API Integration": [
        "verify POST /booking returns 201 with a valid payload",
        "verify GET /booking/{id} returns 404 for a missing booking",
        "verify PUT /booking/{id} rejects a malformed JSON body",
        "verify DELETE /booking/{id} requires authentication",
        "verify API rate-limit headers are present on every response",
        "verify API versioning header routes to the correct handler",
        "verify webhook signature validation rejects tampered payloads",
        "verify pagination cursor tokens are stable across requests",
        "verify OpenAPI spec matches actual response schema",
        "verify idempotency key prevents duplicate booking creation",
    ],
    "Performance": [
        "measure response time for the search endpoint under 100 RPS",
        "measure p95 latency for checkout under peak load",
        "verify database connection pool does not exhaust under load",
        "verify CDN cache hit ratio for static assets exceeds 90%",
        "load test booking creation with 1000 concurrent users",
        "verify memory usage stays under 500MB during a 1-hour soak test",
        "verify autoscaling triggers correctly under sustained CPU load",
        "measure cold-start latency for the search Lambda",
        "verify query plan uses an index for the bookings-by-date lookup",
        "stress test the notification queue with 10k messages/minute",
    ],
    "Security": [
        "verify XSS payload in a comment field is sanitized",
        "verify SQL injection attempt is blocked and logged",
        "verify JWT signature is validated on every protected request",
        "verify sensitive fields are excluded from API responses",
        "verify CSRF token is required for state-changing requests",
        "verify rate limiting blocks brute-force login attempts",
        "verify TLS certificate is valid and not expired",
        "verify file upload rejects executable file types",
        "verify password hashes use a modern algorithm (bcrypt/argon2)",
        "verify security headers (CSP, HSTS) are present on all responses",
    ],
    "Mobile App": [
        "verify booking flow works offline and syncs on reconnect",
        "verify push notification deep-links to the correct screen",
        "verify app handles low-memory warnings without crashing",
        "verify biometric login works on supported devices",
        "verify app respects system dark mode setting",
        "verify camera permission prompt appears before photo upload",
        "verify app state is preserved across a backgrounding event",
        "verify deep link opens the app to the correct booking",
        "verify app gracefully handles a lost network mid-checkout",
        "verify accessibility voice-over reads all interactive elements",
    ],
    "Accessibility": [
        "verify all interactive elements are keyboard-navigable",
        "verify color contrast meets WCAG AA on the checkout page",
        "verify screen reader announces form validation errors",
        "verify focus order follows a logical reading sequence",
        "verify all images have descriptive alt text",
        "verify form inputs have associated labels",
        "verify skip-to-content link is present and functional",
        "verify modal dialogs trap focus correctly",
        "verify text can be resized to 200% without loss of content",
        "verify video content has closed captions available",
    ],
    "Localization": [
        "verify UI strings render correctly in German with longer text",
        "verify date format switches correctly for the selected locale",
        "verify currency symbol matches the selected region",
        "verify right-to-left layout renders correctly in Arabic",
        "verify translated error messages match the source meaning",
        "verify number formatting follows locale conventions (decimal/comma)",
        "verify timezone conversion for booking confirmation emails",
        "verify fallback to English when a translation key is missing",
        "verify locale switcher persists across sessions",
        "verify pluralization rules are correct in Russian",
    ],
    "Reporting & Analytics": [
        "verify daily booking report matches raw database counts",
        "verify funnel conversion metrics update within 5 minutes",
        "verify exported report CSV has no encoding issues",
        "verify scheduled report email is sent at the configured time",
        "verify dashboard chart data matches the underlying query",
        "verify report filters by custom date range correctly",
        "verify anomaly detection flags a sudden booking drop",
        "verify report generation does not block the main API thread",
        "verify cohort retention report groups users correctly",
        "verify report access is restricted to authorized roles",
    ],
    "File Upload": [
        "upload a valid PDF document under the size limit",
        "upload a file exceeding the 10MB size limit",
        "upload a file with an unsupported extension",
        "upload a file with a malicious double extension (.pdf.exe)",
        "verify uploaded file virus scan completes before storage",
        "verify upload progress bar reflects actual transfer percentage",
        "resume an interrupted large file upload",
        "verify uploaded file is stored with a sanitized filename",
        "verify concurrent uploads to the same folder don't collide",
        "verify upload retries automatically on network blip",
    ],
    "Session Management": [
        "verify session expires after 30 minutes of inactivity",
        "verify concurrent sessions on two devices are both valid",
        "verify session is invalidated on password change",
        "verify remember-me extends session lifetime correctly",
        "verify session fixation attack is prevented on login",
        "verify session cookie has Secure and HttpOnly flags",
        "verify logout clears session on all open tabs",
        "verify session data is not leaked across user accounts",
        "verify idle timeout warning appears before forced logout",
        "verify session token rotates after privilege escalation",
    ],
    "Rate Limiting": [
        "verify API returns 429 after exceeding the rate limit",
        "verify rate limit resets after the configured window",
        "verify rate limit is applied per API key, not globally",
        "verify rate limit headers report remaining quota accurately",
        "verify burst traffic within limits is not throttled",
        "verify rate limit bypass is blocked for spoofed headers",
        "verify admin users have a higher rate limit tier",
        "verify rate-limited requests are logged for monitoring",
        "verify retry-after header value is honored by the client",
        "verify distributed rate limiting is consistent across nodes",
    ],
    "Data Validation": [
        "verify email field rejects malformed addresses",
        "verify phone number field enforces E.164 format",
        "verify date field rejects invalid calendar dates",
        "verify required fields block form submission when empty",
        "verify numeric fields reject non-numeric input",
        "verify max-length constraints are enforced server-side",
        "verify whitespace-only input is treated as empty",
        "verify Unicode input is stored and retrieved without corruption",
        "verify duplicate submission is prevented via idempotency check",
        "verify server-side validation matches client-side validation rules",
    ],
    "Third-Party Integration": [
        "verify Stripe webhook updates order status correctly",
        "verify Google Maps API renders the correct pin location",
        "verify Twilio SMS delivery status is tracked",
        "verify Salesforce sync does not duplicate contact records",
        "verify fallback behavior when the payment gateway is down",
        "verify OAuth login via Google returns the correct profile scope",
        "verify Zendesk ticket is created on support form submission",
        "verify analytics events fire correctly to Segment",
        "verify third-party API timeout triggers a graceful fallback",
        "verify webhook retries follow exponential backoff on failure",
    ],
    "Regression Suite": [
        "verify booking creation still works after the auth service upgrade",
        "verify checkout total calculation after the tax engine migration",
        "verify search results after the Elasticsearch version bump",
        "verify email templates after the notification service refactor",
        "verify dashboard metrics after the analytics pipeline rewrite",
        "verify login flow after the SSO provider migration",
        "verify API responses after the schema versioning change",
        "verify file upload after the storage backend migration",
        "verify rate limiting after the API gateway replacement",
        "verify mobile deep links after the routing library upgrade",
    ],
}

EXPECTED_TEMPLATES = [
    "The system should complete the action successfully and return a confirmation.",
    "The system should reject the request with a clear, actionable error message.",
    "The system should return the correct HTTP status code and response payload.",
    "The system should log the event and notify the relevant stakeholders.",
    "The system should preserve data integrity and not leave partial state.",
    "The system should respond within the defined SLA and not degrade other requests.",
    "The system should block the unauthorized action and record an audit entry.",
    "The system should display a user-friendly message without leaking internals.",
    "The system should recover gracefully and retry according to policy.",
    "The system should match the documented API contract exactly.",
]

TAGS_POOL = [
    "smoke", "regression", "api", "ui", "security", "performance", "mobile",
    "accessibility", "critical-path", "edge-case", "negative", "positive",
    "automation-candidate", "manual-only", "flaky-history", "data-driven",
]

STEP_TEMPLATES = [
    "1. Navigate to the {module} section.\n2. {action_cap}.\n3. Observe the system response.\n4. Verify the result against the expected outcome.",
    "1. Set up test data required to {action}.\n2. Trigger the action via the UI or API.\n3. Capture the response/logs.\n4. Assert the outcome matches expectations.",
    "1. Log in as a user with the required role.\n2. Attempt to {action}.\n3. Record any errors or warnings shown.\n4. Confirm the final state is correct.",
    "1. Prepare the environment (mock/stub external dependencies as needed).\n2. Execute the step to {action}.\n3. Validate response time and payload.\n4. Clean up test data.",
]


def make_row(idx):
    module = random.choice(MODULES)
    action = random.choice(ACTIONS[module])
    action_cap = action[0].upper() + action[1:]
    priority = random.choices(PRIORITIES, weights=PRIORITY_WEIGHTS, k=1)[0]
    jira_id = f"VWO-{1000 + idx}"
    case_id = f"TC-{idx:05d}"
    title = f"Verify that a user can {action}"
    steps = random.choice(STEP_TEMPLATES).format(module=module, action=action, action_cap=action_cap)
    expected = random.choice(EXPECTED_TEMPLATES)
    tags = ";".join(sorted(random.sample(TAGS_POOL, k=random.randint(2, 4))))
    return {
        "id": case_id,
        "jira_id": jira_id,
        "priority": priority,
        "module": module,
        "title": title,
        "steps": steps,
        "expected": expected,
        "tags": tags,
    }


def main():
    out_path = Path(__file__).resolve().parent.parent / "testcase" / "test_cases.csv"
    fieldnames = ["id", "jira_id", "priority", "module", "title", "steps", "expected", "tags"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(1, 5001):
            writer.writerow(make_row(i))
    print(f"wrote 5000 rows to {out_path}")


if __name__ == "__main__":
    main()
