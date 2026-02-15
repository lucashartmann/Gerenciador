import os
import av
from textual.app import App
from textual.widgets import ListItem, ListView, Static, Button, Input, Select
from textual.containers import HorizontalGroup, VerticalGroup, Center
from textual import events
from textual import on
from textual_colorpicker import ColorPicker
from textual.widget import Widget
from textual.reactive import reactive
from textual.events import MouseDown, MouseMove
from textual.message import Message
from textual_image.widget import SixelImage, HalfcellImage, TGPImage, Image
from rich.text import Text
from model.Etiqueta import Etiqueta
from model import Cofre


class Slider(Widget):

    value = reactive(0.5)

    def render(self):
        width = self.size.width
        pos = int(self.value * (width - 1))

        bar = ["─"] * width
        bar[pos] = "●"

        return Text("".join(bar))

    def on_mouse_down(self, event: MouseDown):
        self.set_value_from_x(event.x)

    def on_mouse_move(self, event: MouseMove):
        if event.button:
            self.set_value_from_x(event.x)

    def set_value_from_x(self, x):
        width = self.size.width
        self.value = min(max(x / width, 0), 1)

    class Changed(Message):
        def __init__(self, sender, value: float):
            self.value = value
            super().__init__()

    def watch_value(self, value: float):
        self.post_message(self.Changed(self, value))


