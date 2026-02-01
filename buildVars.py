# Build customizations
# Change this file instead of SConstruct or manifest files, whenever possible.

from site_scons.site_tools.NVDATool.typings import AddonInfo, BrailleTables, SymbolDictionaries
from site_scons.site_tools.NVDATool.utils import _

addon_info = AddonInfo(
	# Add-on Name/identifier, internal for NVDA (must match addon/manifest.ini "name")
	addon_name="calendario_simples_BR",
	# Translators: Summary/title for this add-on to be shown on installation and in the add-on store
	addon_summary=_("Calendário Simples BR"),
	# Translators: Long description to be shown for this add-on in the add-on store
	addon_description=_(
		"""Este complemento oferece um calendário simples e acessível para o NVDA.
		Permite navegar por dias, semanas, meses e anos com atalhos de teclado, anunciando as datas de forma clara e rápida."""
	),
	# Version (major.minor.patch) - required by the NV Access add-on store
	addon_version="2026.02.01",
	# Translators: what's new content for the add-on version to be shown in the add-on store
	addon_changelog=_(
		"""Primeira versão pública do Calendário Simples BR.
		Inclui item no menu Ferramentas e atalho NVDA+Shift+C para abrir o calendário."""
	),
	addon_author="Leandro Souza",
	addon_url="https://github.com/leandro-sds/calendario_simples_BR/",
	addon_sourceURL="https://github.com/leandro-sds/calendario_simples_BR",
	addon_docFileName="readme.html",
	addon_minimumNVDAVersion="2024.1",
	addon_lastTestedNVDAVersion="2025.3.2",
	addon_updateChannel=None,
	addon_license="GPL-2.0-only",
	addon_licenseURL=None,
)

pythonSources: list[str] = [
	"addon/globalPlugins/calendario_simples_BR.py",
]

i18nSources: list[str] = pythonSources + ["buildVars.py"]

# Files ignored when building the nvda-addon (paths are relative to the addon directory)
excludedFiles: list[str] = [
	"**/__pycache__",
	"**/__pycache__/*",
	"**/*.pyc",
	"**/*.pyo",
	"**/*.bak",
	"**/.DS_Store",
]

# Base language for the NVDA add-on (folder name under addon/doc and addon/locale)
baseLanguage: str = "pt_BR"

markdownExtensions: list[str] = []

brailleTables: BrailleTables = {}
brailleTableDisplayNames: dict[str, str] = {}

symbolDictionaries: SymbolDictionaries = {}
symbolDictionaryDisplayNames: dict[str, str] = {}
