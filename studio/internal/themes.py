"""Complete Fusion palettes; follow the OS until the user chooses a theme."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


def apply_theme(mode, highlighter):
    app = QApplication.instance()
    dark = mode == 'dark' or (mode == 'system' and
        app.styleHints().colorScheme() == Qt.ColorScheme.Dark)
    colors = (['#20242a', '#e6e9ee', '#16191e', '#292e36', '#343b46', '#88bcff', '#376bb2']
              if dark else
              ['#f1f3f5', '#202630', '#ffffff', '#e8edf3', '#e5e9ee', '#215da3', '#2868b0'])
    window, text, base, alternate, button, link, highlight = colors
    palette = QPalette()
    for role, color in {'Window': window, 'WindowText': text, 'Base': base,
        'AlternateBase': alternate, 'Text': text, 'Button': button, 'ButtonText': text,
        'ToolTipBase': base, 'ToolTipText': text, 'Link': link, 'Highlight': highlight,
        'HighlightedText': '#ffffff', 'PlaceholderText': '#8c97a5' if dark else '#606b79',
        'Light': '#505a68' if dark else '#ffffff', 'Mid': '#46505d' if dark else '#b9c1cb',
        'Dark': '#111418' if dark else '#8995a4', 'BrightText': '#ffffff'}.items():
        palette.setColor(getattr(QPalette.ColorRole, role), QColor(color))
    for role in ('Text', 'WindowText', 'ButtonText'):
        palette.setColor(QPalette.ColorGroup.Disabled, getattr(QPalette.ColorRole, role),
                         QColor('#7f8895' if dark else '#818995'))
    app.setPalette(palette)
    app.setStyleSheet('QPushButton { padding:5px 8px; } QTabBar::tab { padding:8px 10px; }')
    highlighter.dark = dark
    highlighter.rehighlight()
    return dark
