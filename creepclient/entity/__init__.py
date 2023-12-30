"""Entity module for creepclient"""


class Entity(object):
    def __init__(self, data={}, **kwargs):
        if len(data) > 0:
            for key, value in data.iteritems():
                setattr(self, key, value)

        if len(kwargs) > 0:
            for key, value in kwargs.iteritems():
                setattr(self, key, value)


# from creepclient.entity.package import Package
