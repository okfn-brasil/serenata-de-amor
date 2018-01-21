class StringTable(object):

    def __init__(self):
        self.__values = []
        self.__mapping = {}

    def cache(self, value):
        if not value in self.__mapping:
            token = '`%d' % len(self.__values)
            self.__mapping[value] = token
            self.__values.append(value)
        return self.__mapping[value]

    def values(self):
        return self.__values
