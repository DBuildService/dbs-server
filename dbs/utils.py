__author__ = 'ttomecek'


def chain_dict_get(dict_object, keys_list, default=None):
    """
    something like {}.get('key1', 'key2', 'key3', default='') which means

    {}['key1']['key2]...

    :param dict_object: dict
    :param keys_list: list of keys
    :return: value or default
    """
    d = dict_object
    for key in keys_list:
        try:
            d = d[key]
        except (KeyError, TypeError):
            return default
    return d
