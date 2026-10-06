"""Browser end-to-end tests of the web front end (system-level validation)."""
import re
import uuid

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

USER = ("user@scms.example.com", "User@1234")
STAFF = ("staff1@scms.example.com", "Staff@1234")
ADMIN = ("admin@scms.example.com", "Admin@1234")


def login(page: Page, creds):
    page.goto("/#/login")
    page.fill("#email", creds[0])
    page.fill("#password", creds[1])
    page.click("button[type=submit]")
    expect(page.locator(".sidebar")).to_be_visible()


def logout(page: Page):
    page.click("button[aria-label='Sign out']")
    expect(page.locator("#email")).to_be_visible()


def submit_complaint(page: Page, description: str, priority="HIGH") -> str:
    page.goto("/#/complaints/new")
    page.select_option("#category", label="IT & Network")
    page.click(f"label[for=prio-{priority}]")
    page.fill("#description", description)
    page.click("button:has-text('Submit complaint')")
    expect(page.locator(".page-head .ref")).to_be_visible()
    return page.url.split("/")[-1]


@pytest.mark.req("FR-02", "FR-04")
def test_login_validation_and_bad_credentials(page: Page):
    page.goto("/")
    page.click("button[type=submit]")
    expect(page.locator("#email-error")).to_have_text("Email is required")
    page.fill("#email", "user@scms.example.com")
    page.fill("#password", "wrong-password1")
    page.click("button[type=submit]")
    expect(page.locator("[role=alert]")).to_have_text("Invalid email or password")
    expect(page.locator("#password")).to_have_value("")


@pytest.mark.req("FR-01", "FR-02")
def test_register_then_land_on_my_complaints(page: Page):
    page.goto("/#/register")
    page.fill("#name", "Kiran Test")
    page.fill("#email", "bad-email")
    page.fill("#password", "short")
    page.fill("#confirm", "other")
    page.click("button[type=submit]")
    expect(page.locator("#email-error")).to_contain_text("valid email")
    expect(page.locator("#password-error")).to_contain_text("at least 8")
    expect(page.locator("#confirm-error")).to_have_text("Passwords do not match")
    email = f"kiran-{uuid.uuid4().hex[:6]}@scms.example.com"
    page.fill("#email", email)
    page.fill("#password", "Kiran1234")
    page.fill("#confirm", "Kiran1234")
    page.click("button[type=submit]")
    expect(page.locator("h1")).to_have_text("My complaints")
    expect(page.locator(".sidebar .me")).to_contain_text("Kiran Test")


@pytest.mark.req("FR-05", "FR-07", "FR-08", "FR-12", "FR-13", "FR-14", "FR-15", "FR-20")
def test_complaint_journey_across_roles(page: Page):
    text = f"Projector in seminar hall {uuid.uuid4().hex[:5]} shows no signal."
    # 1. user submits (client-side validation first)
    login(page, USER)
    page.goto("/#/complaints/new")
    page.click("button:has-text('Submit complaint')")
    expect(page.locator("#category-error")).to_have_text("Category is required")
    expect(page.locator("#description-error")).to_have_text("Description is required")
    cid = submit_complaint(page, text)
    expect(page.locator(".page-head [data-status]")).to_have_text("Submitted")
    logout(page)

    # 2. admin assigns to Ravi Staff
    login(page, ADMIN)
    page.goto(f"/#/complaints/{cid}")
    page.click(".actions >> text=Assign")
    page.select_option("#staff", label="Ravi Staff")
    page.click(".modal button[type=submit]")
    expect(page.locator(".page-head [data-status]")).to_have_text("Assigned")
    logout(page)

    # 3. staff starts work and resolves (resolution required)
    login(page, STAFF)
    expect(page.locator("[data-testid=unread-count]")).to_be_visible()
    page.goto("/#/complaints?scope=assigned")
    page.click(f"tr[data-id='{cid}']")
    page.click("text=Start work")
    expect(page.locator(".page-head [data-status]")).to_have_text("In Progress")
    page.click(".actions >> text=Resolve")
    page.click(".modal button[type=submit]")
    expect(page.locator("#resolution-error")).to_contain_text("required")
    page.fill("#resolution", "Replaced the HDMI switcher and tested with two laptops.")
    page.click(".modal button[type=submit]")
    expect(page.locator(".page-head [data-status]")).to_have_text("Resolved")
    logout(page)

    # 4. user sees the final status, resolution and full history
    login(page, USER)
    page.goto(f"/#/complaints/{cid}")
    expect(page.locator(".resolution")).to_contain_text("Replaced the HDMI switcher")
    expect(page.locator(".timeline li")).to_have_count(4)
    page.click("#bell")
    expect(page.locator(".popover .notif").first).to_contain_text("Resolved")

