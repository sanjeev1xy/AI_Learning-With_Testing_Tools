"""Local RAG over a small fixture corpus of existing TTACart test cases.

No embedding API, no vector DB - this project has neither configured, so
retrieval is plain keyword overlap over a fixture corpus of test cases a QA
team might already have on file for the target app. Good enough to show the
planner stage real grounding (duplicates / extends / new) without adding an
external dependency.
"""

import re

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


# A small existing library for the TTACart app (login, cart, checkout).
_CORPUS = [
    {
        "id": "TTA-001",
        "type": "functional",
        "title": "Successful login with valid standard_user credentials",
        "last_result": "PASS",
        "status": "active",
        "tags": ["login", "auth", "smoke"],
        "text": "login standard_user tta_secret redirected inventory products page valid credentials",
    },
    {
        "id": "TTA-002",
        "type": "functional",
        "title": "Login rejected for locked_out_user with error banner",
        "last_result": "PASS",
        "status": "active",
        "tags": ["login", "auth", "negative"],
        "text": "login locked_out_user error banner sorry this user has been locked out",
    },
    {
        "id": "TTA-003",
        "type": "functional",
        "title": "Login fails with wrong password shows inline error",
        "last_result": "PASS",
        "status": "active",
        "tags": ["login", "auth", "negative", "validation"],
        "text": "login wrong incorrect password inline error message username and password do not match",
    },
    {
        "id": "TTA-004",
        "type": "functional",
        "title": "Empty username blocks login submission",
        "last_result": "PASS",
        "status": "active",
        "tags": ["login", "validation"],
        "text": "empty username field required error blocks submit login form",
    },
    {
        "id": "TTA-005",
        "type": "functional",
        "title": "Empty password blocks login submission",
        "last_result": "PASS",
        "status": "active",
        "tags": ["login", "validation"],
        "text": "empty password field required error blocks submit login form",
    },
    {
        "id": "TTA-006",
        "type": "functional",
        "title": "Add single item to cart updates cart badge count",
        "last_result": "PASS",
        "status": "active",
        "tags": ["cart", "smoke"],
        "text": "add to cart button badge count increments shopping cart icon header",
    },
    {
        "id": "TTA-007",
        "type": "functional",
        "title": "Remove item from cart clears badge and cart list",
        "last_result": "PASS",
        "status": "active",
        "tags": ["cart"],
        "text": "remove button cart badge disappears cart list empty",
    },
    {
        "id": "TTA-008",
        "type": "functional",
        "title": "Checkout requires first name, last name and zip code",
        "last_result": "FAIL",
        "status": "flaky",
        "tags": ["checkout", "validation"],
        "text": "checkout step one first name last name zip postal code required error",
    },
    {
        "id": "TTA-009",
        "type": "functional",
        "title": "Checkout overview totals equal item total plus tax",
        "last_result": "PASS",
        "status": "active",
        "tags": ["checkout", "pricing"],
        "text": "checkout overview item total tax total price maths finish button",
    },
    {
        "id": "TTA-010",
        "type": "functional",
        "title": "Order confirmation shows thank you message after Finish",
        "last_result": "PASS",
        "status": "active",
        "tags": ["checkout", "smoke"],
        "text": "checkout complete thank you for your order confirmation page finish",
    },
    {
        "id": "TTA-011",
        "type": "ui",
        "title": "Products page can be sorted by name and price",
        "last_result": "PASS",
        "status": "active",
        "tags": ["products", "sort"],
        "text": "products inventory sort name a to z z to a price low high combobox",
    },
    {
        "id": "TTA-012",
        "type": "functional",
        "title": "Logout returns user to the login page",
        "last_result": "PASS",
        "status": "active",
        "tags": ["auth", "logout"],
        "text": "logout link menu returns login page session ended",
    },
]


class TestCaseRAG:
    """Keyword-overlap retrieval over the fixture corpus above."""

    def __init__(self) -> None:
        self.cases = _CORPUS
        self.backend = "keyword-overlap (offline fixture corpus, no embedding API)"
        self._doc_tokens = [_tokens(f"{c['title']} {c['text']} {' '.join(c['tags'])}") for c in self.cases]

    def search(self, query: str, k: int = 5) -> list[tuple[float, dict]]:
        """Return the top-k (score, case) pairs most similar to query.

        Score is Jaccard overlap between query tokens and each case's token
        set - 0 when nothing overlaps, 1 when every query token is covered.
        """
        q_tokens = _tokens(query)
        if not q_tokens:
            return []
        scored = []
        for doc_tokens, case in zip(self._doc_tokens, self.cases):
            union = q_tokens | doc_tokens
            if not union:
                continue
            score = len(q_tokens & doc_tokens) / len(union)
            scored.append((score, case))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [pair for pair in scored if pair[0] > 0][:k]


def format_for_prompt(hits: list[tuple[float, dict]]) -> str:
    """Render retrieved cases as plain text for the planner's prompt context."""
    if not hits:
        return "No similar existing test cases were found in the library."
    lines = []
    for score, c in hits:
        lines.append(
            f"- {c['id']} [{c['type']}] {c['title']} "
            f"(similarity {score:.2f}, last run {c['last_result']}, status {c['status']}, "
            f"tags: {', '.join(c['tags'])})"
        )
    return "\n".join(lines)
