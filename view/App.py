import os
import av
import os
import sys
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
import win32gui
import win32ui
import win32con
from win32com.shell import shell, shellcon
from PIL import Image as PilImage


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

    def resource_path(self, relative_path):
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

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
        Cofre.salvar("Slider", "grid_rows", int(lista.styles.grid_rows[0][0]))
        Cofre.salvar("Slider", "grid_columns", int(
            lista.styles.grid_columns[0][0]))

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
            Cofre.salvar("Render", "render", evento.select.value)

    def on_click(self, evento: events.Click):
        widget = evento.widget
        alvo = None

        while widget:
            if hasattr(widget, "id") and widget.id == "lst_item":
                break
            widget = widget.parent

        if not widget:
            return

        item = evento.widget
        while item and not isinstance(item, ListItem):
            item = item.parent

        if not item:
            return

        static = item.query_one(Static)
        if not static:
            return

        self.static_clicado = static.content
        caminho_completo = os.path.join(self.caminho, self.static_clicado)

        if evento.chain == 2:
            if os.path.isdir(caminho_completo):
                if self.caminho not in self.caminhos:
                    self.caminhos.append(self.caminho)

                self.caminho = caminho_completo
                self.query_one("#campo_caminho").value = self.caminho

                if caminho_completo not in self.caminhos:
                    self.caminhos.append(caminho_completo)

                self.static_antigo = self.static_clicado
                self.atualizar()
            else:
                try:
                    os.startfile(caminho_completo)
                except Exception as e:
                    print(e)

    def extrair_icone(self, path, size=256):
        flags = (
            shellcon.SHGFI_ICON |
            shellcon.SHGFI_LARGEICON |
            shellcon.SHGFI_USEFILEATTRIBUTES
        )

        if os.path.isdir(path):
            attr = win32con.FILE_ATTRIBUTE_DIRECTORY
        else:
            attr = win32con.FILE_ATTRIBUTE_NORMAL

        ret, info = shell.SHGetFileInfo(path, attr, flags)
        hicon = info[0]

        if not hicon:
            return None

        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, size, size)

        hdc_mem = hdc.CreateCompatibleDC()
        hdc_mem.SelectObject(hbmp)

        win32gui.DrawIconEx(
            hdc_mem.GetHandleOutput(),
            0,
            0,
            hicon,
            size,
            size,
            0,
            None,
            win32con.DI_NORMAL,
        )

        bmpinfo = hbmp.GetInfo()
        bmpstr = hbmp.GetBitmapBits(True)

        img = PilImage.frombuffer(
            "RGBA",
            (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
            bmpstr,
            "raw",
            "BGRA",
            0,
            1,
        )

        win32gui.DestroyIcon(hicon)

        return img

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
                self.atualizar()
                self.caminhos.append(self.caminho)
            except Exception as e:
                print(e)
                return

    def carregar_slide(self):
        try:
            grid_rows = Cofre.carregar("Slider", "grid_rows")
            grid_columns = Cofre.carregar("Slider", "grid_columns")
            lista = self.query_one("#lst_item")
            lista.styles.grid_rows = f"{grid_rows}%"
            lista.styles.grid_columns = f"{grid_columns}%"
        except Exception as e:
            print(e)
            return

    def on_mount(self):
        self.atualizar()
        self.carregar_etiquetas()
        self.carregar_slide()
        valor = Cofre.carregar("Render", "render")
        if valor:
            self.query_one(Select).value = valor
        if self.caminho not in self.caminhos:
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
        list_view.remove_children()

        lista = self.lista_arquivos

        if len(self.arquivos_filtrados) > 0:
            lista = self.arquivos_filtrados
        else:
            try:
                self.lista_arquivos = os.listdir(self.caminho)
            except Exception as e:
                self.notify("Caminho inválido")
                print(e)
                return

            lista = self.lista_arquivos

        carregar_etiquetas = Cofre.carregar("Etiquetas.db", "etiquetas")
        carregar_caminhos = Cofre.carregar("Etiquetas.db", "caminhos")
        carregar_caminhos_etiquetas = Cofre.carregar(
            "Etiquetas.db", "caminhos_etiquetas")

        if carregar_etiquetas:
            self.etiquetas = carregar_etiquetas

        if carregar_caminhos:
            self.caminhos = carregar_caminhos

        if carregar_caminhos_etiquetas:
            self.caminhos_etiquetas = carregar_caminhos_etiquetas

        for arquivo in lista:
            caminho_completo = os.path.join(self.caminho, arquivo)
            arquivo_stt = Static(arquivo)

            if self.etiquetas:
                for etiqueta_obj in self.etiquetas.values():
                    if arquivo in etiqueta_obj.arquivos and etiqueta_obj.get_cor():
                        try:
                            arquivo_stt.styles.color = etiqueta_obj.get_cor()
                        except Exception as e:
                            print(e)
                        break

            extensao = arquivo.lower().split(".")[-1] if "." in arquivo else ""

            if extensao in ["jpg", "jpeg", "png", "webp"]:
                list_view.append(
                    ListItem(
                        Center(
                            self.Image(caminho_completo),
                            Static(arquivo)
                        )
                    )
                )

            elif extensao in ["mp4"]:
                try:
                    container = av.open(caminho_completo)
                    stream = container.streams.video[0]
                    frames = container.decode(stream)
                    first_frame = next(frames)
                    thumbnail = first_frame.to_image()
                    container.close()

                    list_view.append(
                        ListItem(
                            Center(
                                self.Image(thumbnail),
                                Static(arquivo)
                            )
                        )
                    )
                except Exception as e:
                    print(e)
                    list_view.append(ListItem(arquivo_stt))

            else:
                imagem = self.extrair_icone(caminho_completo)
                if imagem:
                    list_view.append(
                        ListItem(
                            Center(
                                self.Image(imagem),
                                Static(arquivo)
                            )
                        )
                    )
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
                    self.atualizar()
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
