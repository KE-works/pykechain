import os
from typing import Dict

import requests

from pykechain.exceptions import APIError
from pykechain.models import Base


class ExpiringDownload(Base):
    """
    Expiring Download class
    """
    def __init__(self, json: Dict, **kwargs) -> None:
        super().__init__(json, **kwargs)

        self.expires_in = json.get('expires_in')
        self.expires_at = json.get('expires_at')
        self.token_hint = json.get('token_hint')

    def __repr__(self):  # pragma: no cover
        return "<pyke ExpiringDownload id {}>".format(self.id[-8:])

    # def upload(self, content_path):
    #
    #     if os.path.exists(content_path):
    #         self._upload(content_path=content_path)
    #     else:
    #         raise OSError("Could not locate file to upload at the path '{}'".format(content_path))
    #
    # def _upload(self, content_path):
    #     url = self._client._build_url('service_upload', service_id=self.id)
    #
    #     with open(pkg_path, 'rb') as pkg:
    #         response = self._client._request(
    #             'POST', url,
    #             files={'attachment': (os.path.basename(pkg_path), pkg)}
    #         )
    #
    #     if response.status_code != requests.codes.accepted:  # pragma: no cover
    #         raise APIError("Could not upload script file (or kecpkg) to Service {}".format(self), response=response)
    #
    #     self.refresh(json=response.json()['results'][0])

    def save_as(self, target_dir=None):
        """
        Saves the Expiring Download content.

        :param target_dir:
        :return:
        """
        full_path = os.path.join(target_dir or os.getcwd(), "filename_content")

        url = self._client._build_url('expiring_download_download', download_id=self.id)
        response = self._client._request('GET', url)
        if response.status_code != requests.codes.ok:  # pragma: no cover
            raise APIError("Could not download file from Expiring download {}".format(self), response=response)

        with open(full_path, 'w+b') as f:
            for chunk in response:
                f.write(chunk)
