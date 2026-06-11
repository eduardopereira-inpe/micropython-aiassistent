def _deep_copy(value):
    if isinstance(value, dict):
        copied = {}
        for key in value:
            copied[key] = _deep_copy(value[key])
        return copied

    if isinstance(value, list):
        copied = []
        for item in value:
            copied.append(_deep_copy(item))
        return copied

    if isinstance(value, tuple):
        copied = []
        for item in value:
            copied.append(_deep_copy(item))
        return tuple(copied)

    return value


class CallableTool:

    NAME = None
    _SCHEMA = None

    @property
    def name(self):
        return self.NAME

    @property
    def schema(self):
        # Return a defensive copy so callers cannot mutate schema state.
        return _deep_copy(self._SCHEMA)
