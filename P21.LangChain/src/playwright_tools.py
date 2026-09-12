"""Playwright tools for a LangChain agent (verified against Playwright 1.62).

Design rules every tool here follows, because an LLM is the caller:

1. Return a string, never raise. An agent cannot catch an exception, but it can
   read "Error: no element matches #login" and try a different selector.
2. The docstring IS the tool description the model reads. Say when to use the
   tool, not just what it does.
3. Prefer role/label/text lookups over CSS. The agent guesses CSS badly; it is
   much better at "the button called Sign in".
"""

import json
import os
from functools import wraps

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)
from langchain.tools import tool

# Shared browser state across tools (module-level, like globals in TypeScript)
_playwright = None
_browser: Browser | None = None
_context: BrowserContext | None = None
_page: Page | None = None

# Diagnostics collected by listeners registered in launch_browser().
_console_errors: list[str] = []
_failed_requests: list[str] = []
_responses: list[str] = []
_dialog_log: list[str] = []
_dialog_should_accept = True
_dialog_prompt_text = ""


def _brief(exc: BaseException) -> str:
    """Playwright errors are paragraphs. An agent only needs the first line."""
    return str(exc).strip().splitlines()[0]


def _record_console_message(message) -> None:
    """Keep console errors only - warnings and logs are noise for an agent."""
    if message.type == "error":
        _console_errors.append(message.text)


def _record_failed_request(request) -> None:
    _failed_requests.append(f"{request.method} {request.url} -> {request.failure or 'failed'}")


def _record_response(response) -> None:
    _responses.append(f"{response.status} {response.request.method} {response.url}")
    if len(_responses) > 200:
        del _responses[: len(_responses) - 200]


async def _handle_dialog(dialog) -> None:
    """Auto-handle JS dialogs so they never hang the agent; behavior is tunable
    via set_dialog_behavior, and every dialog is logged for get_dialog_log."""
    _dialog_log.append(f"{dialog.type}: {dialog.message}")
    if _dialog_should_accept:
        await dialog.accept(_dialog_prompt_text or None)
    else:
        await dialog.dismiss()


def _wire_page(page: Page) -> None:
    """Attach the same listeners every page/tab needs, so behavior stays consistent."""
    page.set_default_timeout(15_000)
    page.on("console", _record_console_message)
    page.on("requestfailed", _record_failed_request)
    page.on("response", _record_response)
    page.on("dialog", _handle_dialog)


def _needs_page(fn):
    """Guard + error funnel, so 20 tools do not repeat the same 6 lines.

    Catching broad Exception is deliberate here: a tool that raises kills the
    agent run, while a tool that returns an error string lets the agent adapt.
    """
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        if _page is None:
            return "Error: Browser not launched. Call launch_browser first."
        try:
            return await fn(*args, **kwargs)
        except PlaywrightTimeoutError as exc:
            return f"Timeout: {_brief(exc)}"
        except Exception as exc:
            return f"Error: {_brief(exc)}"
    return wrapper


# --------------------------------------------------------------------------
# Lifecycle
# --------------------------------------------------------------------------

@tool
async def launch_browser(headless: bool = False) -> str:
    """Launch a Chromium browser. Always call this first, before any other tool."""
    global _playwright, _browser, _context, _page
    if _browser:
        return "Browser is already open."
    _console_errors.clear()
    _failed_requests.clear()
    _responses.clear()
    _dialog_log.clear()
    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(headless=headless, slow_mo=700)
    _context = await _browser.new_context()
    _page = await _context.new_page()
    # 30s (the default) is a long time for an agent to sit blocked on a typo.
    _wire_page(_page)
    return f"Browser launched successfully ({'headless' if headless else 'visible'} mode)."


@tool
async def close_browser() -> str:
    """Close the browser and free the session. Call this last."""
    global _playwright, _browser, _context, _page
    if not _browser:
        return "No browser is open."
    await _browser.close()
    await _playwright.stop()
    _playwright = _browser = _context = _page = None
    return "Browser closed successfully."


