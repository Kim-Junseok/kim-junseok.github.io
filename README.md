# Junseok Kim - Jekyll (Chirpy)

This repository now uses **Jekyll + Chirpy** as the primary website stack.

## Local build

```bash
python3 requirements.py --install
python3 requirements.py --serve
```

Then open `http://127.0.0.1:4000`.

If Ruby or Bundler is missing, run `python3 requirements.py` to print the
Ubuntu/WSL package install commands.

If the project gems are already installed, you can also check the homepage
locally with:

```bash
bundle exec jekyll serve --host 127.0.0.1 --port 4000
```

Before pushing layout, content, link, or asset changes, run the same quality
check used by GitHub Actions:

```bash
bundle exec jekyll build
python3 scripts/check_site.py
```

## Content structure

- `index.html`: homepage entry
- `_tabs/about.md`: profile/about page
- `_tabs/publications.md`: publications page
- `_posts/`: blog posts (e.g., Sionna, O-RAN)
