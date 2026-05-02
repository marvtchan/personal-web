#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
DIST = ROOT / "dist"
ASSETS = ROOT / "assets"


@dataclass
class Page:
    source: Path
    slug: str
    title: str
    description: str
    order: int
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
        body=body.strip(),
    )


def page_href(slug: str) -> str:
    return "index.html" if slug == "" else f"{slug}/index.html"


def link_target(raw: str, pages_by_slug: dict[str, Page]) -> str:
    normalized = raw.strip().strip("/")
    candidates = [normalized, normalized.replace(" ", "-").lower()]
    for candidate in candidates:
        if candidate in pages_by_slug:
            return relative_href(page_href(candidate))
    return "#"


def relative_href(path: str) -> str:
    return "/" + path


def inline_markup(text: str, pages_by_slug: dict[str, Page]) -> str:
    escaped = html.escape(text)

    def replace_wikilink(match: re.Match[str]) -> str:
        target = match.group(1)
        label = match.group(2) or target.split("/")[-1].replace("-", " ")
        href = link_target(target, pages_by_slug)
        return f'<a href="{href}">{html.escape(label)}</a>'

    escaped = re.sub(r"\[\[([^|\]]+)(?:\|([^\]]+))?\]\]", replace_wikilink, escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def markdown_to_html(markdown: str, pages_by_slug: dict[str, Page]) -> str:
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    in_code = False
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(line.strip() for line in paragraph)
            blocks.append(f"<p>{inline_markup(text, pages_by_slug)}</p>")
            paragraph.clear()

    def flush_list() -> None:
        if list_items:
            items = "".join(f"<li>{inline_markup(item, pages_by_slug)}</li>" for item in list_items)
            blocks.append(f"<ul>{items}</ul>")
            list_items.clear()

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
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            flush_list()
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{inline_markup(heading.group(2), pages_by_slug)}</h{level}>")
            continue

        bullet = re.match(r"^-+\s+(.+)$", stripped)
        if bullet:
            flush_paragraph()
            list_items.append(bullet.group(1))
            continue

        paragraph.append(stripped)

    flush_paragraph()
    flush_list()
    return "\n".join(blocks)


def render_page(page: Page, pages: list[Page], pages_by_slug: dict[str, Page]) -> str:
    nav_pages = [item for item in pages if item.slug in {"", "resume", "projects", "library"}]
    nav = "\n".join(
        f'<a href="{relative_href(page_href(item.slug))}">{html.escape(item.title)}</a>'
        for item in sorted(nav_pages, key=lambda p: (p.order, p.title.lower()))
    )
    directory = render_directory(page, pages)
    content = markdown_to_html(page.body, pages_by_slug)
    description = html.escape(page.description)
    title = html.escape(page.title)

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="{description}">
    <title>{title} | Marvin Chan</title>
    <link rel="stylesheet" href="/assets/styles.css">
    <script src="/assets/site.js" defer></script>
  </head>
  <body>
    <header class="site-header">
      <div class="header-left">
        <button class="sidebar-toggle" type="button" data-sidebar-toggle aria-controls="site-directory" aria-expanded="true">
          <span aria-hidden="true">☰</span>
          <span>Directory</span>
        </button>
        <a class="site-title" href="/">Marvin Chan</a>
      </div>
      <nav aria-label="Primary navigation">
        {nav}
      </nav>
    </header>
    <div class="site-shell">
      <aside id="site-directory" class="directory" aria-label="Site directory">
        <div class="directory-inner">
          <p class="directory-label">Directory</p>
          {directory}
        </div>
      </aside>
      <main class="note">
        {content}
      </main>
    </div>
    <footer>
      <p>Built from Markdown notes.</p>
    </footer>
  </body>
</html>
"""


def render_directory(current_page: Page, pages: list[Page]) -> str:
    grouped: dict[str, list[Page]] = {}
    for page in pages:
        section = "home" if page.slug == "" else page.slug.split("/", 1)[0]
        grouped.setdefault(section, []).append(page)

    preferred = ["home", "resume", "projects", "library", "notes", "project-summaries", "thoughts"]
    ordered_sections = [section for section in preferred if section in grouped]
    ordered_sections.extend(section for section in sorted(grouped) if section not in preferred)

    parts: list[str] = []
    for section in ordered_sections:
        heading = section.replace("-", " ").title()
        section_open = " open" if any(page.slug == current_page.slug for page in grouped[section]) else ""
        parts.append(
            f'<details class="directory-section"{section_open}>'
            f'<summary>{html.escape(heading)}</summary><ol>'
        )
        for page in sorted(grouped[section], key=lambda p: (p.order, p.title.lower())):
            active = ' aria-current="page"' if page.slug == current_page.slug else ""
            class_name = ' class="active"' if page.slug == current_page.slug else ""
            href = relative_href(page_href(page.slug))
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
    pages.append(make_library_page(pages))
    pages_by_slug = {page.slug: page for page in pages}

    for page in pages:
        output = DIST / page_href(page.slug)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_page(page, pages, pages_by_slug), encoding="utf-8")

    if ASSETS.exists():
        shutil.copytree(ASSETS, DIST / "assets")

    print(f"Built {len(pages)} pages into {DIST}")


def make_library_page(pages: list[Page]) -> Page:
    grouped: dict[str, list[Page]] = {}
    for page in pages:
        if page.slug == "":
            continue
        section = page.slug.split("/", 1)[0]
        grouped.setdefault(section, []).append(page)

    lines = [
        "# Library",
        "",
        "Everything public in this site, generated from Markdown files.",
        "",
    ]

    for section in sorted(grouped):
        heading = section.replace("-", " ").title()
        lines.extend([f"## {heading}", ""])
        for page in sorted(grouped[section], key=lambda p: (p.order, p.title.lower())):
            target = page.slug
            lines.append(f"- [[{target}|{page.title}]]")
        lines.append("")

    return Page(
        source=CONTENT / "library.md",
        slug="library",
        title="Library",
        description="All public notes, project summaries, thoughts, and pages.",
        order=4,
        body="\n".join(lines).strip(),
    )


if __name__ == "__main__":
    build()
