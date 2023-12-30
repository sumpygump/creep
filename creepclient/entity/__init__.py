"""Entity module for creepclient"""


class Entity(object):
    """Base Entity model"""

    def __init__(self, data=None, **kwargs):
        """Initialize this object"""

        if data is None:
            data = {}

        if len(data) > 0:
            for key, value in data.iteritems():
                setattr(self, key, value)

        if len(kwargs) > 0:
            for key, value in kwargs.iteritems():
                setattr(self, key, value)
