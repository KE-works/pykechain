import io

from pykechain.exceptions import APIError
from pykechain.models import Property


class AttachmentProperty(Property):
    """A virtual object representing a KE-chain attachment property."""

    @property
    def value(self):
        """Data value of this attachment.

        Use save_as in order to download as a file.
        """
        return '[Attachment]'

    @value.setter
    def value(self, value):
        try:
            import matplotlib.figure

            if isinstance(value, matplotlib.figure.Figure):
                self._attach_plot(value)
                return
        except ImportError:
            pass

    def save_as(self, filename):
        """Download the attachment to a file.

        :param filename: File path
        :raises: APIError
        """
        with open(filename, 'wb') as f:
            for chunk in self._download():
                f.write(chunk)

    def _download(self):
        url = self._client._build_url('property_download', property_id=self.id)

        r = self._client._request('GET', url)

        if r.status_code != 200:
            raise APIError("Could not download property value")

        return r

    def _upload(self, data):
        url = self._client._build_url('property_upload', property_id=self.id)

        r = self._client._request('POST', url,
                                  data={"part": self._json_data['part']},
                                  files={"attachment": data})

        if r.status_code != 200:
            raise APIError("Could not upload attachment")

    def _attach_plot(self, figure):
        buffer = io.BytesIO()

        figure.savefig(buffer, format="png")

        data = ('plot.png', buffer.getvalue(), 'image/png')

        self._upload(data)
