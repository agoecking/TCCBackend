from abc import ABC, abstractmethod


class ICrud:

    @abstractmethod
    def cadastrar(self):
        pass

    @abstractmethod
    def excluir(self):
        pass

    @abstractmethod
    def alterar(self):
        pass