class Etiqueta:
    
    def __init__(self, nome, cor, caminho):
        self.nome = nome
        self.cor = cor
        self.arquivos = list()
        self.caminho = caminho
        
    def add_arquivo(self, arquivo):
        if arquivo not in self.arquivos:
            self.arquivos.append(arquivo)
            return True
        return False
        
    def get_nome(self):
        return self.nome

    def set_nome(self, value):
        self.nome = value

    def get_cor(self):
        return self.cor

    def set_cor(self, value):
        self.cor = value

    