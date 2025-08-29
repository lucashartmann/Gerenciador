from textual.app import App
from textual.widgets import ListItem, ListView, Static, Button, Input
from textual.containers import HorizontalGroup, VerticalGroup
from textual import on
import os
from model.Etiqueta import Etiqueta
from model import Cofre


class GerenciadorApp(App):
    CSS_PATH = "css/Gerenciador.tcss"
    
    lista_arquivos = os.listdir("C:\\Users\\dudua\\Downloads")
    arquivos_filtrados = []
    arquivo_selecionado = ""
    etiquetas = dict()
    
    def compose(self):
        with HorizontalGroup():
            yield ListView(id="lst_item")
            with HorizontalGroup():
                with VerticalGroup():
                    yield Input(placeholder="Pesquise aqui", id="pesquisa")
                    yield Input(placeholder="Nome da etiqueta", id="nome")
                    yield Input(placeholder="Cor da etiqueta", id="cor")
                with VerticalGroup():
                    yield Button("Limpar")
                    yield Button("Adicionar")
            yield ListView(id="lst_etiqueta")
            
    def carregar_arquivos(self):
        carregar = Cofre.carregar("Etiquetas.db", "etiquetas")
        list_view = self.query_one("#lst_item", ListView)
        
        if carregar:
            self.etiquetas = carregar
            for etiqueta_obj in self.etiquetas.values():
                for arquivo in self.lista_arquivos:
                    arquivo_stt = Static(arquivo)
                    if arquivo in etiqueta_obj.arquivos and etiqueta_obj.get_cor():
                        arquivo_stt.styles.color = etiqueta_obj.get_cor()
                    list_view.append(
                        ListItem(arquivo_stt))
        else:
            for arquivo in self.lista_arquivos:
                list_view.append(
                    ListItem(Static(arquivo)))
                
    def carregar_etiquetas(self):
        lista_view = self.query_one("#lst_etiqueta", ListView)
        for etiqueta_obj in self.etiquetas.values():
            stt = Static(etiqueta_obj.get_nome())
            stt.styles.color = etiqueta_obj.get_cor()
            lista_view.append(
                    ListItem(stt))


    def on_mount(self):
        self.carregar_arquivos()
        self.carregar_etiquetas()
                
    def on_input_changed(self, evento : Input.Changed):
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
            self.notify(str(self.arquivos_filtrados))
            try:
                for etiqueta_obj in self.etiquetas.values():
                    for arquivo in self.arquivos_filtrados:
                        arquivo_stt = Static(arquivo)
                        if arquivo in etiqueta_obj.arquivos and etiqueta_obj.get_cor():
                            arquivo_stt.styles.color = etiqueta_obj.get_cor()
                        list_view.append(
                            ListItem(arquivo_stt))
            except:
                for arquivo in self.arquivos_filtrados:
                    list_view.append(
                        ListItem(Static(arquivo)))
        else:
            try:
                for etiqueta_obj in self.etiquetas.values():
                    for arquivo in self.lista_arquivos:
                        arquivo_stt = Static(arquivo)
                        if arquivo in etiqueta_obj.arquivos and etiqueta_obj.get_cor():
                            arquivo_stt.styles.color = etiqueta_obj.get_cor()
                        list_view.append(
                            ListItem(arquivo_stt))
            except:
                for arquivo in self.lista_arquivos:
                        list_view.append(
                            ListItem(Static(arquivo)))
            

            
    @on(ListView.Highlighted)
    def item_selecionado(self, evento : ListView.Highlighted):
        try:
            arquivo = evento.item.get_child_by_type(Static)._content
            self.notify(str(arquivo))
            self.arquivo_selecionado = arquivo
        except:
            pass
        
    def on_button_pressed(self):
        nome = self.query_one("#nome", Input).value
        cor = self.query_one("#cor", Input).value
        
        if nome not in self.etiquetas.keys():
            etiqueta = Etiqueta(nome, cor)
            etiqueta.add_arquivo(self.arquivo_selecionado)
            self.etiquetas[nome] = etiqueta
            for static in self.query(Static):
                if static._content == self.arquivo_selecionado and cor != "":
                    static.styles.color = cor
        else:
            etiqueta = self.etiquetas[nome]
            etiqueta.add_arquivo(self.arquivo_selecionado)
            for static in self.query(Static):
                if static._content == self.arquivo_selecionado and cor != "":
                    static.styles.color = cor
        Cofre.salvar("Etiquetas.db", "etiquetas", self.etiquetas)
    