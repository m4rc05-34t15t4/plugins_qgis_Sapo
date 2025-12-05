# plugin.py
import os
from qgis.PyQt.QtWidgets import QAction, QToolBar
from qgis.PyQt.QtGui import QIcon

from .encontrar_classe import run

class Plugin:

    def __init__(self, iface):
        """Construtor do plugin."""
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.toolbar = None
        self.action_run = None

    def initGui(self):
        """Inicializa o plugin e adiciona botão na toolbar."""

        # 🔍 PROCURA se a toolbar "Sapo Plugin" já existe
        for tb in self.iface.mainWindow().findChildren(QToolBar):
            if tb.windowTitle() == "Sapo Plugin":
                self.toolbar = tb
                break

        # 🟢 Se não existe, cria
        if not self.toolbar:
            self.toolbar = QToolBar("Sapo Plugin")
            self.toolbar.setStyleSheet("""
                QToolBar {
                    background-color: #90EE90;
                    border: 2px solid #32CD32;
                    padding: 5px;
                }
            """)
            self.iface.addToolBar(self.toolbar)

        # Criar botão do plugin
        icon_action_run = os.path.join(self.plugin_dir, 'icon.png')
        self.action_run = QAction(QIcon(icon_action_run), "Encontrar Classe", self.iface.mainWindow())
        self.action_run.triggered.connect(self.run_script)

        # Adicionar o botão à toolbar
        self.toolbar.addAction(self.action_run)

    def unload(self):
        """Remove o plugin ao desinstalar."""
        if self.toolbar and self.action_run:
            self.toolbar.removeAction(self.action_run)

    def run_script(self):
        """Executa o script externo."""
        run()