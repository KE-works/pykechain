import json
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
        raise RuntimeError("Cannot read the value of an attachment property, use save_as()")

    @value.setter
    def value(self, value):
        raise RuntimeError("Cannot set the value of an attachment property, use upload()")

    def json_load(self):
        """Download the data from the attachment and deserialise the contained json
        
        :return: deserialised json data
        :raises: APIError, JSONDecodeError
        
        Example
        -------
        Ensure that the attachment is valid json data
        
        >>> json_attachment = project.part('Bike').property('json_attachment')
        >>> deserialised_json = json_attachment.json_load()
        """
        return self._download().json()

    def upload(self, data, **kwargs):
        """Upload a file to the attachment property.

        :param filename: File path
        :raises: APIError
        """
        try:
            import matplotlib.figure

            if isinstance(data, matplotlib.figure.Figure):
                self._upload_plot(data, **kwargs)
                return
        except ImportError:
            pass

        if isinstance(data, str):
            with open(data, 'rb') as fp:
                self._upload(fp)
        else:
            self._upload_json(data, **kwargs)

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

    def _upload_json(self, content, name='data.json'):
        data = (name, json.dumps(content), 'application/json')

        self._upload(data)

    def _upload_plot(self, figure, name='plot.png'):
        buffer = io.BytesIO()

        figure.savefig(buffer, format="png")

        data = (name, buffer.getvalue(), 'image/png')

        self._upload(data)
