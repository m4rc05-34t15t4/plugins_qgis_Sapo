# __init__.py
def classFactory(iface):
    from .plugin import Plugin
    return Plugin(iface)
