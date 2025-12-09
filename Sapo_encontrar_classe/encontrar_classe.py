def run():

    import os
    import sys

    # Caminho da pasta de libs dentro do plugin
    plugin_dir = os.path.dirname(__file__)
    sys.path.append(os.path.join(plugin_dir))
    libs_path = os.path.join(plugin_dir, "libs")
    if libs_path not in sys.path:
        sys.path.insert(0, libs_path)
    
    import pandas as pd
    from fuzzywuzzy import process #from rapidfuzz import process
    from qgis.core import QgsProject, QgsVectorLayer, QgsWkbTypes, QgsDefaultValue
    from PyQt5.QtGui import QMovie, QIcon
    from qgis.PyQt.QtWidgets import QTableWidget, QTableWidgetItem, QHBoxLayout, QWidget, QMessageBox, QDialog, QLineEdit, QPushButton, QVBoxLayout, QLabel
    from qgis.utils import iface
    from qgis.PyQt.QtCore import Qt, QSize
    from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QDialog, QVBoxLayout, QComboBox, QStyleFactory

    

    #Retornar nomes csv
    def listar_csv_lista_classes(plugin_dir):
        """
        Retorna uma lista com o nome de todos os arquivos .csv
        dentro da pasta 'lista_classes' localizada no plugin.
        """
        pasta = os.path.join(plugin_dir, "lista_classes")
        if not os.path.exists(pasta):
            return []  # pasta não existe
        arquivos_csv = [
            os.path.splitext(f)[0] for f in os.listdir(pasta)
            if f.lower().endswith(".csv") and os.path.isfile(os.path.join(pasta, f))
        ]
        return arquivos_csv

    #função de set atributo
    def set_atributos_default_tipo(layer, code_value):
        try:
            # Definir o índice da coluna 'tipo'
            tipo_idx = layer.fields().indexFromName('tipo')
            # Definir a expressão para o valor padrão
            default_value_expression = "'"+str(code_value)+"'"
            # Definir o valor padrão da coluna 'tipo' como '1310' por exemplo
            layer.setDefaultValueDefinition(tipo_idx, QgsDefaultValue(default_value_expression))
            # Aplicar as configurações
            layer.updateFields()

        except Exception as e:
            # Em caso de erro, você pode adicionar algum tratamento de erro aqui se desejar
            print(f"Ocorreu um erro: {str(e)}")

    # Função para localizar a camada, iniciar a edição e abrir a ferramenta de aquisição
    def locate_and_edit_layer(c, dialog):
        layer_name = c[0]
        code_value = c[1]

        # Remove a seleção de todas as camadas
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                layer.removeSelection()

        # Localizar a camada no projeto
        layers = QgsProject.instance().mapLayersByName(layer_name)

        if layers:
            layer = layers[0]
            # Verificar se é uma camada vetorial
            if isinstance(layer, QgsVectorLayer):
                # Selecionar a camada no painel de camadas
                iface.setActiveLayer(layer)

                # Iniciar modo de edição da camada, se ainda não estiver
                if not layer.isEditable():
                    layer.startEditing()

                # Verificar o tipo de geometria da camada
                geometry_type = layer.geometryType()

                # Habilitar a ferramenta de adição de feições de acordo com o tipo de geometria
                if geometry_type == QgsWkbTypes.PointGeometry:
                    iface.actionAddFeature().trigger()
                    #QMessageBox.information(None, "Info", f"Camada '{layer_name}' identificada como ponto. Ferramenta de adicionar feição (ponto) habilitada.")
                elif geometry_type == QgsWkbTypes.LineGeometry:
                    iface.actionAddFeature().trigger()
                    #QMessageBox.information(None, "Info", f"Camada '{layer_name}' identificada como linha. Ferramenta de adicionar feição (linha) habilitada.")
                elif geometry_type == QgsWkbTypes.PolygonGeometry:
                    iface.actionAddFeature().trigger()
                    #QMessageBox.information(None, "Info", f"Camada '{layer_name}' identificada como polígono. Ferramenta de adicionar feição (polígono) habilitada.")
                else:
                    QMessageBox.warning(None, "Alerta", "Tipo de geometria desconhecido ou não suportado.")
                    
                set_atributos_default_tipo(layer, code_value)

                # Fechar o diálogo após habilitar a ferramenta
                dialog.accept()
        else:
            QMessageBox.warning(None, "Alerta", f"Camada '{layer_name}' não encontrada no projeto.")

    def center_column(table_widget, col_index):
        for row in range(table_widget.rowCount()):
            item = table_widget.item(row, col_index)
            if item:
                item.setTextAlignment(Qt.AlignCenter)

    # Função para mostrar os resultados em um layout de tabela
    def show_table(data, lista_et):
        dialog = QDialog()
        layout = QVBoxLayout()

        table = QTableWidget()
        table.setRowCount(len(data))
        table.setColumnCount(5)  # Adicionando colunas extras para os botões de ação
        table.setHorizontalHeaderLabels(['Palavra', '%', 'Code', 'Classe', 'Ações'])

        for i, (word, score, code, classe, tipo_geometria) in enumerate(data):
            table.setItem(i, 0, QTableWidgetItem(str(word)))
            table.setItem(i, 1, QTableWidgetItem(str(score)))
            table.setItem(i, 2, QTableWidgetItem(str(code)))
            table.setItem(i, 3, QTableWidgetItem(str(classe)))
            #table.setItem(i, 4, QTableWidgetItem(str(tipo_geometria)))

            # Criar o layout de botões para cada tipo de geometria
            button_layout = QHBoxLayout()

            # Botões para cada tipo de geometria (Ponto, Linha, Polígono)
            btn_ponto = QPushButton('P')
            btn_linha = QPushButton('L')
            btn_poligono = QPushButton('A')

            # Conectar os botões à função, passando a classe e o tipo de geometria
            btn_ponto.clicked.connect(lambda _, c=(str(classe)+"_p", str(code)): locate_and_edit_layer(c, dialog))
            btn_linha.clicked.connect(lambda _, c=(str(classe)+"_l", str(code)): locate_and_edit_layer(c, dialog))
            btn_poligono.clicked.connect(lambda _, c=(str(classe)+"_a", str(code)) : locate_and_edit_layer(c, dialog))

            estilo_bt = """
                QPushButton {
                    font-size: 14px;
                    font-weight: bold;
                    color: white;
                    background-color: #4CAF50; /* Cor de fundo */
                    border: none;
                    padding: 5px;
                    border-radius: 15px;
                }
                QPushButton:hover {
                    background-color: #45A049; /* Cor quando o mouse estiver sobre o botão */
                }
                QPushButton:pressed {
                    background-color: #2E7D32; /* Cor quando o botão estiver pressionado */
                }
            """

            estilo_bt_disable = """
                QPushButton {
                    font-size: 14px;
                    font-weight: bold;
                    border: none;
                    padding: 5px;
                    border-radius: 15px;
                }
            """

            # Desabilitar botões de acordo com o tipo de geometria
            if 'p' not in tipo_geometria:
                btn_ponto.setDisabled(True)
                btn_ponto.setStyleSheet(estilo_bt_disable)
            else:
                btn_ponto.setStyleSheet(estilo_bt)
                btn_ponto.setCursor(Qt.PointingHandCursor)

            if 'l' not in tipo_geometria:
                btn_linha.setDisabled(True)
                btn_linha.setStyleSheet(estilo_bt_disable)
            else:
                btn_linha.setStyleSheet(estilo_bt)
                btn_linha.setCursor(Qt.PointingHandCursor)

            if 'a' not in tipo_geometria:
                btn_poligono.setDisabled(True)
                btn_poligono.setStyleSheet(estilo_bt_disable)
            else:
                btn_poligono.setStyleSheet(estilo_bt)
                btn_poligono.setCursor(Qt.PointingHandCursor)

            # Adicionar os botões ao layout de botões
            button_layout.addWidget(btn_ponto)
            button_layout.addWidget(btn_linha)
            button_layout.addWidget(btn_poligono)

            # Criar um widget para conter o layout de botões e adicioná-lo à célula
            widget = QWidget()
            widget.setLayout(button_layout)
            table.setCellWidget(i, 4, widget)

        # Ajustar o tamanho do diálogo ao conteúdo da tabela
        table.resizeColumnsToContents()
        table.resizeRowsToContents()

        # Definindo largura fixa das colunas
        table.setColumnWidth(0, 300)
        table.setColumnWidth(1, 50)
        table.setColumnWidth(2, 50)
        table.setColumnWidth(3, 200)
        table.setColumnWidth(4, 150)

        # Aplicando alinhamento centralizado
        center_column(table, 1)
        center_column(table, 2)
        center_column(table, 3)

        # Obtendo a largura total da tabela
        total_width = sum(table.columnWidth(col) for col in range(table.columnCount()))
        header_width = table.horizontalHeader().height()  # Altura dos cabeçalhos das colunas
        total_width += header_width + 25

        # Obtendo a altura total da tabela
        total_height = sum(table.rowHeight(row) for row in range(table.rowCount()))
        header_height = table.verticalHeader().width()  # Largura dos cabeçalhos das linhas
        total_height += header_height + 35

        # Definir o tamanho mínimo e máximo do diálogo
        #screen = QApplication.primaryScreen()
        #screen_geometry = screen.availableGeometry()
        #screen_width = screen_geometry.width()
        #screen_height = screen_geometry.height()
        # Centralizar o diálogo na tela
        #dialog.move(int(screen_width * 0.1), int(screen_height * 0.1))

        # Ajustar o tamanho do diálogo com base no tamanho da tabela
        dialog.setMinimumWidth(total_width)
        dialog.setMinimumHeight(total_height)
        dialog.setMaximumWidth(total_width)
        dialog.setMaximumHeight(total_height)

        #####
        #input_field = QLineEdit(dialog)
        #input_field.setPlaceholderText(str(total_width)+" "+str(total_height))
        #layout.addWidget(input_field)  

        layout.addWidget(table)
        dialog.setLayout(layout)
        dialog.setWindowTitle(f"Resultados da Busca ({lista_et})")
        dialog.exec_()
    
    #EXECUTAR

    # Criar um diálogo personalizado
    dialog = QDialog()
    dialog.setWindowTitle(f"Encontrar Classe")
    layout = QVBoxLayout(dialog)

    # Adicionar a imagem ico.png acima do campo de busca
    #image_label = QLabel(dialog)
    #pixmap = QPixmap(os.path.join(self.plugin_dir, 'ico.png'))  # Certifique-se de que o caminho esteja correto
    #pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    #image_label.setPixmap(pixmap)
    #image_label.setAlignment(Qt.AlignCenter)  # Centralizar a imagem

    # Adicionar GIF animado
    gif_label = QLabel()
    gif = QMovie(os.path.join(plugin_dir, "img/sapo_reambulador_digitando_video.gif"))  # Certifique-se de ter um GIF na pasta do plugin
    gif_label.setMovie(gif)

    gif.setScaledSize(QSize(250, 250))
    gif_label.setFixedSize(250, 250)  # Ajuste o tamanho do GIF conforme necessário
    gif_label.setAlignment(Qt.AlignCenter)
    gif.start()

    # Adicionar campo de entrada de select 
    select_input = QComboBox(dialog)
    select_input.addItems(listar_csv_lista_classes(plugin_dir))
    select_input.setStyle(QStyleFactory.create("Fusion"))
    select_input.setStyleSheet("""
        QComboBox {
            font-size: 14px;
            padding-right: 30px;  /* espaço para a seta */
            border: 2px solid #4CAF50;
            border-radius: 10px;
            background-color: #F0F0F0;
            padding: 6px;
            color: black;
        }

        /* Área da seta */
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 28px;
            border: none;
        }

        /* Ícone da seta */
        QComboBox::down-arrow {
            image: url(":/img/img/seta_baixo.svg");
            width: 24px;
            height: 24px;
        }                    

        /* Lista de opções */
        QComboBox QAbstractItemView {
            background-color: #F0F0F0;
            color: black;
            selection-background-color: #66AFE9;
            selection-color: white;
            border: 2px solid #66AFE9;
            border-radius: 10px;
            padding: 6px;
        }                               
    """)      

    # Adicionar campo de entrada de texto
    input_field = QLineEdit(dialog)
    input_field.setPlaceholderText("Digite a palavra ou parte dela:")
    input_field.setStyleSheet("""
        QLineEdit {
            font-size: 14px;
            padding: 8px;
            border: 2px solid #4CAF50; /* Cor da borda */
            border-radius: 10px;
            background-color: #F0F0F0;
        }
        QLineEdit:focus {
            border: 2px solid #66AFE9; /* Cor da borda quando focado */
            background-color: #FFFFFF;
        }
    """)
    input_field.setFocus()

    # Botão para confirmar a busca estilizado
    search_button = QPushButton("Encontrar", dialog)

    # Estilizar o botão com QSS
    search_button.setStyleSheet("""
        QPushButton {
            font-size: 16px;
            font-weight: bold;
            color: white;
            background-color: #4CAF50; /* Cor de fundo */
            border: none;
            padding: 10px;
            border-radius: 15px;
        }
        QPushButton:hover {
            background-color: #45A049; /* Cor quando o mouse estiver sobre o botão */
        }
        QPushButton:pressed {
            background-color: #2E7D32; /* Cor quando o botão estiver pressionado */
        }
    """)
    search_button.setCursor(Qt.PointingHandCursor)

    # Adicionar widgets ao layout
    layout.addWidget(gif_label)      # Adiciona a imagem acima
    layout.addWidget(select_input)   
    layout.addWidget(input_field)     # Campo de entrada de texto
    layout.addWidget(search_button)    # Botão de buscar

    # Função para executar a busca quando o botão for clicado
    def on_search():

        # Carregar o CSV
        especificacao_tecnica = select_input.currentText()
        FIND_CLASSE_APP_LISTA = f'lista_classes/{especificacao_tecnica}.csv'
        file_path = os.path.join(plugin_dir, FIND_CLASSE_APP_LISTA)
        if not os.path.exists(file_path):
            QMessageBox.warning(None, "Alerta", f"Especificação Técnica: {especificacao_tecnica} Não Existe.")
            return
        
        df = pd.read_csv(file_path)

        search_word = input_field.text()
        if search_word:
            # Usar fuzzy matching para buscar palavras similares
            def match_word(search_term, choices):
                matches = process.extract(search_term, choices, limit=5)
                return matches

            # Lista de possíveis correspondências (colunas onde você quer buscar a palavra)
            code_name_choices = df['code_name'].tolist()
            filter_choices = df['filter'].tolist()
            tabela_choices = df['tabela'].tolist()

            # Obter os melhores matches para cada coluna
            code_name_matches = match_word(search_word, code_name_choices)
            filter_matches = match_word(search_word, filter_choices)
            tabela_matches = match_word(search_word, tabela_choices)

            # Preparar os dados para exibir na tabela
            table_data = []
            for word, score in code_name_matches:
                row = df[df['code_name'] == word]
                if not row.empty:
                    classe = row['foreign_table'].values[0]  # Nome da coluna da classe
                    tipo_geometria = row['tipo_geometria'].values[0]  # Nome da coluna do tipo de geometria
                    code = row['code'].values[0]
                    table_data.append((word, score, code, classe, tipo_geometria))

            for word, score in filter_matches:
                if (word, score) not in [x[:2] for x in table_data]:
                    row = df[df['filter'] == word]
                    if not row.empty:
                        classe = row['foreign_table'].values[0]  # Nome da coluna da classe
                        tipo_geometria = row['tipo_geometria'].values[0]  # Nome da coluna do tipo de geometria
                        code = row['code'].values[0]
                        table_data.append((word, score, code, classe, tipo_geometria))

            for word, score in tabela_matches:
                if (word, score) not in [x[:2] for x in table_data]:
                    row = df[df['tabela'] == word]
                    if not row.empty:
                        classe = row['foreign_table'].values[0]  # Nome da coluna da classe
                        tipo_geometria = row['tipo_geometria'].values[0]  # Nome da coluna do tipo de geometria
                        code = row['code'].values[0]
                        table_data.append((word, score, code, classe, tipo_geometria))

            # Fechar o diálogo após a busca
            dialog.accept()

            # Exibir os resultados na tabela
            show_table(table_data, especificacao_tecnica)

    # Conectar o botão à função de busca
    search_button.clicked.connect(on_search)
    dialog.setLayout(layout)
    dialog.exec_()