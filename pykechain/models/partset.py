from typing import Iterable, Text  # noqa: F401

from pykechain.models.part import Part  # noqa: F401


class PartSet(Iterable):
    """A set of KE-chain parts.

    Adding set-like methods on a list of parts:
     * iterable
     * len()
     * get()
     * iPython notebook support for HTML table
    """

    def __init__(self, parts: Iterable[Part]):
        """Construct a PartSet from a part iterable."""
        self._parts = list(parts)

    def __repr__(self):  # pragma: no cover
        return f"<pyke {self.__class__.__name__} object {self.__len__()} parts>"

    def __iter__(self):
        return iter(self._parts)

    def __len__(self):
        return len(self._parts)

    def __getitem__(self, k: int) -> Part:
        if isinstance(k, int):
            return self._parts[k]

        raise NotImplementedError

    def _repr_html_(self) -> str:
        all_instances = all(p.category == "INSTANCE" for p in self._parts)

        html = ["<table width=100%>", "<tr>", "<th>Part</th>"]

        if not all_instances:
            html.append("<th>Category</th>")

        html.append("<th>ID</th>")
        html.append("</tr>")

        for part in self._parts:
            html.append("<tr>")
            html.append(f"<td>{part.name}</td>")

            if not all_instances:
                html.append(f"<td>{part.category}</td>")

            html.append(f"<td>{part.id}</td>")
            html.append("</tr>")

        html.append("</table>")

        return "".join(html)
