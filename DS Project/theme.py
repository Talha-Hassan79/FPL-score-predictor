import json

class Theme:
    """Simple theme manager for light and dark modes.
    Provides color lookups and a toggle method.
    """
    _palettes = {
        "light": {
            "BG": "#F5F5F5",
            "SURFACE": "#FFFFFF",
            "CARD": "#FFFFFF",
            "CARD2": "#F0F0F0",
            "BORDER": "#D1D5DB",
            "BORDER2": "#E5E7EB",
            "TEXT_PRI": "#111827",
            "TEXT_SEC": "#374151",
            "TEXT_MUT": "#6B7280",
            "ACCENT": "#3B82F6",
            "ACCENT_DIM": "#BFDBFE",
            "SUCCESS": "#10B981",
            "SUCCESS_DIM": "#D1FAE5",
        },
        "dark": {
            "BG": "#0D0F14",
            "SURFACE": "#13161F",
            "CARD": "#181C28",
            "CARD2": "#1E2235",
            "BORDER": "#252A3A",
            "BORDER2": "#2E3448",
            "TEXT_PRI": "#F0F2FF",
            "TEXT_SEC": "#6B7280",
            "TEXT_MUT": "#374151",
            "ACCENT": "#6366F1",
            "ACCENT_DIM": "#2D2F6B",
            "SUCCESS": "#10B981",
            "SUCCESS_DIM": "#0C3B2E",
        },
    }
    _current = "dark"

    @classmethod
    def get(cls, key: str) -> str:
        """Return the color value for the current theme.
        If the key does not exist, raise KeyError.
        """
        return cls._palettes[cls._current][key]

    @classmethod
    def toggle(cls):
        """Switch between light and dark themes.
        After toggling, callers should refresh UI elements.
        """
        cls._current = "light" if cls._current == "dark" else "dark"

    @classmethod
    def current_palette(cls) -> dict:
        """Return the full palette dictionary for the active theme."""
        return cls._palettes[cls._current]
