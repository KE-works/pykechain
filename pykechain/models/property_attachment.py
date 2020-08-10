import io
import json

import requests
from six import string_types, text_type

from pykechain.exceptions import APIError
from pykechain.models.property import Property


class AttachmentProperty(Property):  # pragma: no cover
    """
    A virtual object representing a KE-chain attachment property.

    :ivar type: The property type of the property. One of the types described in :class:`pykechain.enums.PropertyType`
    :type type: str
    :ivar output: a boolean if the value is configured as an output (in an activity)
    :type output: bool
    :ivar part: The (parent) part in which this property is available
    :type part: :class:`Part`
    :ivar value: the property value, can be set as well as property
    :type value: Any
    :ivar filename: the filename and extension of the attachment
    :type filename: str or None
    :ivar validators: the list of validators that are available in the property
    :type validators: list(PropertyValidator)
    :ivar is_valid: if the property conforms to the validators
    :type is_valid: bool
    :ivar is_invalid: if the property does not conform to the validator
    :type is_invalid: bool
    """

    @property
    def value(self):
        """Retrieve the data value of this attachment.

        Will show the filename of the attachment if there is an attachment available otherwise None
        Use save_as in order to download as a file.

        Example
        -------
        >>> file_attachment_property = project.part('Bike').property('file_attachment')
        >>> if file_attachment_property.value:
        ...     file_attachment_property.save_as('file.ext')
        ... else:
        ...     print('file attachment not set, its value is None')

        """
        if 'value' in self._json_data and self._json_data['value']:
            return "[Attachment: {}]".format(self._json_data['value'].split('/')[-1])
        else:
            return None

    @value.setter
    def value(self, value):
        raise RuntimeError("Cannot set the value of an attachment property, use upload() to upload a new attachment or "
                           "clear() to clear the attachment from the field")

    def clear(self):
        """Clear the attachment from the attachment field.

        :raises APIError: if unable to remove the attachment
        """
        if self._put_value(None) is None:
            self._value = None
            self._json_data['value'] = None

    @property
    def filename(self):
        """Filename of the attachment, without the full 'attachment' path."""
        if self.value and 'value' in self._json_data and self._json_data['value']:
            return self._json_data['value'].split('/')[-1]
        return None

    def json_load(self):
        """Download the data from the attachment and deserialise the contained json.

        :return: deserialised json data as :class:`dict`
        :raises APIError: When unable to retrieve the json from KE-chain
        :raises JSONDecodeError: When there was a problem in deserialising the json

        Example
        -------
        Ensure that the attachment is valid json data

        >>> json_attachment = project.part('Bike').property('json_attachment')
        >>> deserialised_json = json_attachment.json_load()

        """
        return self._download().json()

    def upload(self, data, **kwargs):
        """Upload a file to the attachment property.

        When providing a :class:`matplotlib.figure.Figure` object as data, the figure is uploaded as PNG.
        For this, `matplotlib`_ should be installed.

        :param filename: File path
        :type filename: basestring
        :raises APIError: When unable to upload the file to KE-chain
        :raises OSError: When the path to the file is incorrect or file could not be found

        .. _matplotlib: https://matplotlib.org/
        """
        try:
            import matplotlib.figure

            if isinstance(data, matplotlib.figure.Figure):
                self._upload_plot(data, **kwargs)
                return
        except ImportError:
            pass

        if isinstance(data, (string_types, text_type)):
            with open(data, 'rb') as fp:
                self._upload(fp)
        else:
            self._upload_json(data, **kwargs)

    def save_as(self, filename):
        """Download the attachment to a file.

        :param filename: File path
        :type filename: basestring
        :raises APIError: When unable to download the data
        :raises OSError: When unable to save the data to disk
        """
        with open(filename, 'w+b') as f:
            for chunk in self._download():
                f.write(chunk)

    def _download(self):
        url = self._client._build_url('property_download', property_id=self.id)

        response = self._client._request('GET', url)

        if response.status_code != requests.codes.ok:
            raise APIError("Could not download property value")

        return response

    def _upload(self, data):
        url = self._client._build_url('property_upload', property_id=self.id)

        response = self._client._request('POST', url,
                                         data={"part": self._json_data['part']},
                                         files={"attachment": data})

        if response.status_code != requests.codes.ok:
            raise APIError("Could not upload attachment")

    def _upload_json(self, content, name='data.json'):
        data = (name, json.dumps(content), 'application/json')

        self._upload(data)

    def _upload_plot(self, figure, name='plot.png'):
        buffer = io.BytesIO()

        figure.savefig(buffer, format="png")

        data = (name, buffer.getvalue(), 'image/png')

        self._upload(data)
