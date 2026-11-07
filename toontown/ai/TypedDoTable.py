"""
The district's doId2do, also kept by class.

Offline, one district holds every street, building, cog and NPC toon of the
game: some 4,000 objects. The NPC players and the district asked for "every
object of this kind" by going through all of them, several times a second,
which was most of a once-a-second pause in the frame (11 ms on a PC, several
times that on a phone). This table keeps each object under its class as well,
so that asking for a kind looks at the few classes that match instead of at
every object.
"""


class TypedDoTable(dict):
    """A dict of doId to object that also knows its objects by class.

    Every way the game puts objects in or takes them out goes through here:
    item assignment, del, pop, popitem, setdefault, update and clear.
    """

    def __init__(self, *args, **kwargs):
        dict.__init__(self)
        self._byType = {}
        self._matches = {}
        self.update(*args, **kwargs)

    # --- Keeping the classes up to date ---

    def _add(self, doId, obj):
        kind = type(obj)
        objects = self._byType.get(kind)
        if objects is None:
            objects = self._byType[kind] = {}
            # A class not seen before may match a kind already asked for.
            self._matches.clear()
        objects[doId] = obj

    def _remove(self, doId, obj):
        objects = self._byType.get(type(obj))
        if objects is not None:
            objects.pop(doId, None)

    def __setitem__(self, doId, obj):
        old = dict.get(self, doId)
        if old is not None:
            self._remove(doId, old)
        dict.__setitem__(self, doId, obj)
        self._add(doId, obj)

    def __delitem__(self, doId):
        old = dict.__getitem__(self, doId)
        dict.__delitem__(self, doId)
        self._remove(doId, old)

    _missing = object()

    def pop(self, doId, default=_missing):
        if doId in self:
            old = dict.pop(self, doId)
            self._remove(doId, old)
            return old
        if default is TypedDoTable._missing:
            raise KeyError(doId)
        return default

    def popitem(self):
        doId, old = dict.popitem(self)
        self._remove(doId, old)
        return doId, old

    def setdefault(self, doId, default=None):
        if doId not in self:
            self[doId] = default
        return dict.__getitem__(self, doId)

    def update(self, *args, **kwargs):
        for doId, obj in dict(*args, **kwargs).items():
            self[doId] = obj

    def clear(self):
        dict.clear(self)
        self._byType.clear()
        self._matches.clear()

    def copy(self):
        return dict(self)

    # --- Asking by class ---

    def ofType(self, classes, exclude=None):
        """Every object that is an instance of classes (a class or a tuple
        of them), and not of exclude when given, as a new list."""
        key = (classes, exclude)
        kinds = self._matches.get(key)
        if kinds is None:
            kinds = self._matches[key] = [kind for kind in self._byType if issubclass(kind, classes)
                                          and not (exclude and issubclass(kind, exclude))]
        found = []
        for kind in kinds:
            found.extend(self._byType[kind].values())
        return found


def objectsOfType(air, classes, exclude=None):
    """The district's objects of a kind (leaving out those of exclude): from
    its table by class when it has one, otherwise by going through every
    object."""
    table = air.doId2do
    if isinstance(table, TypedDoTable):
        return table.ofType(classes, exclude)
    return [obj for obj in list(table.values()) if isinstance(obj, classes)
            and not (exclude and isinstance(obj, exclude))]
