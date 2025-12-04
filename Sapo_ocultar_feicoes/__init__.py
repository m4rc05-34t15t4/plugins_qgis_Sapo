# __init__.py
def classFactory(iface):
    from .plugin import SapoPlugin_ocultar_feicoes
    return SapoPlugin_ocultar_feicoes(iface)
