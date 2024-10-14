import platform


if 'Windows' in platform.platform():
    defaultfont = 'Arial'
else:
    defaultfont = 'Monospace'

defaults = {
    'FONT': defaultfont,
    'FONTSIZE': 12,
    'ALIGNMENT': 'w',
    'COLUMNWIDTH': 80,
    'TIMEFORMAT': '%m/%d/%Y',
    'PRECISION': 3,
    'SHOWPLOTTER': True,
    'ICONSIZE': 26,
    'PLOTSTYLE': 'bmh',
    'DPI': 100,
    'BGCOLOR': '#F4F4F3',
    'THEME': 'Fusion'
}