def test_notification_event_type_filter(page: Page):
    login(page, USER)

    submit_complaint(
        page,
        f"Notification filter test {uuid.uuid4().hex[:6]}",
        priority="HIGH",
    )

    page.goto("/#/notifications")

    event_filter = page.locator("#event-type")
    expect(event_filter).to_be_visible()

    event_filter.select_option("COMPLAINT_SUBMITTED")

    notifications = page.locator(".notif")
    expect(notifications).not_to_have_count(0)

    badges = page.locator(".notif .badge")
    assert all(text == "Submitted" for text in badges.all_inner_texts())


@pytest.mark.req("NFR-07")
def test_html_in_complaint_is_rendered_as_text(page: Page):
    login(page, USER)
    payload = "<img src=x onerror=\"document.body.dataset.pwned='1'\"> broken tap in lab"
    submit_complaint(page, payload, priority="LOW")
    expect(page.locator(".description")).to_have_text(payload)
    assert page.evaluate("document.body.dataset.pwned") is None
    assert page.locator(".description img").count() == 0


@pytest.mark.req("NFR-06", "BR-09")
def test_role_based_navigation_and_route_guards(page: Page):
    login(page, USER)
    expect(page.locator(".sidebar")).not_to_contain_text("Users")
    page.goto("/#/admin/users")
    expect(page).to_have_url(re.compile(r"#/complaints$"))
    page.goto("/#/dashboard")
    expect(page).to_have_url(re.compile(r"#/complaints$"))
    logout(page)
    page.goto("/#/complaints")
    expect(page).to_have_url(re.compile(r"#/login$"))


@pytest.mark.req("FR-09", "FR-16")
def test_admin_manages_categories_and_sla(page: Page):
    login(page, ADMIN)
    name = f"Library {uuid.uuid4().hex[:4]}"
    page.goto("/#/admin/categories")
    page.click("text=Add category")
    page.fill("#cat-name", name)
    page.click(".modal button[type=submit]")
    expect(page.locator(f"tr[data-name='{name}']")).to_be_visible()

    page.goto("/#/admin/sla")
    page.click("tr[data-priority=CRITICAL] >> text=Edit")
    page.fill("#sla-hours", "0")
    page.click(".modal button[type=submit]")
    expect(page.locator("#sla-hours-error")).to_contain_text("between 1 and 2160")
    page.fill("#sla-hours", "2")
    page.click(".modal button[type=submit]")
    expect(page.locator("tr[data-priority=CRITICAL]")).to_contain_text("2 hours")


@pytest.mark.req("FR-22", "FR-23", "FR-24")
def test_dashboard_and_filters(page: Page):
    login(page, USER)
    submit_complaint(page, "Bus 12 arrives 30 minutes late every morning.", priority="CRITICAL")
    logout(page)
    login(page, ADMIN)
    expect(page.locator("h1")).to_have_text("Dashboard")
    total = int(page.locator("[data-testid=kpi-total] .value").inner_text())
    assert total >= 1
    expect(page.locator("text=By category")).to_be_visible()
    page.goto("/#/complaints?scope=all")
    page.select_option("select[aria-label='Filter by priority']", "CRITICAL")
    expect(page.locator("tbody tr").first).to_contain_text("Critical")
    page.fill("input[type=search]", "Bus 12")
    expect(page.locator("tbody tr")).to_have_count(1)
    with page.expect_download() as dl:
        page.click("text=Export CSV")
    assert dl.value.suggested_filename == "complaints_report.csv"


@pytest.mark.req("FR-03", "FR-04")
def test_admin_deactivates_account(page: Page):
    email = f"temp-{uuid.uuid4().hex[:6]}@scms.example.com"
    login(page, ADMIN)
    page.goto("/#/admin/users")
    page.click("text=Add user")
    page.fill("#new-name", "Temp Staff")
    page.fill("#new-email", email)
    page.fill("#new-password", "Temp12345")
    page.click(".modal button[type=submit]")
    row = page.locator(f"tr[data-email='{email}']")
    row.locator("text=Deactivate").click()
    expect(row).to_contain_text("Inactive")
    logout(page)
    page.fill("#email", email)
    page.fill("#password", "Temp12345")
    page.click("button[type=submit]")
    expect(page.locator("[role=alert]")).to_contain_text("inactive")


@pytest.mark.req("NFR-12")
def test_mobile_layout_has_no_horizontal_scroll(page: Page):
    page.set_viewport_size({"width": 360, "height": 780})
    login(page, USER)
    for route in ("/#/complaints", "/#/complaints/new"):
        page.goto(route)
        page.wait_for_selector("h1")
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"), route
    page.click("button[aria-label='Open menu']")
    expect(page.locator(".sidebar")).to_be_in_viewport()
