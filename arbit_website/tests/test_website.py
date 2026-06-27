"""
Автотесты для статического сайта Crypto Arbitrage Bot.
Проверяют HTML-валидность, наличие ключевых элементов и ссылок.
"""
import os
from pathlib import Path
from bs4 import BeautifulSoup
import pytest

# Путь к HTML файлам
LANDING_DIR = Path(__file__).parent.parent / "arb-landing"


def load_html(filename: str) -> BeautifulSoup:
    """Загружает HTML файл и возвращает BeautifulSoup объект."""
    filepath = LANDING_DIR / filename
    assert filepath.exists(), f"Файл не найден: {filepath}"
    with open(filepath, "r", encoding="utf-8") as f:
        return BeautifulSoup(f.read(), "lxml")


class TestIndexPage:
    """Тесты главной страницы."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.soup = load_html("index.html")

    def test_page_has_title(self):
        """Страница имеет title."""
        title = self.soup.find("title")
        assert title is not None
        assert len(title.text.strip()) > 0

    def test_page_has_meta_description(self):
        """Страница имеет meta description."""
        meta = self.soup.find("meta", attrs={"name": "description"})
        assert meta is not None
        assert len(meta.get("content", "").strip()) > 0

    def test_page_has_main_heading(self):
        """Страница имеет главный заголовок H1."""
        h1 = self.soup.find("h1")
        assert h1 is not None
        assert len(h1.text.strip()) > 0

    def test_page_has_css_link(self):
        """Страница подключает CSS."""
        css_link = self.soup.find("link", attrs={"rel": "stylesheet"})
        assert css_link is not None
        assert "styles.css" in css_link.get("href", "")

    def test_page_has_cta_button(self):
        """Страница имеет CTA-кнопку."""
        buttons = self.soup.find_all("button")
        links = self.soup.find_all("a", href=True)
        # Хотя бы одна кнопка или ссылка с текстом
        has_cta = any(
            btn.text.strip() for btn in buttons
        ) or any(
            "начать" in link.text.lower() or "start" in link.text.lower()
            for link in links
        )
        assert has_cta, "Нет CTA-кнопки или ссылки"

    def test_page_has_no_broken_internal_links(self):
        """Все внутренние ссылки ведут на существующие файлы."""
        links = self.soup.find_all("a", href=True)
        for link in links:
            href = link["href"]
            # Пропускаем внешние ссылки и якоря
            if href.startswith("http") or href.startswith("#") or href.startswith("mailto:"):
                continue
            # Проверяем локальные файлы
            if href.endswith(".html"):
                target = LANDING_DIR / href
                assert target.exists(), f"Ссылка ведёт на несуществующий файл: {href}"


class TestSuccessPage:
    """Тесты страницы успешной оплаты."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.soup = load_html("success_payment.html")

    def test_page_has_title(self):
        """Страница имеет title."""
        title = self.soup.find("title")
        assert title is not None
        assert "успешн" in title.text.lower() or "success" in title.text.lower()

    def test_page_has_success_message(self):
        """Страница имеет сообщение об успехе."""
        body_text = self.soup.get_text().lower()
        assert "успешн" in body_text or "success" in body_text


class TestFailedPage:
    """Тесты страницы неудачной оплаты."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.soup = load_html("failed_payment.html")

    def test_page_has_title(self):
        """Страница имеет title."""
        title = self.soup.find("title")
        assert title is not None

    def test_page_has_error_message(self):
        """Страница имеет сообщение об ошибке."""
        body_text = self.soup.get_text().lower()
        assert "ошибк" in body_text or "fail" in body_text or "error" in body_text


class TestCSS:
    """Тесты CSS файла."""

    def test_css_file_exists(self):
        """CSS файл существует."""
        css_path = LANDING_DIR / "styles.css"
        assert css_path.exists()

    def test_css_not_empty(self):
        """CSS файл не пустой."""
        css_path = LANDING_DIR / "styles.css"
        assert css_path.stat().st_size > 100  # Хотя бы 100 байт

    def test_css_has_responsive_design(self):
        """CSS содержит медиа-запросы (адаптивность)."""
        css_path = LANDING_DIR / "styles.css"
        with open(css_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "@media" in content, "Нет медиа-запросов для адаптивности"
