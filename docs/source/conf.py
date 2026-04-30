html_theme = "pydata_sphinx_theme"

html_css_files = ["custom.css"]  

html_theme_options = {
    "github_url": "https://github.com/Kim-Junseok",
    "header_links_before_dropdown": 4,
    "navbar_end": ["navbar-icon-links"],
    "footer_start": ["copyright"],
    "footer_end": [],
    "show_prev_next": False,
    "icon_links": [
        {
            "name": "LinkedIn",
            "url": "https://www.linkedin.com/in/junsk",
            "icon": "fa-brands fa-linkedin",
            "type": "fontawesome",
        },
        {
            "name": "Google Scholar",
            "url": "https://scholar.google.com/citations?user=mJTAhlgAAAAJ&hl=en",
            "icon": "ai ai-google-scholar",
            "type": "fontawesome",
        }
    ],
}

# Show source 제거
html_show_sourcelink = False

html_title = "Junseok Kim"
html_static_path = ['_static']