class GerenciadorApp(App):
    CSS_PATH = "css/Gerenciador.tcss"

    caminho = f"{os.path.expanduser('~')}\\Downloads"
    Image = HalfcellImage
    lista_arquivos = os.listdir(caminho)
    arquivos_filtrados = []
    caminhos = list()
    arquivo_selecionado = ""
    etiquetas = dict()
    caminhos_etiquetas = dict()
    etiqueta_selecionada = ""
    static_antigo = ''
    caminho_arquivo = caminho
    static_clicado = ""
    valor_slide = 0.5

    def on_slider_changed(self, evento: Slider.Changed):
        lista = self.query_one("#lst_item")
        valor_rows = int(lista.styles.grid_rows[0][0])
        valor_columns = int(lista.styles.grid_columns[0][0])
        if evento.value > self.valor_slide:
            lista.styles.grid_rows = f"{valor_rows + 1}%"
            lista.styles.grid_columns = f"{valor_columns + 1}%"
        else:
            lista.styles.grid_rows = f"{valor_rows - 1}%"
            lista.styles.grid_columns = f"{valor_columns - 1}%"
        self.valor_slide = evento.value

    def compose(self):
        with HorizontalGroup(id="nav-bar"):
            yield Button("<-", id="bt_voltar")
            yield Input(self.caminho, id="campo_caminho")
            yield Input(placeholder="Pesquise aqui", id="pesquisa")
        with HorizontalGroup():
            yield ListView(id="lst_item")
            with VerticalGroup(id="menu_etiquetas"):
                yield Slider()
                yield Select([("Sixel", "Sixel"), ("Hallfell", "Halfcell"), ("Auto", "Auto"), ("TGP", "TGP")], value="Halfcell", prompt="Image Render", id="slc_render")
                yield Static(f"Selecionado:", id="stt_arquivo_selecionado")
                yield Input(placeholder="Nome da etiqueta", id="nome")
                with Center(id="center_color"):
                    yield ColorPicker()
                yield Select([("Cadastrar", "Cadastrar"), ("Editar", "Editar"), ("Remover", "Remover")], value="Cadastrar", id="slct_operacao")
                with Center():
                    yield Button("Executar", id="bt_executar")
                    yield Button("Limpar", id="bt_limpar")
                yield Static("Etiquetas:", id="stt_etiquetas")
                yield ListView(id="lst_etiqueta")

    def on_select_changed(self, evento: Select.Changed):
        if evento.select.id == "slc_render":
            antigo = self.Image
            match evento.select.value:
                case "Sixel":
                    self.Image = SixelImage
                case "Halfcell":
                    self.Image = HalfcellImage
                case "Auto":
                    self.Image = Image
                case "TGP":
                    self.Image = TGPImage

            if self.Image != antigo:
                list_view = self.query_one("#lst_item", ListView)
                for item in list_view.children:
                    if "Center()" in str(list(item.children)):
                        conteudo = item.query_one(
                            Center).query_one(antigo).image
                        item.query_one(Center).query_one(antigo).remove()
                        item.query_one(Center).mount(self.Image(conteudo))

    def on_click(self, evento: events.Click):
        if evento.widget.parent.id == "lst_item" or evento.widget.parent.parent.id == "lst_item" or evento.widget.parent.parent.parent.id == "lst_item":
            if evento.widget.parent.id == "lst_item":
                self.static_clicado = evento.widget.query_one(Static).content
            elif evento.widget.parent.parent.id == "lst_item":
                self.static_clicado = evento.widget.parent.query_one(
                    Static).content
            elif evento.widget.parent.parent.parent.id == "lst_item":
                self.static_clicado = evento.widget.parent.parent.query_one(
                    Static).content
            if evento.chain == 2:
                if "." not in self.static_clicado:
                    if self.caminho not in self.caminhos:
                        self.caminhos.append(self.caminho)
                    caminho_pasta = self.caminho + f"\\{self.static_clicado}"
                    self.caminho = caminho_pasta
                    self.query_one("#campo_caminho").value = self.caminho
                    self.caminhos.append(caminho_pasta)
                    self.static_antigo = self.static_clicado
                    self.carregar_arquivos()
                else:
                    os.startfile(self.caminho + f"\\{self.static_clicado}")
            elif evento.chain > 2:
                os.startfile(self.caminho + f"\\{self.static_clicado}")

    def carregar_arquivos(self):
        list_view = self.query_one("#lst_item", ListView)
        for child in list_view.children:
            child.remove()
        try:
            self.lista_arquivos = os.listdir(self.caminho)
        except Exception as e:
            self.notify("Caminho inválido")
            print(e)
            return
        carregar_etiquetas = Cofre.carregar("Etiquetas.db", "etiquetas")
        carregar_caminhos = Cofre.carregar("Etiquetas.db",
                                           "caminhos",)
        carregar_caminhos_etiquetas = Cofre.carregar("Etiquetas.db",
                                                     "caminhos_etiquetas", )

        if carregar_caminhos:
            self.caminhos = carregar_caminhos
        if carregar_caminhos_etiquetas:
            self.caminhos_etiquetas = carregar_caminhos_etiquetas

        for arquivo in self.lista_arquivos:
            if "." not in arquivo:
                index_arquivo = self.lista_arquivos.index(arquivo)
                self.lista_arquivos[index_arquivo] = arquivo

        if carregar_etiquetas:
            self.etiquetas = carregar_etiquetas
            for arquivo in self.lista_arquivos:
                arquivo_stt = Static(arquivo)
                for etiqueta_obj in self.etiquetas.values():
                    if arquivo in etiqueta_obj.arquivos and etiqueta_obj.get_cor():
                        try:
                            arquivo_stt.styles.color = etiqueta_obj.get_cor()
                        except Exception as e:
                            print(e)
                            pass
                        break
                if "." not in arquivo:
                    list_view.append(
                        ListItem(Center(self.Image(r"assets/folder.png")), arquivo_stt))
                elif arquivo.split(".")[-1] in ["jpg", "jpeg", "png", "webpm"]:
                    list_view.append(
                        ListItem(Center(self.Image(self.caminho + f"\\{arquivo}")), arquivo_stt))
                elif arquivo.split(".")[-1] in ["mp4"]:
                    container = av.open(self.caminho + f"\\{arquivo}")
                    stream = container.streams.video[0]
                    frames = container.decode(stream)
                    preloaded_frames = [frame.to_image() for frame in frames]
                    thumbnail = preloaded_frames[0]
                    list_view.append(
                        ListItem(Center(self.Image(thumbnail)), arquivo_stt))
                else:
                    list_view.append(ListItem(arquivo_stt))
        else:
            for arquivo in self.lista_arquivos:
                if "." not in arquivo:
                    list_view.append(
                        ListItem(Center(self.Image(r"assets/folder.png")), Static(arquivo)))
                elif arquivo.split(".")[-1] in ["jpg", "jpeg", "png", "webpm"]:
                    list_view.append(
                        ListItem(Center(self.Image(self.caminho + f"\\{arquivo}")), Static(arquivo)))
                elif arquivo.split(".")[-1] in ["mp4"]:
                    container = av.open(self.caminho + f"\\{arquivo}")
                    stream = container.streams.video[0]
                    frames = container.decode(stream)
                    preloaded_frames = [frame.to_image() for frame in frames]
                    thumbnail = preloaded_frames[0]
                    list_view.append(
                        ListItem(Center(self.Image(thumbnail)), Static(arquivo)))
                else:
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

    def on_input_submitted(self, evento: Input.Submitted):
        if evento.input.id == "campo_caminho":
            self.caminho = evento.input.value
            try:
                self.carregar_arquivos()
                self.caminhos.append(self.caminho)
            except Exception as e:
                print(e)
                return

    def on_mount(self):
        self.carregar_arquivos()
        self.carregar_etiquetas()
        self.caminhos.append(self.caminho)

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
                        except Exception as e:
                            print(e)
                            pass
                        break
                if "." not in arquivo:
                    list_view.append(
                        ListItem(Center(self.Image(r"assets/folder.png")), arquivo_stt))
                elif arquivo.split(".")[-1] in ["jpg", "jpeg", "png", "webpm"]:
                    list_view.append(
                        ListItem(Center(self.Image(self.caminho + f"\\{arquivo}")), arquivo_stt))
                elif arquivo.split(".")[-1] in ["mp4"]:
                    container = av.open(self.caminho + f"\\{arquivo}")
                    stream = container.streams.video[0]
                    frames = container.decode(stream)
                    preloaded_frames = [frame.to_image() for frame in frames]
                    thumbnail = preloaded_frames[0]
                    list_view.append(
                        ListItem(Center(self.Image(thumbnail)), arquivo_stt))
                else:
                    list_view.append(ListItem(arquivo_stt))

        else:
            for arquivo in self.lista_arquivos:
                arquivo_stt = Static(arquivo)
                for etiqueta_obj in self.etiquetas.values():
                    if arquivo in etiqueta_obj.arquivos and etiqueta_obj.get_cor():
                        try:
                            arquivo_stt.styles.color = etiqueta_obj.get_cor()
                        except Exception as e:
                            print(e)
                            pass
                        break
                if "." not in arquivo:
                    list_view.append(
                        ListItem(Center(self.Image(r"assets/folder.png")), arquivo_stt))
                elif arquivo.split(".")[-1] in ["jpg", "jpeg", "png", "webpm"]:
                    list_view.append(
                        ListItem(Center(self.Image(self.caminho + f"\\{arquivo}")), arquivo_stt))
                elif arquivo.split(".")[-1] in ["mp4"]:
                    container = av.open(self.caminho + f"\\{arquivo}")
                    stream = container.streams.video[0]
                    frames = container.decode(stream)
                    preloaded_frames = [frame.to_image() for frame in frames]
                    thumbnail = preloaded_frames[0]
                    list_view.append(
                        ListItem(Center(self.Image(thumbnail)), arquivo_stt))
                else:
                    list_view.append(ListItem(arquivo_stt))

    @on(ListView.Highlighted)
    def item_selecionado(self, evento: ListView.Highlighted):
        match evento.list_view.id:
            case "lst_item":
                try:
                    arquivo = evento.item.get_child_by_type(Static).content
                    self.arquivo_selecionado = arquivo
                    self.query_one(
                        "#stt_arquivo_selecionado").content = f"Selecionado: {self.arquivo_selecionado}"
                except Exception as e:
                    print(e)
                    pass
            case "lst_etiqueta":
                try:
                    etiqueta = evento.item.get_child_by_type(Static).content
                    self.etiqueta_selecionada = etiqueta
                except Exception as e:
                    print(e)
                    pass

    def on_button_pressed(self, evento: Button.Pressed):
        match evento.button.id:
            case "bt_voltar":
                if self.static_clicado == self.static_antigo:
                    if len(self.caminhos) < 2:
                        self.notify("Não há caminhos antigos")
                        return
                    self.caminhos.pop()
                    self.caminho = self.caminhos[-1]
                    self.query_one("#campo_caminho").value = self.caminho
                    self.carregar_arquivos()
                else:
                    self.notify("Sem pasta raiz")

            case "bt_limpar":
                for input in self.query(Input):
                    input.value = ""

            case "bt_executar":
                select = self.query_one("#slct_operacao", Select)
                match select.value:
                    case "Cadastrar":
                        nome = self.query_one("#nome", Input).value
                        cor = self.query_one(ColorPicker).color

                        if nome not in self.etiquetas.keys():
                            etiqueta = Etiqueta(nome, cor, self.caminho)
                            cadastro = etiqueta.add_arquivo(
                                self.arquivo_selecionado)
                            if cadastro:
                                self.etiquetas[nome] = etiqueta
                                self.caminhos_etiquetas[self.caminho] = self.etiquetas
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
                            # self.caminhos_etiquetas[self.caminho] = self.etiquetas[nome]
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
                        Cofre.salvar("Etiquetas.db",
                                     "caminhos", self.caminhos)
                        Cofre.salvar("Etiquetas.db",
                                     "caminhos_etiquetas", self.caminhos_etiquetas)

                    case "Editar":
                        nome = self.etiqueta_selecionada
                        novo_nome = self.query_one("#nome", Input).value
                        cor = self.query_one(ColorPicker).color
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
                            Cofre.salvar("Etiquetas.db",
                                         "caminhos", self.caminhos)
                            Cofre.salvar("Etiquetas.db",
                                         "caminhos_etiquetas", self.caminhos_etiquetas)
                        except Exception as e:
                            print(e)
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
                            Cofre.salvar("Etiquetas.db",
                                         "caminhos", self.caminhos)
                            Cofre.salvar("Etiquetas.db",
                                         "caminhos_etiquetas", self.caminhos_etiquetas)
                        except Exception as e:
                            print(e)
                            self.notify(
                                f"ERRO ao remover! '{self.etiqueta_selecionada}'")

                    case _:
                        self.notify("Selecione uma operação")
