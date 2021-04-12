import datetime
import os
from typing import Dict, Optional, Text

import requests

from pykechain.exceptions import APIError
from pykechain.models import Base
from pykechain.models.input_checks import check_type
from pykechain.utils import empty, clean_empty_values


class ExpiringDownload(Base):
    """Expiring Download class."""

    def __init__(self, json: Dict, **kwargs) -> None:
        """
        Init function.

        :param json: the json response to construct the :class:`ExpiringDownload` from
        :type json: dict
        """
        super().__init__(json, **kwargs)
        self.filename = json.get('content_file_name')
        self.expires_in = json.get('expires_in')
        self.expires_at = json.get('expires_at')
        self.token_hint = json.get('token_hint')

    def __repr__(self):  # pragma: no cover
        return "<pyke ExpiringDownload id {}>".format(self.id[-8:])

    def save_as(self, target_dir: Optional[Text] = None) -> None:
        """
        Save the Expiring Download content.

        :param target_dir: the target directory where the file will be stored
        :type target_dir: str
        """
        full_path = os.path.join(target_dir or os.getcwd(), self.filename)

        url = self._client._build_url('expiring_download_download', download_id=self.id)
        response = self._client._request('GET', url)
        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not download file from Expiring download {}".format(self), response=response)

        with open(full_path, 'w+b') as f:
            for chunk in response:
                f.write(chunk)

    def delete(self) -> None:
        """Delete this expiring download.

        :raises APIError: if delete was not successful.
        """
        response = self._client._request('DELETE', self._client._build_url('expiring_download', download_id=self.id))

        if response.status_code != requests.codes.no_content:  # pragma: no cover
            raise APIError("Could not delete Expiring Download {}".format(self), response=response)

    def edit(
            self,
            expires_at: Optional[datetime.datetime] = empty,
            expires_in: Optional[int] = empty,
            **kwargs
    ) -> None:
        """
        Edit Expiring Download details.

        :param expires_at: The moment at which the ExpiringDownload will expire
        :type expires_at: datetime.datetime
        :param expires_in: The amount of time (in seconds) in which the ExpiringDownload will expire
        :type expires_in: int
        """
        update_dict = {
            'id': self.id,
            'expires_at': check_type(expires_at, datetime.datetime, 'expires_at') or self.expires_at,
            'expires_in': check_type(expires_in, int, 'expires_in') or self.expires_in
        }

        if kwargs:  # pragma: no cover
            update_dict.update(**kwargs)

        update_dict = clean_empty_values(update_dict=update_dict)

        response = self._client._request('PUT', self._client._build_url('expiring_download', download_id=self.id),
                                         json=update_dict)

        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not update Expiring Download {}".format(self), response=response)

        self.refresh(json=response.json()['results'][0])

    def upload(self, content_path):
        """
        Upload a file to the Expiring Download.

        .. versionadded:: 3.10.0

        :param content_path: path to the file to upload.
        :type content_path: basestring
        :raises APIError: if the file could not be uploaded.
        :raises OSError: if the file could not be located on disk.
        """
        if os.path.exists(content_path):
            self._upload(content_path=content_path)
        else:
            raise OSError("Could not locate file to upload in '{}'".format(content_path))

    def _upload(self, content_path):
        url = self._client._build_url('expiring_download_upload', download_id=self.id)

        with open(content_path, 'rb') as file:
            response = self._client._request(
                'POST', url,
                files={'attachment': (os.path.basename(content_path), file)}
            )

        if response.status_code not in (requests.codes.accepted, requests.codes.ok):  # pragma: no cover
            raise APIError("Could not upload  file to Expiring Download {}".format(self), response=response)

        self.refresh(json=response.json()['results'][0])