# --------------------------------------------------------------------------
# Seeing the page - call these before guessing a selector
# --------------------------------------------------------------------------

@tool
@_needs_page
async def snapshot_page(selector: str = "body") -> str:
    """Get the ARIA snapshot: every role, name and value on the page as a YAML tree.

    Call this FIRST whenever you do not already know what is on the page. It is
    the cheapest way to find out what you can click or type into, and the names
    it returns are exactly what click_by_role and type_by_label expect.
    """
    snap = await _page.locator(selector).aria_snapshot()
    return snap[:6000] or "Snapshot is empty."


@tool
@_needs_page
async def get_page_info() -> str:
    """Get the current URL and page title. Use it to confirm navigation worked."""
    return f"URL: {_page.url}\nTitle: {await _page.title()}"


@tool
@_needs_page
async def get_page_text() -> str:
    """Get every visible word on the page, top to bottom, truncated to 8000 characters.

    Use this when snapshot_page's role/name tree is more structure than you need and
    you just want the wording - e.g. to read an error banner or a paragraph of copy.
    """
    text = await _page.locator("body").inner_text()
    return text[:8000] or "Page has no visible text."


# --------------------------------------------------------------------------
# Navigation
# --------------------------------------------------------------------------

@tool
@_needs_page
async def navigate_to(url: str) -> str:
    """Navigate to a full URL, for example https://example.com/login."""
    await _page.goto(url, wait_until="domcontentloaded")
    return f"Navigated to {url}"


@tool
@_needs_page
async def go_back() -> str:
    """Go back one entry in browser history."""
    await _page.go_back(wait_until="domcontentloaded")
    return f"Went back. Now at {_page.url}"


@tool
@_needs_page
async def reload_page() -> str:
    """Reload the current page. Useful after a change that needs a refresh."""
    await _page.reload(wait_until="domcontentloaded")
    return f"Reloaded {_page.url}"


@tool
@_needs_page
async def wait_for_url(url_pattern: str, timeout_ms: int = 10000) -> str:
    """Wait until the page URL matches a pattern, e.g. '**/inventory*' or an exact URL.

    Use this right after an action that triggers navigation (a login click, a redirect)
    instead of guessing how long to wait - it returns as soon as the URL matches.
    """
    await _page.wait_for_url(url_pattern, timeout=timeout_ms)
    return f"URL now matches {url_pattern}: {_page.url}"


@tool
@_needs_page
async def wait_for_element(selector: str, state: str = "visible", timeout_ms: int = 10000) -> str:
    """Wait until an element reaches a state: visible, hidden, attached or detached.

    Use this instead of retrying a failed click. Never sleep; Playwright already
    auto-waits, and this is the explicit version for slow, async pages.
    """
    await _page.locator(selector).wait_for(state=state, timeout=timeout_ms)
    return f"Element {selector} is now {state}."


# --------------------------------------------------------------------------
# Interacting - CSS selector versions
# --------------------------------------------------------------------------

@tool
@_needs_page
async def type_text(selector: str, text: str) -> str:
    """Type text into an input field found by CSS selector."""
    await _page.locator(selector).fill(text)
    return f'Typed "{text}" into {selector}'


@tool
@_needs_page
async def click_element(selector: str) -> str:
    """Click on an element found by CSS selector."""
    await _page.locator(selector).click()
    return f"Clicked on {selector}"


@tool
@_needs_page
async def click_nth_element(selector: str, index: int) -> str:
    """Click the Nth (0-based) element matching a selector.

    Use for repeated rows or list items, where click_element's default "first match"
    would click the wrong one - e.g. the 3rd row of a results table.
    """
    await _page.locator(selector).nth(index).click()
    return f"Clicked element {index} matching {selector}"


@tool
@_needs_page
async def clear_text(selector: str) -> str:
    """Clear an input field's value without typing anything new."""
    await _page.locator(selector).clear()
    return f"Cleared {selector}"


