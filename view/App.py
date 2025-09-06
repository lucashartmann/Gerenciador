from textual.app import App
from textual.widgets import ListItem, ListView, Static, Button, Input, Select
from textual.containers import HorizontalGroup, VerticalGroup
from textual.events import Click
from textual import on
import os
from model.Etiqueta import Etiqueta
from model import Cofre


class GerenciadorApp(App):
    CSS_PATH = "css/Gerenciador.tcss"

    caminho = f"{os.path.expanduser('~')}\\Downloads"

    lista_arquivos = os.listdir(caminho)
    arquivos_filtrados = []
    arquivo_selecionado = ""
    etiquetas = dict()
    arquivo_antes = ""
    expandidas = set()
    etiqueta_selecionada = ""
    pasta = ""
    contador = 1

    def compose(self):
        with HorizontalGroup():
            yield ListView(id="lst_item")
            with HorizontalGroup():
                with VerticalGroup(id="vg_inputs"):
                    yield Input(placeholder="Pesquise aqui", id="pesquisa")
                    yield Input(placeholder="Nome da etiqueta", id="nome")
                    yield Input(placeholder="Cor da etiqueta", id="cor")
                with VerticalGroup():
                    yield Select([("Cadastrar", "Cadastrar"), ("Editar", "Editar"), ("Remover", "Remover")])
                    yield Button("Executar", id="bt_executar")
                    yield Button("Limpar", id="bt_limpar")
                yield ListView(id="lst_etiqueta")

    caminho_arquivo = caminho

    def on_click(self, evento: Click):
        if evento.widget.parent.parent.id == "lst_item":
            if isinstance(evento.widget, Static):
                static_clicado = evento.widget.content  # Static que recebeu o clique
                if static_clicado == self.arquivo_antes and evento.chain == 2:  # Verifica se o static recebeu clique duplo

                    lista_view = self.query_one(ListView)

                    if "." not in static_clicado:  # Verifica se é uma pasta

                        if "->" not in static_clicado and static_clicado[:-1] not in self.caminho_arquivo.split("\\"):
                            # Caminho da pasta clicada, [:1] remove a seta ↓
                            self.notify("Lucas")
                            self.caminho_arquivo += \
                                f"\\{static_clicado[:-1]}"

                        self.notify(str(self.caminho_arquivo.split("\\")))
                        if "->" in static_clicado:  # Verifica se é uma pasta dentro de outra pasta
                            self.contador += 1
                            statics = []

                            for list_item in lista_view.children:  # Varre a lista de ListItem da ListView

                                statics.append(
                                    # Adiciona o conteúdo do Static de cada ListItem na lista statics
                                    list_item.get_child_by_type(Static).content)

                            if static_clicado[(self.contador+2):-1] not in self.caminho_arquivo.split("\\"):
                                self.caminho_arquivo += \
                                    f"\\{static_clicado[(self.contador+2):-1]}"  # Caminho da pasta clicada dentro da pasta raiz

                        arquivos_pasta = os.listdir(
                            self.caminho_arquivo)

                        self.notify(self.caminho_arquivo)

                        for arquivo in arquivos_pasta:  # Varre os arquivos da pasta clicada
                            # Substitui o nome do arquivo na lista por ele mesmo + seta (↓) se for uma pasta
                            if "." not in arquivo[1:]:
                                index_arquivo = arquivos_pasta.index(
                                    arquivo)
                                arquivo = arquivo + "↓"
                                arquivos_pasta[index_arquivo] = arquivo

                        for list_item in lista_view.children:  # Varre a lista de ListItem da ListView

                            if list_item.get_child_by_type(Static).content == static_clicado:
                                index_static = lista_view.children.index(
                                    list_item)  # Pega o index do ListItem que contém o Static clicado

                        # Verifica se a pasta já está expandida
                        if "->" in static_clicado and static_clicado[static_clicado.index("->"):-1] in self.expandidas or "↓" in static_clicado and static_clicado[:-1] in self.expandidas:

                            for list_item in lista_view.children:  # Varre a lista de ListItem da ListView
                                conteudo = list_item.get_child_by_type(
                                    Static).content
                                self.notify(str(arquivos_pasta))

                                # Remove "->"
                                conteudo = conteudo[self.contador+3:]

                                if conteudo in arquivos_pasta:
                                    list_item.remove()

                            if "->" in static_clicado:
                                index = static_clicado.index("->")
                                self.expandidas.remove(
                                    static_clicado[index:-1])
                            if "↓" in static_clicado:
                                self.expandidas.remove(static_clicado[:-1])

                            if self.contador > 1:
                                self.contador -= 1

                        else:
                            if "->" in static_clicado and static_clicado[static_clicado.index("->"):-1] not in self.expandidas or "↓" in static_clicado and static_clicado[:-1] not in self.expandidas:
                                for i, arquivo in enumerate(arquivos_pasta):
                                    i += 1
                                    lista_view.insert(
                                        index_static+i, [ListItem(Static(f"{self.contador * ' '}-> {arquivo}"), name=arquivo)])

                                if "->" in static_clicado:
                                    index = static_clicado.index("->")
                                    self.expandidas.add(
                                        static_clicado[index:-1])
                                if "↓" in static_clicado:
                                    self.expandidas.add(static_clicado[:-1])

                    else:
                        if "->" in static_clicado and "." in static_clicado:
                            os.startfile(
                                f"{self.caminho}\\{self.pasta}\\{static_clicado[6:]}")
                        else:
                            os.startfile(self.caminho_arquivo)
                else:
                    self.arquivo_antes = static_clicado

    def carregar_arquivos(self):
        carregar = Cofre.carregar("Etiquetas.db", "etiquetas")
        list_view = self.query_one("#lst_item", ListView)
        for arquivo in self.lista_arquivos:
            if "." not in arquivo:
                index_arquivo = self.lista_arquivos.index(arquivo)
                arquivo = arquivo + "↓"
                self.lista_arquivos[index_arquivo] = arquivo

        if carregar:
            self.etiquetas = carregar
            for arquivo in self.lista_arquivos:
                arquivo_stt = Static(arquivo)
                for etiqueta_obj in self.etiquetas.values():
                    if arquivo in etiqueta_obj.arquivos and etiqueta_obj.get_cor():
                        try:
                            arquivo_stt.styles.color = etiqueta_obj.get_cor()
                        except:
                            pass
                        break
                list_view.append(ListItem(arquivo_stt))
        else:
            for arquivo in self.lista_arquivos:
                list_view.append(ListItem(Static(arquivo)))

    def carregar_etiquetas(self):
        lista_view = self.query_one("#lst_etiqueta", ListView)
        for child in lista_view.children:
            child.remove()
        if self.etiquetas:
            for etiqueta_obj in self.etiquetas.values():
                stt = Static(etiqueta_obj.get_nome())
                stt.styles.color = etiqueta_obj.get_cor()
                lista_view.append(
                    ListItem(stt))

    def on_mount(self):
        self.carregar_arquivos()
        self.carregar_etiquetas()

    def on_input_changed(self, evento: Input.Changed):
        if evento.input.id == "pesquisa":
            texto = evento.input.value
            self.arquivos_filtrados = []
            if len(texto) > 0:
                for chave, etiqueta in self.etiquetas.items():
                    if texto in chave:
                        for arquivo in etiqueta.arquivos:
                            if arquivo not in self.arquivos_filtrados:
                                self.arquivos_filtrados.append(arquivo)

            self.atualizar()

    def atualizar(self):

        list_view = self.query_one("#lst_item", ListView)
        list_view.clear()

        if len(self.arquivos_filtrados) > 0:
            for arquivo in self.arquivos_filtrados:
                arquivo_stt = Static(arquivo)
                for etiqueta_obj in self.etiquetas.values():
                    if arquivo in etiqueta_obj.arquivos and etiqueta_obj.get_cor():
                        try:
                            arquivo_stt.styles.color = etiqueta_obj.get_cor()
                        except:
                            pass
                        break
                list_view.append(ListItem(arquivo_stt))

        else:
            for arquivo in self.lista_arquivos:
                arquivo_stt = Static(arquivo)
                for etiqueta_obj in self.etiquetas.values():
                    if arquivo in etiqueta_obj.arquivos and etiqueta_obj.get_cor():
                        try:
                            arquivo_stt.styles.color = etiqueta_obj.get_cor()
                        except:
                            pass
                        break
                item = ListItem(arquivo_stt)
                list_view.append(item)

    @on(ListView.Highlighted)
    def item_selecionado(self, evento: ListView.Highlighted):
        match evento.list_view.id:
            case "lst_item":
                try:
                    arquivo = evento.item.get_child_by_type(Static).content
                    self.arquivo_selecionado = arquivo
                except:
                    pass
            case "lst_etiqueta":
                try:
                    etiqueta = evento.item.get_child_by_type(Static).content
                    self.etiqueta_selecionada = etiqueta
                except:
                    pass

    def on_button_pressed(self, evento: Button.Pressed):
        match evento.button.id:
            case "bt_limpar":
                for input in self.query(Input):
                    input.value = ""

            case "bt_executar":
                select = self.query_one(Select)
                match select.value:
                    case "Cadastrar":
                        nome = self.query_one("#nome", Input).value
                        cor = self.query_one("#cor", Input).value

                        if nome not in self.etiquetas.keys():
                            etiqueta = Etiqueta(nome, cor)
                            cadastro = etiqueta.add_arquivo(
                                self.arquivo_selecionado)
                            if cadastro:
                                self.etiquetas[nome] = etiqueta
                                for static in self.query(Static):
                                    if static.content == self.arquivo_selecionado and cor != "":
                                        try:
                                            static.styles.color = cor
                                        except:
                                            self.notify(
                                                f"ERRO. '{cor}' inválida")
                                self.notify("Arquivo etiquetado")
                            else:
                                self.notify("Arquivo já cadastrado")
                        else:
                            etiqueta = self.etiquetas[nome]
                            cadastro = etiqueta.add_arquivo(
                                self.arquivo_selecionado)
                            if cadastro:
                                for static in self.query(Static):
                                    if static.content == self.arquivo_selecionado and cor != "":
                                        try:
                                            static.styles.color = cor
                                        except:
                                            self.notify(
                                                f"ERRO. '{cor}' inválida")
                                self.notify("Arquivo etiquetado")
                            else:
                                self.notify("Arquivo já cadastrado")
                        self.carregar_etiquetas()
                        Cofre.salvar("Etiquetas.db",
                                     "etiquetas", self.etiquetas)

                    case "Editar":
                        nome = self.etiqueta_selecionada
                        novo_nome = self.query_one("#nome", Input).value
                        cor = self.query_one("#cor", Input).value
                        try:
                            etiqueta = self.etiquetas[nome]
                            if novo_nome and cor:
                                etiqueta.set_nome(novo_nome)
                                etiqueta.set_cor(cor)
                            elif cor:
                                etiqueta.set_cor(cor)
                            elif novo_nome:
                                etiqueta.set_nome(novo_nome)
                            self.carregar_etiquetas()
                            self.atualizar()
                            Cofre.salvar("Etiquetas.db",
                                         "etiquetas", self.etiquetas)
                        except:
                            self.notify(
                                f"ERRO ao editar! '{self.etiqueta_selecionada}'")

                    case "Remover":
                        try:
                            del self.etiquetas[self.etiqueta_selecionada]
                            self.notify("Etiqueta Removida com sucesso")
                            statico = self.query_one("#lst_item", ListView).query_one(
                                ListItem).query_one(Static)
                            if statico.content == self.etiqueta_selecionada:
                                statico.remove()
                            self.carregar_etiquetas()
                            self.atualizar()
                            Cofre.salvar("Etiquetas.db",
                                         "etiquetas", self.etiquetas)
                        except:
                            self.notify(
                                f"ERRO ao remover! '{self.etiqueta_selecionada}'")

                    case _:
                        self.notify("Selecione uma operação")
