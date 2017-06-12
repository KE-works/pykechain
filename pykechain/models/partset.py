from typing import Sized, Any, Iterable  # flake8: noqa

from pykechain.models.part import Part


class PartSet(Sized):
    """A set of KE-chain parts.

    Adding set-like methods on a list of parts:
     * iterable
     * len()
     * get()
     * iPython notebook support for HTML table
    """

    def __init__(self, parts):
        # type: (Iterable[Part]) -> None
        """Construct a PartSet from a part iterable."""
        self._parts = list(parts)
        self._iter = iter(self._parts)

    def __repr__(self):  # pragma: no cover
        return "<pyke {} object {} parts>".format(self.__class__.__name__, self.__len__())

    def __iter__(self):
        return self

    def __len__(self):
        return len(self._parts)

    def __next__(self):
        # py3.4 and up style next
        return next(self._iter)

    next = __next__  # py2.7 alias

    def __getitem__(self, k):
        # type: (Any) -> Part
        if isinstance(k, int):
            return self._parts[k]

        raise NotImplementedError

    def _repr_html_(self):
        # type: () -> str
        all_instances = all(p.category == 'INSTANCE' for p in self._parts)

        html = [
            "<table width=100%>",
            "<tr>",
            "<th>Part</th>"
        ]

        if not all_instances:
            html.append("<th>Category</th>")

        html.append("<th>ID</th>")
        html.append("</tr>")

        for part in self._parts:
            html.append("<tr>")
            html.append("<td>{}</td>".format(part.name))

            if not all_instances:
                html.append("<td>{}</td>".format(part.category))

            html.append("<td>{}</td>".format(part.id))
            html.append("</tr>")

        html.append("</table>")

        return ''.join(html)
