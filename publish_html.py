from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
DOCS_DIR = REPO_ROOT / "docs"


def seo_meta_tags(title: str, description: str, url: str = None) -> str:
    """Generate SEO meta tags for a page."""
    base_url = "https://jarogumulec.github.io/perseidy"
    full_url = f"{base_url}/{url}" if url else base_url

    return f'''
    <title>{title}</title>
    <meta name="description" content="{description}">
    <meta name="keywords" content="perseidy, tmava obloha, svetelne zneistení, astronomie, ceska republika, vyhlidkova mista">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{full_url}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    '''


def save_html_for_pages(map_obj, output_file: Path):
    output_file = Path(output_file)
    docs_file = DOCS_DIR / output_file.relative_to(REPO_ROOT)
    docs_file.parent.mkdir(parents=True, exist_ok=True)
    map_obj.save(str(docs_file))

    output_file.parent.mkdir(parents=True, exist_ok=True)
    map_obj.save(str(output_file))

    return output_file, docs_file


def github_link_html(url: str = "https://github.com/jarogumulec/perseidy") -> str:
        return f'''
        <div style="position: fixed; top: 10px; left: 10px; z-index: 1100;">
            <a href="{url}" target="_blank" rel="noopener noreferrer"
                 style="display:inline-block;padding:8px 12px;border-radius:999px;
                                background:rgba(15,27,45,0.92);color:#e7eef8;text-decoration:none;
                                border:1px solid rgba(255,255,255,0.14);font-size:12px;
                                box-shadow:0 8px 22px rgba(0,0,0,0.25);">
                GitHub
            </a>
        </div>
        '''


def back_link_html(label: str, href: str) -> str:
        return f'''
        <div style="position: fixed; top: 10px; left: 10px; z-index: 1100;">
            <a href="{href}" style="display:inline-block;padding:8px 12px;border-radius:999px;
                                 background:rgba(15,27,45,0.92);color:#e7eef8;text-decoration:none;
                                 border:1px solid rgba(255,255,255,0.14);font-size:12px;
                                 box-shadow:0 8px 22px rgba(0,0,0,0.25);">
                {label}
            </a>
        </div>
        '''


def nav_links_html(links):
        buttons = "".join(
                f'<a href="{href}" style="display:inline-block;margin:4px 6px 0 0;padding:8px 12px;'
                f'border-radius:999px;background:rgba(15,27,45,0.92);color:#e7eef8;text-decoration:none;'
                f'border:1px solid rgba(255,255,255,0.14);font-size:12px;box-shadow:0 8px 22px rgba(0,0,0,0.25);">{label}</a>'
                for label, href in links
        )
        return f'''
        <div style="position: fixed; top: 10px; left: 10px; z-index: 1100; max-width: calc(100vw - 20px);">
            {buttons}
        </div>
        '''


def ratio_legend_html(title: str = "Falchi 2015 - Světelné znečištění") -> str:
        return f'''
    <details style="position: fixed; bottom: 10px; right: 10px; z-index: 1000;
                                                background: rgba(255,255,255,0.94); padding: 10px 12px;
                                                border-radius: 10px; box-shadow: 0 0 5px rgba(0,0,0,0.25);
                                                font-size: 12px; max-width: min(290px, calc(100vw - 20px));">
            <summary style="cursor:pointer;font-weight:700;list-style:none;">{title}</summary>
            <table style="margin-top:8px;border-collapse:collapse;">
                <tr><td style="background:#000000;width:14px;height:12px;"></td><td style="padding-left:8px;">≤1%</td></tr>
                <tr><td style="background:#808080;width:14px;height:12px;"></td><td style="padding-left:8px;">1-2%</td></tr>
                <tr><td style="background:#A9A9A9;width:14px;height:12px;"></td><td style="padding-left:8px;">2-4%</td></tr>
                <tr><td style="background:#00008B;width:14px;height:12px;"></td><td style="padding-left:8px;">4-8%</td></tr>
                <tr><td style="background:#0000FF;width:14px;height:12px;"></td><td style="padding-left:8px;">8-16%</td></tr>
                <tr><td style="background:#444AF8;width:14px;height:12px;"></td><td style="padding-left:8px;">16-32%</td></tr>
                <tr><td style="background:#006400;width:14px;height:12px;"></td><td style="padding-left:8px;">32-64%</td></tr>
                <tr><td style="background:#008000;width:14px;height:12px;"></td><td style="padding-left:8px;">64-128%</td></tr>
                <tr><td style="background:#FFFF00;width:14px;height:12px;"></td><td style="padding-left:8px;">>128%</td></tr>
            </table>
        </details>
        '''