@tool
@_needs_page
async def hover_element(selector: str) -> str:
    """Hover over an element to reveal menus or tooltips that appear on hover."""
    await _page.locator(selector).hover()
    return f"Hovered over {selector}"


@tool
@_needs_page
async def press_key(key: str, selector: str = "") -> str:
    """Press a keyboard key such as Enter, Tab, Escape, ArrowDown or Control+A.

    Leave selector empty to send the key to the page, or pass one to focus an
    element first. Use this to submit a form that has no visible submit button.
    """
    if selector:
        await _page.locator(selector).press(key)
        return f"Pressed {key} on {selector}"
    await _page.keyboard.press(key)
    return f"Pressed {key}"


@tool
@_needs_page
async def select_dropdown_option(selector: str, value: str) -> str:
    """Choose an option in a native <select> dropdown, by visible label or value."""
    try:
        chosen = await _page.locator(selector).select_option(label=value)
    except Exception:
        chosen = await _page.locator(selector).select_option(value)
    return f"Selected {chosen} in {selector}"


@tool
@_needs_page
async def set_checkbox(selector: str, checked: bool = True) -> str:
    """Tick or untick a checkbox or radio button. Safe to call when already correct."""
    locator = _page.locator(selector)
    await (locator.check() if checked else locator.uncheck())
    return f"Set {selector} to checked={checked}"


@tool
@_needs_page
async def upload_file(selector: str, file_path: str) -> str:
    """Upload a local file to an <input type=file>.

    Works on hidden inputs, so do not try to click the file button first - an
    OS file dialog cannot be driven by the browser.
    """
    if not os.path.exists(file_path):
        return f"Error: no such file: {file_path}"
    await _page.locator(selector).set_input_files(file_path)
    return f"Uploaded {os.path.basename(file_path)} to {selector}"


@tool
@_needs_page
async def drag_and_drop(source_selector: str, target_selector: str) -> str:
    """Drag one element onto another, for kanban boards and sortable lists."""
    await _page.drag_and_drop(source_selector, target_selector)
    return f"Dragged {source_selector} onto {target_selector}"


@tool
@_needs_page
async def scroll_to_element(selector: str) -> str:
    """Scroll an element into view. Rarely needed - clicks auto-scroll already."""
    await _page.locator(selector).scroll_into_view_if_needed()
    return f"Scrolled {selector} into view"


# --------------------------------------------------------------------------
# Interacting - resilient locators (prefer these over CSS)
# --------------------------------------------------------------------------

@tool
@_needs_page
async def click_by_role(role: str, name: str) -> str:
    """Click an element by its ARIA role and visible name, e.g. role="button", name="Sign in".

    Prefer this over click_element: it survives CSS and markup changes, and the
    role/name pairs come straight out of snapshot_page.
    """
    await _page.get_by_role(role, name=name).first.click()
    return f'Clicked {role} named "{name}"'


@tool
@_needs_page
async def click_by_text(text: str) -> str:
    """Click the first element containing this visible text. Use for links and cards."""
    await _page.get_by_text(text).first.click()
    return f'Clicked element containing text "{text}"'


@tool
@_needs_page
async def type_by_label(label: str, text: str) -> str:
    """Type into the field with this form label or placeholder, e.g. label="Password".

    Prefer this over type_text - it is how a human finds the field, and it does
    not break when the CSS class changes.
    """
    field = _page.get_by_label(label)
    if await field.count() == 0:
        field = _page.get_by_placeholder(label)
    await field.first.fill(text)
    return f'Typed "{text}" into the field labelled "{label}"'


# --------------------------------------------------------------------------
# Frames - iframes are a separate document; CSS selectors on _page never reach inside
# --------------------------------------------------------------------------

