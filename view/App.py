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
    etiqueta_selecionada = ""

    caminhos = list()

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
                static_clicado = evento.widget.content
                if evento.chain == 2:
                    if "." not in static_clicado:
                        self.caminhos.append(self.caminho)
                        caminho_pasta = self.caminho + \
                            f"\\{static_clicado[:-1]}"
                        arquivos_pasta = os.listdir(caminho_pasta)
                        self.caminho = arquivos_pasta
                        self.caminhos.append(arquivos_pasta)
                        self.carregar_arquivos()
                else:
                    os.startfile(self.caminho_arquivo)

    def carregar_arquivos(self):
        self.lista_arquivos = os.listdir(self.caminho)
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
