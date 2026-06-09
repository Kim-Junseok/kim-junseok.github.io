---
name: homepage-quality
description: Use when editing this Jekyll homepage, including content, layouts, styles, links, images, assets, navigation, or deployment checks. Ensures responsive compatibility, safe external links, accessible images, and build validation for kim-junseok.github.io.
---

# Homepage Quality

Use this skill for changes to this personal Jekyll/Chirpy site.

## Core Rules

- Preserve the homepage's quiet, neat profile-first layout unless the user explicitly asks for a larger redesign.
- Do not edit `_site` directly. It is generated output.
- Keep changes scoped to the page, include, asset, or workflow relevant to the request.
- Treat user edits in the working tree as intentional. Do not revert unrelated changes.

## Content And Layout

- Check mobile, tablet, and desktop behavior when a change affects layout, images, text length, navigation, or cards.
- Avoid fixed widths that can overflow. Prefer `width: 100%`, `max-width`, grid/flex constraints, and responsive media rules.
- Ensure text does not overlap, clip, or depend on viewport-scaled font sizes.
- Keep page sections unframed unless the content is a repeated item, modal, or tool surface.
- Keep the palette and spacing consistent with the existing Chirpy theme and local `metadata-hook.html` customizations.
- Keep the first-load default theme dark while preserving the visible theme toggle.

## Links And Assets

- Use `{{ '/path' | relative_url }}` for local assets in Jekyll source.
- External content links should open in a new tab with `target="_blank"` and include `rel="noopener"` at minimum.
- The `_plugins/external_links.rb` build hook enforces new-tab external links in generated HTML; keep `scripts/check_site.py` aligned with that policy.
- The `_plugins/default_theme_mode.rb` build hook enforces the generated dark default; keep the toggle logic in `metadata-hook.html` compatible with it.
- Images must have meaningful `alt` text unless they are purely decorative.
- Avoid adding large visual assets without checking file size and responsive rendering.

## Verification

Run these before finishing site changes:

```bash
bundle exec jekyll build
python3 scripts/check_site.py
```

If the change has visual risk and browser tooling is available, also verify key pages at narrow mobile, tablet, and desktop widths.