@tool
@_needs_page
async def click_in_frame(frame_selector: str, target_selector: str) -> str:
    """Click an element inside an <iframe>.

    frame_selector locates the iframe itself, e.g. 'iframe[name="payment"]' or
    'iframe[src*="checkout"]'. target_selector locates the element inside that frame.
    Use this instead of click_element whenever the target lives inside an iframe
    (payment widgets, embedded chat, third-party login forms).
    """
    await _page.frame_locator(frame_selector).locator(target_selector).click()
    return f"Clicked {target_selector} inside frame {frame_selector}"


@tool
@_needs_page
async def type_in_frame(frame_selector: str, target_selector: str, text: str) -> str:
    """Type text into a field inside an <iframe>. See click_in_frame for frame_selector."""
    await _page.frame_locator(frame_selector).locator(target_selector).fill(text)
    return f'Typed "{text}" into {target_selector} inside frame {frame_selector}'


# --------------------------------------------------------------------------
# Reading and asserting - this is a QA agent, so let it verify
# --------------------------------------------------------------------------

@tool
@_needs_page
async def get_text(selector: str) -> str:
    """Extract the text content of an element found by CSS selector."""
    text = await _page.locator(selector).text_content()
    return (text or "No text found").strip()


@tool
@_needs_page
async def get_all_texts(selector: str) -> str:
    """Get the text of EVERY element matching the selector, as a numbered list.

    Use for tables, search results and list items, instead of calling get_text
    once per row.
    """
    texts = await _page.locator(selector).all_inner_texts()
    if not texts:
        return f"No elements match {selector}"
    return "\n".join(f"{i}. {t.strip()}" for i, t in enumerate(texts[:50], 1))


@tool
@_needs_page
async def get_attribute_value(selector: str, attribute: str) -> str:
    """Read one HTML attribute, such as href, value, class, disabled or aria-label."""
    value = await _page.locator(selector).first.get_attribute(attribute)
    return f"{attribute}={value!r}" if value is not None else f"{selector} has no {attribute}"


@tool
@_needs_page
async def count_elements(selector: str) -> str:
    """Count how many elements match a selector. Use to assert list lengths."""
    return f"{await _page.locator(selector).count()} element(s) match {selector}"


@tool
@_needs_page
async def assert_visible(selector: str, should_be_visible: bool = True) -> str:
    """Check whether an element is visible. Returns PASS or FAIL, never raises.

    This is the verification step of a test - call it after an action to decide
    whether the scenario actually passed.
    """
    actual = await _page.locator(selector).first.is_visible()
    ok = actual == should_be_visible
    return (f"{'PASS' if ok else 'FAIL'}: {selector} visible={actual}, "
            f"expected visible={should_be_visible}")


@tool
@_needs_page
async def assert_text_contains(selector: str, expected_text: str) -> str:
    """Check an element's text contains the expected substring. Returns PASS or FAIL."""
    actual = ((await _page.locator(selector).first.text_content()) or "").strip()
    ok = expected_text.lower() in actual.lower()
    return (f"{'PASS' if ok else 'FAIL'}: expected {expected_text!r} "
            f"{'found in' if ok else 'NOT found in'} {actual!r}")


# --------------------------------------------------------------------------
# Diagnostics - what a human tester checks that an agent usually forgets
# --------------------------------------------------------------------------

@tool
@_needs_page
async def get_console_errors() -> str:
    """List JavaScript console errors since the browser launched.

    A page can look perfect and still be broken. Check this before declaring a
    scenario passed.
    """
    if not _console_errors:
        return "No console errors."
    return f"{len(_console_errors)} console error(s):\n" + "\n".join(
        f"- {e}" for e in _console_errors[-20:])


@tool
@_needs_page
async def get_failed_requests() -> str:
    """List network requests that failed since launch - broken APIs, images, 4xx/5xx."""
    if not _failed_requests:
        return "No failed network requests."
    return f"{len(_failed_requests)} failed request(s):\n" + "\n".join(
        f"- {r}" for r in _failed_requests[-20:])


