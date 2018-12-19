MSG = 'This is not yet implemented'


def validate(sketch):
    """
    - sketch: a `dict`
    """
    raise NotImplementedError(MSG)


def readsketch_iter(iterable):
    """
    - iterable: as return by ijson.parser

    Returns a `dict` with a sketch information
    """
    raise NotImplementedError(MSG)


def readjamschema(schema):
    """
    Read a JAM definition schema
    """
    raise NotImplementedError(MSG)
    
