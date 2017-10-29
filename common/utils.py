def from_querydict_to_dict(querydict):
    python_dict=dict(querydict.iterlists())
    return {key:value[0] for key,value in python_dict.items()}