@tool
@_needs_page
async def get_recent_responses(url_contains: str = "") -> str:
    """List recent network responses (status, method, URL), newest last.

    Pass url_contains to filter to one endpoint, e.g. url_contains="/api/cart", to confirm
    a specific API call happened and check its status code - including calls that
    "succeeded" at the HTTP level but returned a 4xx/5xx business error.
    """
    matches = [r for r in _responses if url_contains in r] if url_contains else _responses
    if not matches:
        return "No matching responses recorded."
    return "\n".join(matches[-30:])


@tool
@_needs_page
async def get_dialog_log() -> str:
    """List JS dialogs (alert/confirm/prompt/beforeunload) seen since launch and their text.

    Dialogs are auto-handled (accepted by default) so they never hang the agent; use
    set_dialog_behavior beforehand to change that, and check here afterwards for what
    a dialog actually said - a "delete this item?" confirm is easy to miss otherwise.
    """
    if not _dialog_log:
        return "No dialogs appeared."
    return f"{len(_dialog_log)} dialog(s):\n" + "\n".join(f"- {d}" for d in _dialog_log[-20:])


@tool
@_needs_page
async def take_screenshot(filename: str = "screenshot.png") -> str:
    """Take a full page screenshot and save it in the screenshots folder."""
    os.makedirs("screenshots", exist_ok=True)
    path = f"screenshots/{filename}"
    await _page.screenshot(path=path, full_page=True)
    return f"Screenshot saved as {path}"


# --------------------------------------------------------------------------
# Advanced - test conditions you cannot reach by clicking
# --------------------------------------------------------------------------

@tool
@_needs_page
async def set_viewport(width: int = 1280, height: int = 720) -> str:
    """Resize the viewport to test responsive layouts. Try 390x844 for mobile."""
    await _page.set_viewport_size({"width": width, "height": height})
    return f"Viewport set to {width}x{height}"


@tool
@_needs_page
async def evaluate_js(script: str) -> str:
    """Run a JavaScript expression in the page and return its result as a string.

    Example: 'document.title' or 'window.localStorage.getItem("token")'. For reading
    page state Playwright's own API cannot reach - do not use this to bypass UI actions
    that are actually what you are supposed to be testing.
    """
    result = await _page.evaluate(script)
    return str(result)


@tool
@_needs_page
async def download_via_click(selector: str, save_as: str = "") -> str:
    """Click an element that triggers a file download, wait for it, and save it locally.

    Use instead of click_element whenever the click is expected to download a file
    (an "Export CSV" or "Download report" button) rather than navigate.
    """
    async with _page.expect_download() as download_info:
        await _page.locator(selector).click()
    download = await download_info.value
    os.makedirs("downloads", exist_ok=True)
    path = save_as or f"downloads/{download.suggested_filename}"
    await download.save_as(path)
    return f"Downloaded {download.suggested_filename} to {path}"


@tool
@_needs_page
async def save_page_as_pdf(filename: str = "page.pdf") -> str:
    """Save the current page as a PDF.

    Needs a headless Chromium browser (launch_browser(headless=True)) - Playwright can
    only print to PDF in headless mode, so this fails if the browser was launched visible.
    """
    os.makedirs("pdfs", exist_ok=True)
    path = f"pdfs/{filename}"
    await _page.pdf(path=path)
    return f"Saved PDF to {path}"


@tool
@_needs_page
async def api_request(method: str, url: str, json_body: str = "") -> str:
    """Call a REST API endpoint directly (GET/POST/PUT/PATCH/DELETE), reusing the
    browser's cookies and auth headers.

    Use for hybrid UI+API testing - e.g. confirming what the backend actually returned
    after a UI action, or seeding/cleaning up data, without navigating the browser away
    from the page under test. json_body is a JSON string, sent as the request body.
    """
    kwargs = {}
    if json_body:
        kwargs["data"] = json_body
        kwargs["headers"] = {"Content-Type": "application/json"}
    response = await _page.request.fetch(url, method=method.upper(), **kwargs)
    body = (await response.text())[:2000]
    return f"{response.status} {method.upper()} {url}\n{body}"


