#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import posixpath
import re
import shutil
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
DIST = ROOT / "dist"
ASSETS = ROOT / "assets"
CONTENT_ASSETS = CONTENT / "assets"
CUSTOM_DOMAIN = "www.marvtchan.com"
SUBSCRIBE_FORM_ID = "1FAIpQLSeDHC-InHmOxiSQW4twdcunkBdcmWlui_CzrVpI-1_HXLdjRw"
SUBSCRIBE_EMAIL_ENTRY = "entry.1776673923"
GOOGLE_ANALYTICS_ID = os.environ.get("GOOGLE_ANALYTICS_ID", "").strip()
ASSET_VERSION = str(int(time.time()))


@dataclass
class Page:
    source: Path
    slug: str
    title: str
    description: str
    order: int
    created: str
    updated: str
    body: str


def slug_for(path: Path) -> str:
    rel = path.relative_to(CONTENT).with_suffix("")
    slug = rel.as_posix()
    return "" if slug == "index" else slug


def parse_note(path: Path) -> Page:
    raw = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    body = raw

    if raw.startswith("---\n"):
        _, frontmatter, body = raw.split("---\n", 2)
        for line in frontmatter.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"')

    fallback_title = path.stem.replace("-", " ").title()
    title = meta.get("title", fallback_title)
    description = meta.get("description", "")
    created = meta.get("created", "")
    updated = meta.get("updated", "")
    try:
        order = int(meta.get("order", "100"))
    except ValueError:
        order = 100

    return Page(
        source=path,
        slug=slug_for(path),
        title=title,
        description=description,
        order=order,
        created=created,
        updated=updated,
        body=body.strip(),
    )


def page_href(slug: str) -> str:
    return "index.html" if slug == "" else f"{slug}/index.html"


def link_target(raw: str, pages_by_slug: dict[str, Page], current_slug: str) -> str:
    normalized = raw.strip().strip("/")
    candidates = [normalized, normalized.replace(" ", "-").lower()]
    for candidate in candidates:
        if candidate in pages_by_slug:
            return relative_href(page_href(candidate), current_slug)
    return "#"


def relative_href(path: str, current_slug: str) -> str:
    target = path.lstrip("/")
    current_dir = posixpath.dirname(page_href(current_slug)) or "."
    return posixpath.relpath(target, start=current_dir)


