from playwright.sync_api import sync_playwright


def test_login_page():
    with sync_playwright() as p:
        request = p.request.new_context(
            base_url="http://127.0.0.1:5000"
        )

        response = request.get("/login")

        assert response.status == 200
        assert "Login" in response.text()

        request.dispose()