@tool
@_needs_page
async def set_fixed_time(iso_datetime: str) -> str:
    """Freeze the page's clock at a fixed date/time, e.g. '2026-01-01T00:00:00'.

    Use to deterministically test date-dependent UI - countdowns, "new" badges, expiry
    banners, subscription-renewal warnings - instead of waiting for real time to pass.
    """
    await _page.clock.set_fixed_time(iso_datetime)
    return f"Clock fixed at {iso_datetime}"


@tool
@_needs_page
async def fast_forward_time(ms: int) -> str:
    """Advance the page's mocked clock by N milliseconds, firing any timers/intervals
    that fall in between. Call set_fixed_time first to enable clock mocking."""
    await _page.clock.fast_forward(ms)
    return f"Fast-forwarded clock by {ms}ms"


@tool
@_needs_page
async def mock_api_response(url_pattern: str, status: int = 500, body: str = "{}") -> str:
    """Force an API call to return a fake status and body, e.g. url_pattern="**/api/cart".

    This is how you test error states that you cannot trigger by clicking: a 500
    from the backend, an empty list, a timeout banner.
    """
    async def handler(route):
        await route.fulfill(status=status, content_type="application/json", body=body)
    await _page.route(url_pattern, handler)
    return f"Requests matching {url_pattern} will now return HTTP {status}"


@tool
@_needs_page
async def save_login_state(path: str = "auth_state.json") -> str:
    """Save cookies and localStorage to a file so a later run can skip logging in."""
    state = await _context.storage_state()
    with open(path, "w") as fh:
        json.dump(state, fh)
    return f"Saved {len(state.get('cookies', []))} cookie(s) to {path}"


@tool
@_needs_page
async def load_login_state(path: str = "auth_state.json") -> str:
    """Restore cookies/localStorage saved by save_login_state, skipping a fresh login.

    This replaces the current browser context to apply the saved state: any other open
    tabs are discarded and a single fresh tab is opened in the restored session.
    """
    global _context, _page
    if not os.path.exists(path):
        return f"Error: no such file: {path}"
    await _context.close()
    _context = await _browser.new_context(storage_state=path)
    _page = await _context.new_page()
    _wire_page(_page)
    return f"Restored session from {path}."


@tool
async def set_dialog_behavior(accept: bool = True, prompt_text: str = "") -> str:
    """Configure how future JS dialogs (alert/confirm/prompt/beforeunload) are handled.

    By default every dialog is accepted so it never blocks the agent. Call this with
    accept=False to make the next dialogs get dismissed instead (e.g. to test a "Cancel"
    path), or pass prompt_text for what to type into a window.prompt() dialog.
    """
    global _dialog_should_accept, _dialog_prompt_text
    _dialog_should_accept = accept
    _dialog_prompt_text = prompt_text
    mode = "accepted" if accept else "dismissed"
    return f"Dialogs will now be {mode}" + (f" with text '{prompt_text}'" if accept and prompt_text else "")


# --------------------------------------------------------------------------
# Tabs - a BrowserContext can hold several pages; _page always points at the active one
# --------------------------------------------------------------------------

@tool
@_needs_page
async def open_new_tab(url: str = "") -> str:
    """Open a new browser tab and switch to it, optionally navigating to a URL.

    Use list_tabs to see indices and switch_tab to go back to a previous one - handy
    for flows that open a link in a new tab (payment providers, OAuth popups, "preview").
    """
    global _page
    new_page = await _context.new_page()
    if url:
        await new_page.goto(url, wait_until="domcontentloaded")
    _wire_page(new_page)
    _page = new_page
    return f"Opened new tab (index {len(_context.pages) - 1}), now active."


