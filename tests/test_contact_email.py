from agent import contact_email as ce


class FakeResp:
    def __init__(self, text, status=200):
        self.text, self.status_code, self.headers = text, status, {"content-type": "text/html"}


class FakeSession:
    def __init__(self, pages):
        self.pages = pages

    def get(self, url, **kw):
        return FakeResp(self.pages[url]) if url in self.pages else FakeResp("", 404)


def run(monkeypatch, pages, site="https://acme.com"):
    monkeypatch.setattr(ce.requests, "Session", lambda: FakeSession(pages))
    monkeypatch.setattr(ce.time, "sleep", lambda s: None)
    return ce.find_email(site)


def test_extract_variants():
    page = '<a href="mailto:Info@Acme.com">x</a> sales [at] acme [dot] com logo@2x.png'
    assert ce.extract_emails(page) == ["info@acme.com", "sales@acme.com"]


def test_generic_only():
    assert ce.is_generic("info@acme.com") and ce.is_generic("sales2@acme.com")
    assert not ce.is_generic("john.smith@acme.com")


def test_found_on_contact_page_linked_from_home(monkeypatch):
    pages = {"https://acme.com": '<a href="/get-in-touch-contact">c</a> john@acme.com',
             "https://acme.com/get-in-touch-contact": 'Write to <a href="mailto:contact@acme.com">us</a>'}
    assert run(monkeypatch, pages) == ("contact@acme.com", "https://acme.com/get-in-touch-contact")


def test_other_domains_and_personal_addresses_ignored(monkeypatch):
    pages = {"https://acme.com": "info@other.org john@acme.com"}
    assert run(monkeypatch, pages) == ("", "")
