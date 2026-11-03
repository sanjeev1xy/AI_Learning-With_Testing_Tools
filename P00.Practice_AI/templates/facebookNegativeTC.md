# Facebook Login Negative Test Cases

- **Application:** Facebook
- **URL:** https://www.facebook.com/
- **Feature under test:** Login form
- **Precondition:** Use an authorized test account and test data only.

| Test ID | Invalid Scenario | Input | Expected Error |
|---|---|---|---|
| FB-NEG-001 | Submit with both login fields empty | Email/phone: empty; Password: empty | Login is rejected. Required-field validation is displayed, and the user remains unauthenticated. |
| FB-NEG-002 | Submit without an email address or phone number | Email/phone: empty; Password: any test value | Login is rejected and the missing login identifier is indicated. |
| FB-NEG-003 | Submit without a password | Email/phone: authorized test account; Password: empty | Login is rejected and the missing password is indicated. |
| FB-NEG-004 | Submit a malformed email address | Email/phone: `not-an-email`; Password: any test value | Invalid input is rejected or sign-in fails; the user remains unauthenticated. |
| FB-NEG-005 | Submit an incorrect password for an authorized test account | Email/phone: authorized test account; Password: incorrect test password | Login is rejected with an authentication error; the user remains unauthenticated. |
| FB-NEG-006 | Submit login details for an unregistered test identifier | Email/phone: unregistered test identifier; Password: any test value | Login is rejected with a sign-in error; the user remains unauthenticated. |
| FB-NEG-007 | Submit whitespace-only values | Email/phone: spaces only; Password: spaces only | Values are treated as empty or invalid, and login is rejected. |

**Note:** Exact validation and error wording may change. Confirm expected messages against current Facebook behavior and applicable test requirements.
