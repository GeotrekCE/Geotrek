import datetime

extensions = [
    'sphinx.ext.todo',
    "sphinx_immaterial"
]

html_theme = 'sphinx_immaterial'
# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'Geotrek-admin'
copyright = f'2013-{datetime.date.today().year}, Makina Corpus'


exclude_patterns = ['_build']

pygments_style = 'sphinx'

html_logo = "_static/logo.svg"

# Material theme options (see theme.conf for more information)
html_theme_options = {
    "icon": {
        "repo": "fontawesome/brands/github",
        "edit": "material/file-edit-outline",
    },
    "site_url": "https://geotrek.fr/",
    "repo_url": "https://github.com/GeotrekCE/Geotrek-admin/",
    "repo_name": "Geotrek-admin",
    "edit_uri": "blob/main/docs",
    "globaltoc_collapse": True,
    "features": [
        "navigation.expand",
        # "navigation.tabs",
        # "toc.integrate",
        "navigation.sections",
        # "navigation.instant",
        # "header.autohide",
        "navigation.top",
        # "navigation.tracking",
        # "search.highlight",
        "search.share",
        "toc.follow",
        "toc.sticky",
        "content.tabs.link",
        "announce.dismiss",
    ],
    "palette": [
        {
            "media": "(prefers-color-scheme: light)",
            "scheme": "default",
            "primary": "red",
            "accent": "deep-orange",
            "toggle": {
                "icon": "material/weather-night",
                "name": "Switch to dark mode",
            },
        },
        {
            "media": "(prefers-color-scheme: dark)",
            "scheme": "slate",
            "primary": "red",
            "accent": "deep-orange",
            "toggle": {
                "icon": "material/weather-sunny",
                "name": "Switch to light mode",
            },
        },
    ],
    "social": [
        {
            "icon": "fontawesome/brands/github",
            "link": "https://github.com/GeotrekCE/Geotrek-admin"
        },
        {
            "icon": "fontawesome/brands/linkedin",
            "link": "https://www.linkedin.com/company/geotrek-application",
        },
    ],
    "toc_title_is_page_title": True,
}

html_favicon = "_static/favicon.png"

html_static_path = ['_static']

# Output file base name for HTML help builder.
htmlhelp_basename = 'Geotrekdoc'

latex_documents = [
    ('index', 'Geotrek.tex', 'Geotrek-admin Documentation',
     'Makina Corpus', 'manual'),
]

man_pages = [
    ('index', 'geotrek', 'Geotrek-admin Documentation',
     ['Makina Corpus'], 1)
]
html_sidebars = {
    "**": ["logo-text.html", "globaltoc.html", "localtoc.html", "searchbox.html"]
}
texinfo_documents = [
    ('index', 'Geotrek', 'Geotrek-admin Documentation',
     'Makina Corpus', 'Geotrek-admin', 'One line description of project.',
     'Miscellaneous'),
]

locale_dirs = ['locale']   # path is example but recommended.
gettext_compact = False     # optional.