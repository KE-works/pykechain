

class PartSet(object):

    def __init__(self, parts, client=None):
        self._client = client

        self._parts = list(parts)

    def __iter__(self):
        return self._parts.__iter__()

    def __len__(self):
        return len(self._parts)

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

            html.append("<td><a target='_blank' href={}>".format(self._client._build_url('part', part_id=part.id)))
            html.append("{}</a></td>".format(part.id))
            html.append("</tr>")

        html.append("</table>")

        return '' .join(html)
