from abc import abstractmethod


class Foo():

    def __init__(self):
        pass

    def bar(self):
        return "bar"

    @abstractmethod
    def abstract(self):
        raise NotImplementedError()
