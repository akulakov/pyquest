import conf

class Levels:
    """Current level map with all objects and beings."""

    __shared_state = {}

    def __init__(self):
        self.current = 1
        self.list = [None]*conf.levels
        self.__init__ = self.__shared_state

levels = Levels()