def inline_markup(text: str, pages_by_slug: dict[str, Page], current_slug: str) -> str:
    escaped = html.escape(text)

    def replace_image(match: re.Match[str]) -> str:
        alt = html.escape(match.group(1))
        src = html.escape(asset_path(match.group(2), current_slug))
        return f'<img src="{src}" alt="{alt}">'

    def replace_wikilink(match: re.Match[str]) -> str:
        target = match.group(1)
        label = match.group(2) or target.split("/")[-1].replace("-", " ")
        href = link_target(target, pages_by_slug, current_slug)
        return f'<a href="{href}">{html.escape(label)}</a>'

    escaped = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace_image, escaped)
    escaped = re.sub(r"\[\[([^|\]]+)(?:\|([^\]]+))?\]\]", replace_wikilink, escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def asset_path(raw: str, current_slug: str) -> str:
    path = raw.strip()
    if re.match(r"^[a-z][a-z0-9+.-]*://", path, flags=re.I):
        return path
    if path.startswith("content/assets/"):
        return relative_href(path.removeprefix("content/"), current_slug)
    if path.startswith("assets/"):
        return relative_href(path, current_slug)
    if path.startswith("/"):
        return relative_href(path, current_slug)
    return path


def markdown_to_html(markdown: str, pages_by_slug: dict[str, Page], current_slug: str) -> str:
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[tuple[int, str, str]] = []
    quote_lines: list[str] = []
    in_code = False
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(line.strip() for line in paragraph)
            blocks.append(f"<p>{inline_markup(text, pages_by_slug, current_slug)}</p>")
            paragraph.clear()

    def flush_list() -> None:
        if list_items:
            blocks.append(render_list(list_items, pages_by_slug, current_slug))
            list_items.clear()

    def flush_quote() -> None:
        if quote_lines:
            text = " ".join(line.strip() for line in quote_lines)
            blocks.append(f"<blockquote><p>{inline_markup(text, pages_by_slug, current_slug)}</p></blockquote>")
            quote_lines.clear()

    for line in markdown.splitlines():
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                blocks.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines.clear()
                in_code = False
            else:
                flush_paragraph()
                flush_list()
                flush_quote()
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            flush_paragraph()
            flush_list()
            flush_quote()
            continue

        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            flush_list()
            flush_quote()
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{inline_markup(heading.group(2), pages_by_slug, current_slug)}</h{level}>")
            continue

        unordered = re.match(r"^(\s*)-+\s+(.+)$", line)
        ordered = re.match(r"^(\s*)\d+\.\s+(.+)$", line)
        list_match = unordered or ordered
        if list_match:
            flush_paragraph()
            flush_quote()
            indent = len(list_match.group(1).expandtabs(2))
            tag = "ul" if unordered else "ol"
            list_items.append((indent // 2, tag, list_match.group(2)))
            continue

        quote = re.match(r"^>\s?(.*)$", stripped)
        if quote:
            flush_paragraph()
            flush_list()
            quote_lines.append(quote.group(1))
            continue

        flush_quote()
        paragraph.append(stripped)

    flush_paragraph()
    flush_list()
    flush_quote()
    return "\n".join(blocks)


def render_list(items: list[tuple[int, str, str]], pages_by_slug: dict[str, Page], current_slug: str) -> str:
    parts: list[str] = []
    stacks: list[tuple[int, str]] = []
    open_items: list[bool] = []

    for level, tag, text in items:
        if not stacks:
            parts.append(f"<{tag}>")
            stacks.append((level, tag))
            open_items.append(False)
        elif level > stacks[-1][0]:
            parts.append(f"<{tag}>")
            stacks.append((level, tag))
            open_items.append(False)
        else:
            while stacks and (level < stacks[-1][0] or (level == stacks[-1][0] and tag != stacks[-1][1])):
                if open_items[-1]:
                    parts.append("</li>")
                parts.append(f"</{stacks[-1][1]}>")
                stacks.pop()
                open_items.pop()

            if stacks and level == stacks[-1][0] and tag == stacks[-1][1] and open_items[-1]:
                parts.append("</li>")
                open_items[-1] = False

        if not stacks:
            parts.append(f"<{tag}>")
            stacks.append((level, tag))
            open_items.append(False)

        parts.append(f"<li>{inline_markup(text, pages_by_slug, current_slug)}")
        open_items[-1] = True

    while stacks:
        if open_items[-1]:
            parts.append("</li>")
        parts.append(f"</{stacks[-1][1]}>")
        stacks.pop()
        open_items.pop()

    return "".join(parts)


def latest_blog_page(pages: list[Page]) -> Page | None:
    blog_pages = [page for page in pages if page.slug.startswith("blog/")]
    if not blog_pages:
        return None
    return max(
        blog_pages,
        key=lambda page: (
            created_sort_value(page),
            page.source.stat().st_mtime,
            page.title.lower(),
        ),
    )


def render_latest_post_preview(page: Page, pages_by_slug: dict[str, Page], current_slug: str) -> str:
    date = page.updated or page.created
    meta = f'<p class="latest-post-meta">{html.escape(date)}</p>' if date else ""
    body_without_title = re.sub(r"^#\s+.+\n+", "", page.body, count=1)
    excerpt = text_excerpt(body_without_title, 260)
    href = relative_href(page_href(page.slug), current_slug)
    return f"""
<section class="latest-post" aria-labelledby="latest-post-heading">
  <h2 id="latest-post-heading"><a href="{href}">{html.escape(page.title)}</a></h2>
  {meta}
  <p>{html.escape(excerpt)}</p>
  <a class="latest-post-link" href="{href}">Read post</a>
</section>
"""


def render_subscribe_section() -> str:
    form_url = f"https://docs.google.com/forms/d/e/{SUBSCRIBE_FORM_ID}/formResponse"
    fallback_url = f"https://docs.google.com/forms/d/e/{SUBSCRIBE_FORM_ID}/viewform"
    return f"""
<section class="subscribe-section" aria-labelledby="subscribe-heading">
  <div>
    <h2 id="subscribe-heading">Subscribe</h2>
    <p>Get new posts by email.</p>
  </div>
  <form class="subscribe-form" action="{html.escape(form_url)}" method="POST" data-subscribe-form data-fallback-url="{html.escape(fallback_url)}">
    <input type="hidden" name="fvv" value="1">
    <input type="hidden" name="pageHistory" value="0">
    <label class="sr-only" for="subscribe-email">Email address</label>
    <input id="subscribe-email" name="{html.escape(SUBSCRIBE_EMAIL_ENTRY)}" type="email" placeholder="email address" autocomplete="email" required>
    <button type="submit">Subscribe</button>
  </form>
  <p class="subscribe-status" data-subscribe-status hidden></p>
</section>
"""


def ordered_pages(pages: list[Page]) -> list[Page]:
    section_order = {
        "": 0,
        "blog": 1,
        "projects": 2,
        "resume": 3,
    }

    def key(page: Page) -> tuple[int, float, int, str]:
        section = "" if page.slug == "" else page.slug.split("/", 1)[0]
        return (
            section_order.get(section, 99),
            -created_sort_value(page),
            page.order,
            page.title.lower(),
        )

    return sorted(pages, key=key)


def adjacent_pages(page: Page, pages: list[Page]) -> tuple[Page | None, Page | None]:
    ordered = ordered_pages(pages)
    index = next((i for i, candidate in enumerate(ordered) if candidate.slug == page.slug), -1)
    if index == -1:
        return None, None
    previous_page = ordered[index - 1] if index > 0 else None
    next_page = ordered[index + 1] if index < len(ordered) - 1 else None
    return previous_page, next_page


def render_page_nav(page: Page, pages: list[Page]) -> str:
    previous_page, next_page = adjacent_pages(page, pages)
    if not previous_page and not next_page:
        return ""

    links = []
    if previous_page:
        links.append(
            f'<a class="page-swipe-link page-swipe-link-previous" '
            f'href="{relative_href(page_href(previous_page.slug), page.slug)}">'
            f'<span>Previous</span><strong>{html.escape(previous_page.title)}</strong></a>'
        )
    if next_page:
        links.append(
            f'<a class="page-swipe-link page-swipe-link-next" '
            f'href="{relative_href(page_href(next_page.slug), page.slug)}">'
            f'<span>Next</span><strong>{html.escape(next_page.title)}</strong></a>'
        )
    link_markup = "\n  ".join(links)

    return f"""
<nav class="page-swipe-nav" aria-label="Page navigation">
  {link_markup}
</nav>
"""


def render_page(page: Page, pages: list[Page], pages_by_slug: dict[str, Page]) -> str:
    directory = render_directory(page, pages)
    content = markdown_to_html(page.body, pages_by_slug, page.slug)
    if page.slug == "":
        latest_post = latest_blog_page(pages)
        if latest_post:
            content = f"{content}\n{render_latest_post_preview(latest_post, pages_by_slug, page.slug)}"
    content = f"{content}\n{render_subscribe_section()}"
    description = html.escape(page.description)
    title = html.escape(page.title)
    metadata = render_page_metadata(page)
    page_nav = render_page_nav(page, pages)
    previous_page, next_page = adjacent_pages(page, pages)
    previous_url = relative_href(page_href(previous_page.slug), page.slug) if previous_page else ""
    next_url = relative_href(page_href(next_page.slug), page.slug) if next_page else ""
    swipe_attrs = (
        f' data-swipe-previous="{html.escape(previous_url, quote=True)}"'
        f' data-swipe-next="{html.escape(next_url, quote=True)}"'
    )
    analytics = render_google_analytics()
    analytics_block = f"\n    {analytics}" if analytics else ""

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="{description}">{analytics_block}
    <title>{title} | Marvin Chan</title>
    <link rel="stylesheet" href="{relative_href("assets/styles.css", page.slug)}?v={ASSET_VERSION}">
    <script src="{relative_href("assets/site.js", page.slug)}?v={ASSET_VERSION}" defer></script>
  </head>
  <body{swipe_attrs}>
    <header class="site-header">
      <div class="header-left">
        <button class="sidebar-toggle" type="button" data-sidebar-toggle aria-controls="site-directory" aria-expanded="true">
          <span aria-hidden="true">☰</span>
          <span>Directory</span>
        </button>
        <a class="site-title" href="{relative_href(page_href(""), page.slug)}">Marvin Chan</a>
      </div>
      <div class="header-right">
        <search class="site-search" role="search">
          <label class="sr-only" for="site-search">Search notes</label>
          <input id="site-search" type="search" placeholder="search notes..." autocomplete="off" data-search-input>
          <div class="search-results" data-search-results hidden></div>
        </search>
        <label class="theme-switch" for="theme-toggle">
          <span class="sr-only">Dark mode</span>
          <input id="theme-toggle" type="checkbox" data-theme-toggle>
          <span class="theme-slider" aria-hidden="true">
            <span>Light</span>
            <span>Dark</span>
          </span>
        </label>
      </div>
    </header>
    <div class="site-shell">
      <aside id="site-directory" class="directory" aria-label="Site directory">
        <div class="directory-inner">
          <p class="directory-label">Directory</p>
          {directory}
        </div>
      </aside>
      <main class="note">
        {metadata}
        {content}
{page_nav}
      </main>
    </div>
    <footer>
      <p>Built from Markdown notes.</p>
    </footer>
  </body>
</html>
"""


def render_google_analytics() -> str:
    if not GOOGLE_ANALYTICS_ID:
        return ""

    tag_id = html.escape(GOOGLE_ANALYTICS_ID, quote=True)
    return f"""<!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={tag_id}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{tag_id}');
    </script>"""


def render_page_metadata(page: Page) -> str:
    items = []
    if page.created:
        items.append(f"<span>Created {html.escape(page.created)}</span>")
    if page.updated:
        items.append(f"<span>Updated {html.escape(page.updated)}</span>")
    if not items:
        return ""
    return f'<div class="page-meta">{"".join(items)}</div>'


def created_sort_value(page: Page) -> float:
    if not page.created:
        return float("-inf")
    try:
        return datetime.fromisoformat(page.created).timestamp()
    except ValueError:
        return float("-inf")


def render_directory(current_page: Page, pages: list[Page]) -> str:
    grouped: dict[str, list[Page]] = {}
    for page in pages:
        section = "home" if page.slug == "" else page.slug.split("/", 1)[0]
        grouped.setdefault(section, []).append(page)

    preferred = ["home", "blog", "projects", "resume"]
    section_labels = {
        "home": "Home",
        "blog": "Blog",
        "projects": "Project",
        "resume": "Resume",
    }
    ordered_sections = [section for section in preferred if section in grouped]
    ordered_sections.extend(section for section in sorted(grouped) if section not in preferred)

    parts: list[str] = []
    for section in ordered_sections:
        heading = section_labels.get(section, section.replace("-", " ").title())
        section_open = " open" if any(page.slug == current_page.slug for page in grouped[section]) else ""
        parts.append(
            f'<details class="directory-section"{section_open}>'
            f'<summary>{html.escape(heading)}</summary><ol>'
        )
        for page in sorted(
            grouped[section],
            key=lambda p: (-created_sort_value(p), p.order, p.title.lower()),
        ):
            active = ' aria-current="page"' if page.slug == current_page.slug else ""
            class_name = ' class="active"' if page.slug == current_page.slug else ""
            href = relative_href(page_href(page.slug), current_page.slug)
            parts.append(
                f'<li><a{class_name}{active} href="{href}">{html.escape(page.title)}</a></li>'
            )
        parts.append("</ol></details>")

    return "\n".join(parts)


def build() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    pages = [parse_note(path) for path in sorted(CONTENT.rglob("*.md"))]
    pages_by_slug = {page.slug: page for page in pages}

    for page in pages:
        output = DIST / page_href(page.slug)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_page(page, pages, pages_by_slug), encoding="utf-8")

    if ASSETS.exists():
        shutil.copytree(ASSETS, DIST / "assets")
    if CONTENT_ASSETS.exists():
        shutil.copytree(CONTENT_ASSETS, DIST / "assets", dirs_exist_ok=True)

    (DIST / "CNAME").write_text(f"{CUSTOM_DOMAIN}\n", encoding="utf-8")
    write_search_index(pages)
    print(f"Built {len(pages)} pages into {DIST}")


def text_excerpt(markdown: str, limit: int = 180) -> str:
    plain = plain_text(markdown)
    return plain[:limit]


def plain_text(markdown: str) -> str:
    return re.sub(r"\s+", " ", " ".join(search_lines(markdown))).strip()


def search_lines(markdown: str) -> list[str]:
    without_code = re.sub(r"```.*?```", "", markdown, flags=re.S)
    without_frontmatter = re.sub(r"^---\n.*?\n---\n", "", without_code, flags=re.S)
    lines = []

    for line in without_frontmatter.splitlines():
        cleaned = re.sub(
            r"\[\[([^|\]]+)\|([^\]]+)\]\]",
            lambda match: match.group(2),
            line,
        )
        cleaned = re.sub(
            r"\[\[([^\]]+)\]\]",
            lambda match: match.group(1).split("/")[-1].replace("-", " "),
            cleaned,
        )
        cleaned = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", cleaned)
        cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
        cleaned = re.sub(r"^\s{0,6}(?:[-*]+|\d+\.)\s+", "", cleaned)
        cleaned = re.sub(r"^\s{0,6}>+\s?", "", cleaned)
        cleaned = re.sub(r"[\[#*_`]+", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if cleaned:
            lines.append(cleaned)

    return lines


def write_search_index(pages: list[Page]) -> None:
    data = [
        {
            "title": page.title,
            "description": page.description,
            "url": page_href(page.slug),
            "excerpt": text_excerpt(page.body),
            "text": plain_text(page.body),
            "lines": search_lines(page.body),
        }
        for page in pages
    ]
    (DIST / "search.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    build()
