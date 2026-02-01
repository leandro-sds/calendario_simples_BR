
import gettext
from pathlib import Path
try:
	import markdown as _markdown
except Exception:  # pragma: no cover
	_markdown = None

def _renderMarkdown(mdText: str, mdExtensions: list[str]) -> str:
	"""Render Markdown to HTML.

	The official template uses the 'markdown' package (Python-Markdown).
	For local builds where it isn't installed, we fall back gracefully:
	- Try 'markdown2' if available
	- Otherwise, wrap plain text in a <pre> block
	"""
	if _markdown is not None:
		return _markdown.markdown(mdText, extensions=mdExtensions)

	try:
		import markdown2  # type: ignore
		# markdown2 uses different extension naming; keep extras empty if unknown.
		return str(markdown2.markdown(mdText))
	except Exception:
		import html
		return f"<pre>{html.escape(mdText)}</pre>"

from .typings import AddonInfo



def md2html(
		source: str | Path,
		dest: str | Path,
		*,
		moFile: str | Path|None,
		mdExtensions: list[str],
		addon_info: AddonInfo
	):
	if isinstance(source, str):
		source = Path(source)
	if isinstance(dest, str):
		dest = Path(dest)
	if isinstance(moFile, str):
		moFile = Path(moFile)

	try:
		with moFile.open("rb") as f:
			_ = gettext.GNUTranslations(f).gettext
	except Exception:
		summary = addon_info["addon_summary"]
	else:
		summary = _(addon_info["addon_summary"])
	version = addon_info["addon_version"]
	title = f"{summary} {version}"
	lang = source.parent.name.replace("_", "-")
	headerDic = {
		'[[!meta title="': "# ",
		'"]]': " #",
	}
	with source.open("r", encoding="utf-8") as f:
		mdText = f.read()
	for k, v in headerDic.items():
		mdText = mdText.replace(k, v, 1)
	htmlText = _renderMarkdown(mdText, mdExtensions)
	# Optimization: build resulting HTML text in one go instead of writing parts separately.
	docText = "\n".join(
		(
			"<!DOCTYPE html>",
			f'<html lang="{lang}">',
			"<head>",
			'<meta charset="UTF-8">',
			'<meta name="viewport" content="width=device-width, initial-scale=1.0">',
			'<link rel="stylesheet" type="text/css" href="../style.css" media="screen">',
			f"<title>{title}</title>",
			"</head>\n<body>",
			htmlText,
			"</body>\n</html>",
		)
	)
	with dest.open("w", encoding="utf-8") as f:
		f.write(docText) # type: ignore
