# Marvin Chan Portfolio

Static portfolio site for Marvin Chan.

## Local preview

```sh
python3 -m http.server 4173
```

Then open `http://localhost:4173`.

## Deploy options

### Cloudflare Pages

1. Create a new GitHub repo for this folder.
2. Connect the repo in Cloudflare Pages.
3. Build command: leave blank.
4. Build output directory: `/`.
5. Add the custom domain in Cloudflare Pages.
6. In Squarespace DNS, point the desired host to the Pages target Cloudflare gives you.

### GitHub Pages

1. Push this folder to a GitHub repo.
2. Enable Pages from the repo settings.
3. Use branch `main` and root `/`.
4. Add the custom domain in GitHub Pages settings.
5. Add the matching DNS records in Squarespace.

## Content TODO

- Replace placeholder contact links.
- Add public project links.
- Add a downloadable PDF resume.
- Replace `notes.example.com` with the real notes subdomain.
- Decide whether notes use Obsidian Publish or Quartz.
