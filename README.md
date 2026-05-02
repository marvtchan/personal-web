# Marvin Chan Notes

Minimal Obsidian-powered website for public notes, resume, and selected work.

Edit Markdown in `content/`. Run the build script to generate static HTML in `dist/`.

## Local preview

```sh
python3 scripts/build.py
cd dist
python3 -m http.server 4173
```

Then open `http://localhost:4173`.

## Content model

- `content/index.md` is the homepage.
- Any other `.md` file under `content/` becomes a page.
- `library/index.html` is generated automatically and lists every public page.
- Frontmatter supports `title`, `description`, and `order`.
- Obsidian wikilinks like `[[resume]]` and `[[notes/finance-control-plane|Finance control plane]]` are converted to site links.

Suggested folders:

- `content/notes/` for evergreen notes.
- `content/thoughts/` for shorter public thoughts.
- `content/project-summaries/` for project writeups.

## Publish workflow

```sh
git add content
git commit -m "Publish notes"
git push
```

After pushing to GitHub, the included GitHub Pages workflow builds the site and deploys `dist/`.

## Deploy options

### Cloudflare Pages

1. Create a new GitHub repo for this folder.
2. Connect the repo in Cloudflare Pages.
3. Build command: `python3 scripts/build.py`.
4. Build output directory: `dist`.
5. Add the custom domain in Cloudflare Pages.
6. In Squarespace DNS, point the desired host to the Pages target Cloudflare gives you.

### GitHub Pages

1. Push this folder to a GitHub repo.
2. In the repository settings, enable Pages with source set to GitHub Actions.
3. Push to `main`; `.github/workflows/pages.yml` builds and deploys the site.

## Content TODO

- Replace placeholder contact links.
- Add public project links.
- Add a downloadable PDF resume.
- Add more public notes under `content/notes/`.
