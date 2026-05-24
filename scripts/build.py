#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import posixpath
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
DIST = ROOT / "dist"
ASSETS = ROOT / "assets"
CONTENT_ASSETS = CONTENT / "assets"
CUSTOM_DOMAIN = "www.marvtchan.com"
SUBSCRIBE_FORM_ID = "1FAIpQLSeDHC-InHmOxiSQW4twdcunkBdcmWlui_CzrVpI-1_HXLdjRw"
SUBSCRIBE_EMAIL_ENTRY = "entry.1776673923"


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
            page.updated or page.created,
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

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="{description}">
    <title>{title} | Marvin Chan</title>
    <link rel="stylesheet" href="{relative_href("assets/styles.css", page.slug)}">
    <script src="{relative_href("assets/site.js", page.slug)}" defer></script>
  </head>
  <body>
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
      </main>
    </div>
    <footer>
      <p>Built from Markdown notes.</p>
    </footer>
  </body>
</html>
"""


def render_page_metadata(page: Page) -> str:
    items = []
    if page.created:
        items.append(f"<span>Created {html.escape(page.created)}</span>")
    if page.updated:
        items.append(f"<span>Updated {html.escape(page.updated)}</span>")
    if not items:
        return ""
    return f'<div class="page-meta">{"".join(items)}</div>'


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
        for page in sorted(grouped[section], key=lambda p: (p.order, p.title.lower())):
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
    without_code = re.sub(r"```.*?```", "", markdown, flags=re.S)
    without_frontmatter = re.sub(r"^---\n.*?\n---\n", "", without_code, flags=re.S)
    wikilinks_resolved = re.sub(
        r"\[\[([^|\]]+)\|([^\]]+)\]\]",
        lambda match: match.group(2),
        without_frontmatter,
    )
    wikilinks_resolved = re.sub(
        r"\[\[([^\]]+)\]\]",
        lambda match: match.group(1).split("/")[-1].replace("-", " "),
        wikilinks_resolved,
    )
    plain = re.sub(r"[\[#*_`>\]-]+", " ", wikilinks_resolved)
    plain = re.sub(r"\s+", " ", plain).strip()
    return plain[:limit]


def write_search_index(pages: list[Page]) -> None:
    data = [
        {
            "title": page.title,
            "description": page.description,
            "url": page_href(page.slug),
            "text": text_excerpt(page.body),
        }
        for page in pages
    ]
    (DIST / "search.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    build()
