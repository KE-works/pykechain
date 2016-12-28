
class PartSet(object):
    """
    A Set of Parts

    Adding set-like methods on a list of parts:
     * iterable
     * len()
     * get()
     * iPython notebook support for HTML table
    """

    def __init__(self, parts):
        self._parts = list(parts)
        self._iter = iter(self._parts)

    def __iter__(self):
        return self

    def __len__(self):
        return len(self._parts)

    def __next__(self):
        # py3.4 and up style next
        return next(self._iter)

    def next(self):
        # py27 style next
        return self.__next__()

    def __getitem__(self, k):
        if isinstance(k, int):
            return self._parts[k]

        return [p.property(k).value for p in self._parts]

    def _repr_html_(self):
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

        for part in self:
            html.append("<tr>")
            html.append("<td>{}</td>".format(part.name))

            if not all_instances:
                html.append("<td>{}</td>".format(part.category))

            html.append("<td>{}</td>".format(part.id))
            html.append("</tr>")

        html.append("</table>")

        return '' .join(html)
