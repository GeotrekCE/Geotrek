import datetime
import os

root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

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

sphinx_immaterial_custom_admonitions = [
    {
        "name": "legend",
        "color": (142, 142, 142),
        "icon": "fontawesome/solid/eye",
    },
    {
        "name": "ns-only-fr",
        "color": (72, 138, 87),
        "icon": None,  # This does not work, it is overriden in CSS
        "title": "✨ Disponible uniquement en segmentation dynamique",
    },
    {
        "name": "ns-only",
        "color": (72, 138, 87),
        "icon": None,  # This does not work, it is overriden in CSS
        "title": "✨ Only available in dynamic segmentation",
    },
    {
        "name": "ns-detail-fr",
        "color": (72, 138, 87),
        "icon": None,  # This does not work, it is overriden in CSS
        "title": "🗺️ Données stockées via segmentation dynamique lorsqu'elle est activée",
    },
    {
        "name": "ns-detail",
        "color": (72, 138, 87),
        "icon": None,  # This does not work, it is overriden in CSS
        "title": "🗺️ Data stored via dynamic segmentation when enabled",
    },
]

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
            "primary": "green",
            "accent": "light-green",
            "toggle": {
                "icon": "material/weather-night",
                "name": "Switch to dark mode",
            },
        },
        {
            "media": "(prefers-color-scheme: dark)",
            "scheme": "slate",
            "primary": "green",
            "accent": "light-green",
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
html_css_files = ["extra_css.css"]

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
     'Makina Corpus', 'Geotrek-admin',
     'Miscellaneous'),
]
