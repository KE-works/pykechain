

class PartSet(object):

    def __init__(self, parts):
        self._parts = list(parts)

    def __iter__(self):
        return self._parts.__iter__()

    def __len__(self):
        return len(self._parts)

    def __getitem__(self, k):
        assert isinstance(k, int), "[not implemented] non-integer indexing in PartSet"

        return self._parts[k]

    def _repr_html_(self):
        from .api import api_url

        html = []

        html.append("<table width=100%>")

        html.append("<tr>")
        html.append("<th>Part</th>")
        html.append("<th>ID</th>")
        html.append("</tr>")

        for part in self:
            html.append("<tr>")
            html.append("<td>{}</td>".format(part.name))
            html.append("<td><a target='_blank' href={}>".format(api_url('part', part_id=part.id)))
            html.append("{}</a></td>".format(part.id))
            html.append("</tr>")

        html.append("</table>")

        return '' .join(html)