@tool
@_needs_page
async def list_tabs() -> str:
    """List every open tab with its index, title and URL. The active tab is marked."""
    lines = []
    for i, p in enumerate(_context.pages):
        marker = " (active)" if p == _page else ""
        lines.append(f"{i}: {await p.title()} - {p.url}{marker}")
    return "\n".join(lines)


@tool
@_needs_page
async def switch_tab(index: int) -> str:
    """Switch the active tab by index, as shown by list_tabs. All later tool calls
    (click, type, snapshot...) act on this tab until you switch again."""
    global _page
    pages = _context.pages
    if not 0 <= index < len(pages):
        return f"Error: no tab at index {index}. {len(pages)} tab(s) open."
    _page = pages[index]
    return f"Switched to tab {index}: {_page.url}"


@tool
@_needs_page
async def close_tab(index: int) -> str:
    """Close a tab by index. If you close the active tab, switches to tab 0."""
    global _page
    pages = _context.pages
    if not 0 <= index < len(pages):
        return f"Error: no tab at index {index}. {len(pages)} tab(s) open."
    if len(pages) == 1:
        return "Error: cannot close the only open tab. Use close_browser instead."
    was_active = pages[index] == _page
    await pages[index].close()
    if was_active:
        _page = _context.pages[0]
    return f"Closed tab {index}." + (f" Active tab is now {_page.url}" if was_active else "")


# --------------------------------------------------------------------------
# Cookies
# --------------------------------------------------------------------------

@tool
@_needs_page
async def get_cookies() -> str:
    """List cookies for the current browser context: name, value, domain."""
    cookies = await _context.cookies()
    if not cookies:
        return "No cookies set."
    return "\n".join(f"{c['name']}={c['value']} (domain={c['domain']})" for c in cookies[:50])


@tool
@_needs_page
async def set_cookie(name: str, value: str, url: str = "") -> str:
    """Set a cookie. Pass url (e.g. https://example.com) to scope it correctly, or leave
    it empty to use the current page's URL."""
    target_url = url or _page.url
    await _context.add_cookies([{"name": name, "value": value, "url": target_url}])
    return f"Set cookie {name}={value} for {target_url}"


@tool
@_needs_page
async def clear_cookies() -> str:
    """Delete all cookies in the current browser context."""
    await _context.clear_cookies()
    return "Cleared all cookies."


# --------------------------------------------------------------------------
# Bundles - give an agent the smallest set that can do its job
# --------------------------------------------------------------------------

CORE_TOOLS = [
    launch_browser, close_browser, snapshot_page, get_page_info,
    navigate_to, click_by_role, click_by_text, type_by_label,
    click_element, type_text, get_text, take_screenshot,
]

INTERACTION_TOOLS = [
    hover_element, press_key, select_dropdown_option, set_checkbox,
    upload_file, drag_and_drop, scroll_to_element, wait_for_element,
    wait_for_url, go_back, reload_page, click_nth_element, clear_text,
    get_page_text,
]

ASSERTION_TOOLS = [
    assert_visible, assert_text_contains, count_elements,
    get_all_texts, get_attribute_value,
]

DIAGNOSTIC_TOOLS = [
    get_console_errors, get_failed_requests, get_recent_responses, get_dialog_log,
]

FRAME_TOOLS = [click_in_frame, type_in_frame]

TAB_TOOLS = [open_new_tab, list_tabs, switch_tab, close_tab]

COOKIE_TOOLS = [get_cookies, set_cookie, clear_cookies]

ADVANCED_TOOLS = [
    set_viewport, mock_api_response, save_login_state, load_login_state,
    set_dialog_behavior, evaluate_js, download_via_click, save_page_as_pdf,
    api_request, set_fixed_time, fast_forward_time,
]

PLAYWRIGHT_TOOLS = (
    CORE_TOOLS + INTERACTION_TOOLS + ASSERTION_TOOLS
    + DIAGNOSTIC_TOOLS + FRAME_TOOLS + TAB_TOOLS + COOKIE_TOOLS + ADVANCED_TOOLS
)
