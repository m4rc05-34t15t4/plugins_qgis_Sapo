def run():
    from qgis.PyQt.QtWidgets import (
        QDialog, QVBoxLayout, QLabel, QComboBox, QLineEdit,
        QCheckBox, QPushButton, QHBoxLayout, QProgressBar
    )
    from qgis.PyQt.QtCore import QCoreApplication
    from qgis.core import Qgis
    from PyQt5.QtGui import QPixmap
    from PyQt5.QtCore import Qt
    from qgis.PyQt.QtWidgets import QMessageBox
    import os

    class ConfigDialog(QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Ocultar Feições Sobrepostas")
            self.setMinimumWidth(320)

            self.valores_confirmados = False  # flag para saber se o usuário confirmou

            layout = QVBoxLayout()

            # --------------- LOGO -----------------
            logo_label = QLabel()
            caminho_logo = os.path.join(os.path.dirname(__file__), "icon.png")
            pixmap = QPixmap(caminho_logo)

            # Ajuste opcional de tamanho
            pixmap = pixmap.scaledToWidth(200)  
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)

            layout.addWidget(logo_label)

            # --- CAMADA REFERÊNCIA ---
            layout.addWidget(QLabel("Camada de referência:"))
            self.input_camada = QLineEdit()
            self.input_camada.setText("constr_edificacao_p")
            layout.addWidget(self.input_camada)

            # --- SELECT DE ESCALA ---
            layout.addWidget(QLabel("Selecione a escala:"))
            self.combo_escala = QComboBox()
            self.combo_escala.addItems(["25k", "50k", "100k", "250k"])
            layout.addWidget(self.combo_escala)

            # --- CHECKBOXES ---
            self.check_visivel_null = QCheckBox("Resetar atributo visivel para null")
            self.check_visivel_null.setChecked(False)   # valor padrão
            layout.addWidget(self.check_visivel_null)

            self.check_priorizar = QCheckBox("Priorizar visibilidade das camadas com nome")
            self.check_priorizar.setChecked(True)   # valor padrão
            layout.addWidget(self.check_priorizar)

            self.check_remover_temp = QCheckBox("Remover camadas temporárias")
            self.check_remover_temp.setChecked(True)
            layout.addWidget(self.check_remover_temp)

            # --- BARRA DE PROGRESSO ---
            self.barra = QProgressBar()
            self.barra.setVisible(False)  # inicia escondida
            layout.addWidget(self.barra)

            # --- BOTÕES OK / CANCELAR ---
            btn_layout = QHBoxLayout()
            self.btn_ok = QPushButton("OK")
            self.btn_ok.setAutoDefault(False)
            self.btn_cancel = QPushButton("Cancelar")
            btn_layout.addWidget(self.btn_ok)
            btn_layout.addWidget(self.btn_cancel)
            layout.addLayout(btn_layout)

            self.setLayout(layout)

            # --- CONEXÕES ---
            self.btn_ok.clicked.connect(self.confirmar)
            self.btn_cancel.clicked.connect(self.reject)
        
        def confirmar(self):
            """Pega os valores e mantém o diálogo aberto."""
            self.valores_confirmados = True
            # NÃO chama accept(), então a janela não fecha

        # Função para iniciar a barra
        def iniciar_barra(self, total):
            self.barra.setMaximum(total)
            self.barra.setValue(0)
            self.barra.setVisible(True)

    # ➤ ABRIR O DIÁLOGO E OBTER OS VALORES
    dlg = ConfigDialog()
    dlg.show()

    # Aguarda o usuário clicar OK ou Cancelar
    while not dlg.valores_confirmados and dlg.isVisible():
        QCoreApplication.processEvents()

    if not dlg.valores_confirmados:
        #QMessageBox.information(None, "Cancelado", "Execução cancelada pelo usuário.")
        return
        #raise Exception("Execução cancelada pelo usuário.")

    # --- PEGANDO OS VALORES ---
    camada_referencia = dlg.input_camada.text() #"constr_edificacao_p"
    escala = dlg.combo_escala.currentText()
    priorizar_visibilidade_camadas_com_nome = dlg.check_priorizar.isChecked()
    remover_camadas_temporarias = dlg.check_remover_temp.isChecked()
    resetar_visibilidade = dlg.check_visivel_null.isChecked()
    #variavel valor do lado do quadrado da edificacao
    switch_valor_raio = { "25k": 17.5, "50k": 35.0, "100k": 70.0, "250k": 175.0 }
    raio = 0
    if(switch_valor_raio[escala]):
        raio = switch_valor_raio[escala]
    else:
        QMessageBox.information(None, "Cancelado", "Escala não definida.")
        return
        #raise Exception("Escala não definida.")
    
    #Deixar campo visivel null
    def campo_visivel_null():
        layer_name = camada_referencia
        field_name = "visivel"

        # Obter camada
        layer = QgsProject.instance().mapLayersByName(layer_name)
        if not layer:
            raise Exception(f"Camada '{layer_name}' não encontrada.")
        layer = layer[0]

        # Verifica se o campo existe
        if field_name not in [f.name() for f in layer.fields()]:
            raise Exception(f"O campo '{field_name}' não existe na camada.")

        # Começar edição
        if not layer.isEditable():
            layer.startEditing()

        # Se houver seleção, usa apenas selecionadas. Caso contrário, todas.
        features = (
            layer.selectedFeatures() 
            if layer.selectedFeatureCount() > 0 
            else layer.getFeatures()
        )

        # Atualizar cada feição
        for feat in features:
            fid = feat.id()
            layer.changeAttributeValue(fid, layer.fields().indexFromName(field_name), None)

        # Salvar
        layer.commitChanges()

        print("Campo atualizado para NULL com sucesso!")


    from qgis.core import (
        QgsProject,
        QgsFeature,
        QgsVectorLayer,
        QgsGeometry,
        QgsPointXY,
        QgsField
    )
    from PyQt5.QtCore import QVariant
    import math

    # =========================================================
    # 1️⃣ GERAR BUFFERS QUADRADOS ROTACIONADOS
    # =========================================================
    def gerar_buffers_quadrados_rotacionados(layer_name='constr_edificacao_p', half=35.0, acrescimo_rot=90.0):
        layer_list = QgsProject.instance().mapLayersByName(layer_name)
        if not layer_list:
            QMessageBox.critical(None, "Erro", f"Camada '{layer_name}' não encontrada.")
            return
            #raise Exception(f"Camada '{layer_name}' não encontrada.")
        layer = layer_list[0]

        crs = layer.crs().toWkt()
        out_layer = QgsVectorLayer(f"Polygon?crs={crs}", "buffer_quadrado_edificacao", "memory")
        prov = out_layer.dataProvider()

        prov.addAttributes(layer.fields())
        out_layer.updateFields()
        
        field_names = [f.name() for f in out_layer.fields()]
        
        # cria campo visibilidade se não existir
        if 'visibilidade' not in field_names:
            prov.addAttributes([QgsField('visibilidade', QVariant.Int)])
            out_layer.updateFields()

        if 'area_sobreposta' not in field_names:
            prov.addAttributes([QgsField('area_sobreposta', QVariant.Double)])
            out_layer.updateFields()
        
        # Adiciona campo id_ilha na camada de buffer, se não existir
        if 'id_ilha' not in field_names:
            prov.addAttributes([QgsField('id_ilha', QVariant.Int)])
            out_layer.updateFields()

        features_out = []

        for f in layer.getFeatures():
            geom = f.geometry()
            if geom is None or geom.isEmpty():
                continue

            try:
                pt = geom.asPoint()
            except Exception:
                continue

            x, y = pt.x(), pt.y()

            coords = [
                QgsPointXY(x - half, y - half),
                QgsPointXY(x + half, y - half),
                QgsPointXY(x + half, y + half),
                QgsPointXY(x - half, y + half),
                QgsPointXY(x - half, y - half)
            ]
            square = QgsGeometry.fromPolygonXY([coords])

            raw = f["simb_rot"] if "simb_rot" in f.fields().names() else None
            rot_value = None
            if raw not in [None, ""]:
                try:
                    rot_value = float(raw)
                    if math.isnan(rot_value):
                        rot_value = None
                except Exception:
                    rot_value = None

            if rot_value is not None:
                angle_deg = float(rot_value) + acrescimo_rot
                square.rotate(angle_deg, QgsPointXY(x, y))

            new_feat = QgsFeature(out_layer.fields())
            new_feat.setAttributes(f.attributes())
            new_feat.setGeometry(square)
            features_out.append(new_feat)

        prov.addFeatures(features_out)
        out_layer.updateExtents()
        QgsProject.instance().addMapLayer(out_layer)

        print(f"✅ {len(features_out)} buffers quadrados criados e rotacionados (+{acrescimo_rot}°).")
        return out_layer


    # =========================================================
    # 2️⃣ CALCULAR ÁREA SOBREPOSTA ENTRE FEIÇÕES
    # =========================================================
    from qgis.core import QgsProject, QgsVectorLayer
    def preencher_coluna_area_sobreposta(buffer_layer_name="buffer_quadrado_edificacao"):
        """
        Calcula a área sobreposta apenas para feições da camada
        cujo campo 'visibilidade' é NULL, 0 ou vazio.
        Preenche o campo 'area_sobreposta'.
        """

        # obtém camada
        layers = QgsProject.instance().mapLayersByName(buffer_layer_name)
        if not layers:
            QMessageBox.critical(None, "Erro", f"Camada '{buffer_layer_name}' não encontrada.")
            return
            #raise Exception(f"Camada '{buffer_layer_name}' não encontrada.")
        layer = layers[0]

        if not isinstance(layer, QgsVectorLayer):
            QMessageBox.critical(None, "Erro", "Parâmetro 'layer' deve ser uma QgsVectorLayer.")
            return
            #raise Exception("Parâmetro 'layer' deve ser uma QgsVectorLayer.")

        # verifica se o campo existe
        if 'area_sobreposta' not in [f.name() for f in layer.fields()]:
            layer.dataProvider().addAttributes([QgsField('area_sobreposta', QVariant.Double)])
            layer.updateFields()
        idx_area = layer.fields().indexFromName('area_sobreposta')
        #idx_vis = layer.fields().indexFromName('visibilidade')

        # seleciona apenas feições com visibilidade NULL, vazio ou 0
        feats_all = list(layer.getFeatures())
        feats = [f for f in feats_all if f['visibilidade'] in (None, 0, '', 1)]

        # === 🔄 ZERAR COLUNA ANTES DO CÁLCULO ===
        layer.startEditing()
        for f in feats:
            layer.changeAttributeValue(f.id(), idx_area, None)
        layer.commitChanges()

        total = len(feats)
        print(f"🔍 Calculando áreas sobrepostas para {total} feições incompletas...")

        if total == 0:
            print("✅ Todas as feições já possuem visibilidade preenchida. Nada a fazer.")
            return

        layer.startEditing()

        for i, f1 in enumerate(feats):
            geom1 = f1.geometry()
            area_total = 0.0

            for f2 in feats_all:
                if f1.id() == f2.id():
                    continue
                geom2 = f2.geometry()
                if geom1.intersects(geom2):
                    inter = geom1.intersection(geom2)
                    if inter and not inter.isEmpty():
                        area_total += inter.area()

            layer.changeAttributeValue(f1.id(), idx_area, round(area_total, 3))

            if i % 500 == 0 or i == total - 1:
                print(f"  → Processadas {i + 1}/{total}")

        layer.commitChanges()
        layer.updateExtents()
        print("✅ Coluna 'area_sobreposta' preenchida nas feições incompletas.")


    # =========================================================
    # 3️⃣ CRIAR ILHAS E ATRIBUIR ID
    # =========================================================
    from qgis.core import (
        QgsProject, QgsVectorLayer, QgsFeature, QgsField,
        QgsGeometry, QgsSpatialIndex, edit
    )
    from PyQt5.QtCore import QVariant

    def criar_ilhas_edificacoes(buffer_layer_name="buffer_quadrado_edificacao"):
        """
        Cria uma camada temporária com as ilhas (grupos de buffers conectados),
        considerando apenas feições com 'visibilidade' NULL, 0 ou vazio.
        Adiciona um campo 'id_ilha' na camada de buffer, indicando a qual
        ilha cada feição pertence.
        Retorna a camada temporária de ilhas.
        """

        # Obtém camada de buffer
        layers = QgsProject.instance().mapLayersByName(buffer_layer_name)
        if not layers:
            print(f"Camada '{buffer_layer_name}' não encontrada.")
            return None
        buffer_layer = layers[0]

        # Índices dos campos
        idx_vis = buffer_layer.fields().indexFromName('visibilidade')
        if 'id_ilha' not in [f.name() for f in buffer_layer.fields()]:
            buffer_layer.dataProvider().addAttributes([QgsField('id_ilha', QVariant.Int)])
            buffer_layer.updateFields()
        idx_id_ilha = buffer_layer.fields().indexFromName('id_ilha')

        # Todas as feições
        features_all = list(buffer_layer.getFeatures())

        # Filtra apenas feições com visibilidade NULL, 0 ou vazio
        features = [f for f in features_all if f[idx_vis] in (None, 0, '')]

        if not features:
            print("Nenhuma feição com visibilidade NULL, 0 ou vazia encontrada.")
            return None

        # Cria índice espacial corretamente
        index = QgsSpatialIndex()
        for f in features_all:
            index.insertFeature(f)

        visitados = set()
        ilha_id = 1
        ilha_features = []

        for f in features:
            fid = f.id()
            if fid in visitados:
                continue

            # BFS para agrupar feições conectadas
            grupo = set()
            fila = [f]
            while fila:
                atual = fila.pop()
                if atual.id() in grupo:
                    continue
                grupo.add(atual.id())
                visitados.add(atual.id())

                bbox_ids = index.intersects(atual.geometry().boundingBox())
                for vizinho_id in bbox_ids:
                    if vizinho_id == atual.id():
                        continue
                    vizinho = buffer_layer.getFeature(vizinho_id)
                    if vizinho[idx_vis] not in (None, 0, '', 1):
                        continue  # só considera vizinhos que também têm visibilidade NULL/0 e 1
                    if atual.geometry().intersects(vizinho.geometry()) and vizinho.id() not in grupo:
                        fila.append(vizinho)

            # Cria geometria unida da ilha
            geoms = [buffer_layer.getFeature(g).geometry() for g in grupo]
            geom_unida = geoms[0]
            for g in geoms[1:]:
                geom_unida = geom_unida.combine(g)

            # Explode multipolígonos
            partes = []
            if geom_unida.isMultipart():
                for part in geom_unida.asMultiPolygon():
                    partes.append(QgsGeometry.fromPolygonXY(part))
            else:
                partes.append(geom_unida)

            # Cria feições de ilha
            for parte in partes:
                ilha_feat = QgsFeature()
                ilha_feat.setGeometry(parte)
                ilha_feat.setAttributes([ilha_id])
                ilha_features.append(ilha_feat)

            # Atualiza id_ilha na camada de buffer
            if not buffer_layer.isEditable():
                buffer_layer.startEditing()
            for fid in grupo:
                buffer_layer.changeAttributeValue(fid, idx_id_ilha, ilha_id)

            ilha_id += 1

        if buffer_layer.isEditable():
            buffer_layer.commitChanges()

        # Cria camada temporária de ilhas
        ilha_layer = QgsVectorLayer(f"Polygon?crs={buffer_layer.crs().authid()}", "ilhas_edificacao", "memory")
        prov = ilha_layer.dataProvider()
        prov.addAttributes([QgsField("id_ilha", QVariant.Int)])
        ilha_layer.updateFields()
        prov.addFeatures(ilha_features)

        QgsProject.instance().addMapLayer(ilha_layer)
        print(f"Foram criadas {ilha_id - 1} ilhas (considerando apenas feições com visibilidade NULL/0/1).")
        return ilha_layer

    # =========================================================
    # 4️⃣ Definir visualização
    # =========================================================
    import math
    from qgis.core import QgsProject

    def definir_visibilidade_buffers(buffer_layer_name="buffer_quadrado_edificacao"):
        """
        Atualiza o campo 'visibilidade' apenas para feições que não têm valor 1 ou 2:
        - area_sobreposta == 0 → 1
        - ilha com apenas uma feição → 1
        - maior area_sobreposta (>0) por ilha → 2
        - todas as demais feições permanecem inalteradas
        """

        # pega camada
        layers = QgsProject.instance().mapLayersByName(buffer_layer_name)
        if not layers:
            print(f"Camada '{buffer_layer_name}' não encontrada.")
            return
        layer = layers[0]

        # verifica campos
        field_names = [f.name() for f in layer.fields()]
        if 'area_sobreposta' not in field_names or 'id_ilha' not in field_names:
            print("Erro: a camada precisa conter 'area_sobreposta' e 'id_ilha'.")
            return

        idx_area = layer.fields().indexFromName('area_sobreposta')
        idx_ilha = layer.fields().indexFromName('id_ilha')
        idx_vis = layer.fields().indexFromName('visibilidade')

        feats = list(layer.getFeatures())

        # filtra apenas feições com visibilidade diferente de 1 ou 2
        feats_filtradas = [f for f in feats if f['visibilidade'] not in (1, 2)]

        # agrupa feições por ilha (somente area_sobreposta >0)
        ilhas = {}
        for f in feats_filtradas:
            try:
                area = float(f['area_sobreposta']) if f['area_sobreposta'] is not None else None
                if area is None or math.isnan(area):
                    continue
            except:
                continue

            id_ilha = f['id_ilha']
            if id_ilha is not None:
                ilhas.setdefault(id_ilha, []).append((f, area))

        # inicia edição
        if not layer.isEditable():
            layer.startEditing()

        for id_ilha, lista in ilhas.items():
            if not lista:
                continue

            # se ilha tiver apenas uma feição → visibilidade = 1
            if len(lista) == 1:
                f_unica = lista[0][0]
                if f_unica['visibilidade'] not in (1, 2):
                    layer.changeAttributeValue(f_unica.id(), idx_vis, 1)
                    #layer.changeAttributeValue(f.id(), idx_ilha, 0)
                continue

            # 1️⃣ feições com area_sobreposta == 0 → visibilidade = 1
            for f, area in lista:
                if area == 0.0 and f['visibilidade'] not in (1, 2):
                    layer.changeAttributeValue(f.id(), idx_vis, 1)
                    #layer.changeAttributeValue(f.id(), idx_ilha, 0)

            # 2️⃣ maior area_sobreposta (>0) por ilha → visibilidade = 2
            lista_sorted = sorted(lista, key=lambda x: x[1], reverse=True)
            f_top = lista_sorted[0][0]
            if f_top['visibilidade'] not in (1, 2):
                layer.changeAttributeValue(f_top.id(), idx_vis, 2)
                #layer.changeAttributeValue(f.id(), idx_ilha, 0)

        layer.commitChanges()

        # seleciona apenas feições com visibilidade NULL, vazio ou 0
        feats_filtardas = [f for f in feats if f['visibilidade'] in (1, 2)]

        # === 🔄 ZERAR COLUNA ANTES DO CÁLCULO ===
        layer.startEditing()
        for f in feats_filtardas:
            layer.changeAttributeValue(f.id(), idx_ilha, None)
        layer.commitChanges()

    from qgis.core import QgsProject, QgsVectorLayer, QgsField
    from PyQt5.QtCore import QVariant

    def definir_visibilidade_por_nome(layer_name="buffer_quadrado_edificacao", definir=True):
        """
        Define o valor 1 no atributo 'visibilidade' para todas as feições
        onde o atributo 'nome' possui algum valor (não é NULL, vazio ou espaço).
        """
        if(definir):
            # obter camada
            layers = QgsProject.instance().mapLayersByName(layer_name)
            if not layers:
                QMessageBox.critical(None, "Erro", f"Camada '{layer_name}' não encontrada.")
                return
                #raise Exception(f"Camada '{layer_name}' não encontrada.")
            layer = layers[0]

            if not isinstance(layer, QgsVectorLayer):
                QMessageBox.critical(None, "Erro", "Parâmetro 'layer' deve ser uma QgsVectorLayer.")
                return
                #raise Exception("Parâmetro 'layer' deve ser uma QgsVectorLayer.")

            # valida campo 'nome'
            campos = [f.name() for f in layer.fields()]
            if 'nome' in campos and 'visibilidade' in campos:
                idx_nome = layer.fields().indexFromName('nome')
                idx_vis = layer.fields().indexFromName('visibilidade')

                # iniciar edição
                layer.startEditing()
                count = 0

                for feat in layer.getFeatures():
                    valor_nome = feat[idx_nome]

                    # se o nome tem conteúdo, seta visibilidade = 1
                    if valor_nome not in (None, '', ' '):
                        layer.changeAttributeValue(feat.id(), idx_vis, 1)
                        count += 1

                layer.commitChanges()
                print(f"✅ 'visibilidade' definido como 1 em {count} feições onde 'nome' possui valor.")



    # =========================================================
    # 5️⃣ Faz o loop das funções
    # =========================================================
    from qgis.core import QgsProject
    def loop_atualizar_visibilidade(buffer_layer_name="buffer_quadrado_edificacao"):
        """
        Executa em loop as funções:
        1️⃣ preencher_coluna_area_sobreposta
        2️⃣ criar_ilhas_edificacoes
        3️⃣ definir_visibilidade_buffers
        Apenas para feições que ainda têm visibilidade NULL, 0 ou vazia.
        O loop termina quando todas as feições tiverem visibilidade preenchida.
        Imprime a quantidade de feições da camada de ilhas a cada iteração.
        """

        # Pega camada
        layers = QgsProject.instance().mapLayersByName(buffer_layer_name)
        if not layers:
            print(f"Camada '{buffer_layer_name}' não encontrada.")
            return
        buffer_layer = layers[0]

        # Índice do campo visibilidade
        idx_vis = buffer_layer.fields().indexFromName('visibilidade')

        loop_count = 0
        barra_val = 3
        while True:
            # verifica se ainda existem feições com visibilidade NULL, 0 ou vazia
            feats = list(buffer_layer.getFeatures())
            faltando = [f for f in feats if f[idx_vis] in (None, 0, '')]
            if not faltando:
                print("✅ Todas as feições já possuem visibilidade preenchida!")
                break

            loop_count += 1
            print(f"\n🔄 Iteração {loop_count}, feições pendentes: {len(faltando)}")

            # 2️⃣ Calcula a área sobreposta
            preencher_coluna_area_sobreposta(buffer_layer_name)

            # 3️⃣ Cria as ilhas e adiciona id_ilha
            ilha_layer = criar_ilhas_edificacoes(buffer_layer_name)
            if ilha_layer:
                print(f"Camada de ilhas criada com {ilha_layer.featureCount()} feições.")

            # 4️⃣ Definir visibilidade
            definir_visibilidade_buffers(buffer_layer_name)

            #set a barra de progresso
            
            if barra_val <= 21:
                barra_val += 3
                dlg.barra.setValue(barra_val)
                QCoreApplication.processEvents()

        print(f"\nLoop finalizado após {loop_count} iterações.")
        

    # =========================================================
    # 6️⃣ Passar os valores para a camaa original
    # =========================================================
    from qgis.core import QgsProject, QgsField, edit

    def copiar_visibilidade_para_camada(dest_layer_name, buffer_layer_name="buffer_quadrado_edificacao"):
        """
        Copia o valor do atributo 'visibilidade' da camada buffer_layer_name
        para a camada dest_layer_name na coluna 'visivel', usando o campo 'id' em comum.
        """

        # pega camada de destino
        dest_layers = QgsProject.instance().mapLayersByName(dest_layer_name)
        if not dest_layers:
            print(f"Camada '{dest_layer_name}' não encontrada.")
            return
        dest_layer = dest_layers[0]

        # pega camada de buffer
        buffer_layers = QgsProject.instance().mapLayersByName(buffer_layer_name)
        if not buffer_layers:
            print(f"Camada '{buffer_layer_name}' não encontrada.")
            return
        buffer_layer = buffer_layers[0]

        # verifica campos
        if 'id' not in [f.name() for f in dest_layer.fields()]:
            print(f"Erro: camada '{dest_layer_name}' precisa ter o campo 'id'.")
            return
        if 'id' not in [f.name() for f in buffer_layer.fields()] or 'visibilidade' not in [f.name() for f in buffer_layer.fields()]:
            print(f"Erro: camada '{buffer_layer_name}' precisa ter os campos 'id' e 'visibilidade'.")
            return

        # cria dicionário id → visibilidade
        vis_dict = {f['id']: f['visibilidade'] for f in buffer_layer.getFeatures()}

        # cria o campo 'visivel' na camada destino se não existir
        idx_visivel = dest_layer.fields().indexFromName('visivel')
        if idx_visivel == -1:
            dest_layer.dataProvider().addAttributes([QgsField('visivel', int)])
            dest_layer.updateFields()
            idx_visivel = dest_layer.fields().indexFromName('visivel')

        # inicia edição na camada de destino
        if not dest_layer.isEditable():
            dest_layer.startEditing()

        # atualiza os valores
        for f in dest_layer.getFeatures():
            id_val = f['id']
            if id_val in vis_dict:
                dest_layer.changeAttributeValue(f.id(), idx_visivel, vis_dict[id_val])

        dest_layer.commitChanges()
        print(f"✅ Valores de 'visibilidade' copiados de '{buffer_layer_name}' para '{dest_layer_name}' na coluna 'visivel'.")


    from qgis.core import QgsProject
    def remover_camadas_buffer_e_ilhas(remover=True):
        """
        Remove todas as camadas do projeto que tenham como nome:
        - 'buffer_quadrado_edificacao'
        - 'ilhas_edicao'
        """
        if(remover):
            nomes_alvo = ["buffer_quadrado_edificacao", "ilhas_edificacao"]
            projeto = QgsProject.instance()
            layers = projeto.mapLayers().values()

            # lista de camadas que serão removidas
            camadas_remover = [layer for layer in layers if layer.name() in nomes_alvo]

            if not camadas_remover:
                print("✅ Nenhuma camada com os nomes especificados foi encontrada.")
                return

            for layer in camadas_remover:
                print(f"🗑️ Removendo camada: {layer.name()} (ID: {layer.id()})")
                projeto.removeMapLayer(layer.id())

            print(f"✅ {len(camadas_remover)} camada(s) removida(s) com sucesso.")


    from qgis.PyQt.QtWidgets import QProgressBar
    from qgis.utils import iface
    from qgis.core import Qgis

    # cria barra
    total_barra = 28

    dlg.iniciar_barra(total_barra)
    # Exibir barra no messageBar do QGIS (opcional)

    #Reseta visibilidade se necessario
    if(resetar_visibilidade):
        campo_visivel_null()
    dlg.barra.setValue(1)
    QCoreApplication.processEvents()
        
    # 1️⃣ Cria os buffers quadrados
    layer_buff = gerar_buffers_quadrados_rotacionados(camada_referencia, raio)
    dlg.barra.setValue(2)
    QCoreApplication.processEvents()

    #definir visualização prioridade com feições com nome
    definir_visibilidade_por_nome(layer_name="buffer_quadrado_edificacao", definir=priorizar_visibilidade_camadas_com_nome)
    #barra.setValue(2)
    dlg.barra.setValue(2)
    QCoreApplication.processEvents()

    # 2️⃣ Calcula a área sobreposta
    #preencher_coluna_area_sobreposta(buffer_layer_name="buffer_quadrado_edificacao")

    # 3️⃣ Cria as ilhas e adiciona id_ilha
    #ilha_layer = criar_ilhas_edificacoes(buffer_layer_name="buffer_quadrado_edificacao")

    #4 Definir visibilidade
    #definir_visibilidade_buffers(buffer_layer_name="buffer_quadrado_edificacao")

    #5 Faz o loop
    loop_atualizar_visibilidade(buffer_layer_name="buffer_quadrado_edificacao")
    dlg.barra.setValue(25)
    QCoreApplication.processEvents()

    #Passar valores
    copiar_visibilidade_para_camada(camada_referencia, buffer_layer_name="buffer_quadrado_edificacao")
    dlg.barra.setValue(26)
    QCoreApplication.processEvents()

    #remover camadadas auxiliares
    remover_camadas_buffer_e_ilhas(remover_camadas_temporarias)
    dlg.barra.setValue(total_barra)
    QCoreApplication.processEvents()

    iface.messageBar().clearWidgets()
    iface.messageBar().pushMessage("Processo concluído ✅", "Todas as etapas foram finalizadas.", level=Qgis.Success, duration=total_barra)