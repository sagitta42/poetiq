import enum

from pydantic import BaseModel

from poetiq.logger import logg


class Tree(enum.StrEnum):
    space = "    "
    branch = "|   "
    tee = "├── "
    final = "└── "


class TreeBaseModel(BaseModel):
    """
    Base model with tree display.
    """

    def display(
        self,
        log: bool = True,
        debug: bool = False,
        header: str | None = None,
        value: str = "=",
        tee: str = Tree.tee.value,
        final: str = Tree.final.value,
    ) -> str | None:
        display_str = self._display(value, tee, final)
        if header is not None:
            display_str = f"{header}\n{display_str}"
        if log:
            log_call = logg.debug if debug else logg.info
            log_call(display_str)
            return
        return display_str

    def _display(
        self,
        value: str = "=",
        tee: str = Tree.tee.value,
        final: str = Tree.final.value,
        _level: int = 0,
        _is_final=False,
    ) -> str:
        """
        Display in tree-style hierarchy.

        value: symbol used to show values, default =
        tee: symbol used to show intermediate fields, default ├──
        final: symbol used to show final fields, default └──

        _level: used for recursion to represent tree level (impacts indents and tree markers)
        _is_final: used for recursion to signal last level (impacts indents and tree markers)
        """

        n_fields = len(self.__class__.model_fields)
        ret = ""
        for idx, field_name in enumerate(self.__class__.model_fields):
            field = getattr(self, field_name)
            field_allias = self.__class__.model_fields[field_name].alias or field_name
            marker = final if idx == n_fields - 1 else tee
            indent = Tree.space.value if _is_final else Tree.branch.value
            level_indent = _level * indent + marker
            # NOTE: assumes all list entries are of same type (as typical with pydantic)
            if isinstance(field, TreeBaseModel) or (
                isinstance(field, list)
                and len(field) > 0
                and isinstance(field[0], TreeBaseModel)
            ):
                fields = [field] if isinstance(field, TreeBaseModel) else field
                next_is_final = (idx == n_fields - 1) and _level == 0
                ret += f"{level_indent}{field_allias}\n"
                for f in fields:
                    ret += f._display(
                        value,
                        tee,
                        final,
                        _level=_level + 1,
                        _is_final=next_is_final,
                    )
            else:
                ret += f"{level_indent}{field_allias}{value}{field}\n"
        return ret
