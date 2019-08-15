# -*- coding: utf-8 -*-
#
# This file is part of DataCite.
#
# Copyright (C) 2015 CERN.
#
# DataCite is free software; you can redistribute it and/or modify it
# under the terms of the Revised BSD License; see LICENSE file for
# more details.

"""Python API client wrapper for the DataCite Metadata Store API.

API documentation is available on https://mds.datacite.org/static/apidoc.
"""

from __future__ import absolute_import, print_function

from .errors import DataCiteError
from .request import DataCiteRequest


class DataCiteRESTClient(object):
    """DataCite REST API client wrapper."""

    def __init__(self, username=None, password=None, url=None, prefix=None,
                 test_mode=False, api_ver="2", timeout=None):
        """Initialize the REST client wrapper.

        :param username: DataCite username.
        :param password: DataCite password.
        :param url: DataCite API base URL. Defaults to
            https://api.datacite.org/.
        :param test_mode: Set to True to change base url to
        https://api.test.datacite.prg. Defaults to False.
        :param prefix: DOI prefix (or CFG_DATACITE_DOI_PREFIX).
        :param api_ver: DataCite API version. Currently has no effect.
            Default to 2.
        :param timeout: Connect and read timeout in seconds. Specify a tuple
            (connect, read) to specify each timeout individually.
        """
        self.username = username
        self.password = password
        self.prefix = prefix
        self.api_ver = api_ver  # Currently not used

        if test_mode:
            self.api_url = 'https://api.test.datacite.org/'
        else:
            self.api_url = url or 'https://api.datacite.org/'
        if self.api_url[-1] != '/':
            self.api_url = self.api_url + "/"

        self.timeout = timeout

    def __repr__(self):
        """Create string representation of object."""
        return '<DataCiteMDSClient: {0}>'.format(self.username)

    def _request_factory(self):
        """Create a new Request object."""
        params = {}

        return DataCiteRequest(
            base_url=self.api_url,
            username=self.username,
            password=self.password,
            default_params=params,
            timeout=self.timeout,
        )

    def doi_get(self, doi):
        """Get the URL where the resource pointed by the DOI is located.

        :param doi: DOI name of the resource.
        """
        r = self._request_factory()
        r.get("dois/" + doi)
        if r.code == 200:
            return r.data['attributes']['url']
        else:
            raise DataCiteError.factory(r.code, r.data)

    def draft_doi(self, new_doi=None):
        """Create a draft doi.

        If new_doi is not provided, DataCite
        will automatically create a DOI with a random, 
        recommended DOI suffix
        """
        headers = {'Content-Type': 'content-type: application/vnd.api+json'}
        data = {"data":{"attributes":{"prefix":self.prefix}}}
        if new_doi:
            #If prefix is in doi
            if '/' in new_doi:
                split = doi.split('/')
                if split[0] != self.prefix:
                    #Provided a DOI with the wrong prefix
                    raise ValueError
            else:
                doi = self.prefix +'/'+new_doi
            data = {"data":{"attributes":{"doi":new_doi}}}
        # Use \r\n for HTTP client data.
        body = "\r\n".join(["doi=%s" % new_doi, "url=%s" % location])

        r = self._request_factory()
        r.post("doi", body=body, headers=headers)

        if r.code == 201:
            return r.data
        else:
            raise DataCiteError.factory(r.code, r.data)

    def doi_post(self, new_doi, location):
        """Mint new DOI.

        :param new_doi: DOI name for the new resource.
        :param location: URL where the resource is located.
        :return: "CREATED" or "HANDLE_ALREADY_EXISTS".
        """
        headers = {'Content-Type': 'text/plain;charset=UTF-8'}
        # Use \r\n for HTTP client data.
        body = "\r\n".join(["doi=%s" % new_doi, "url=%s" % location])

        r = self._request_factory()
        r.post("doi", body=body, headers=headers)

        if r.code == 201:
            return r.data
        else:
            raise DataCiteError.factory(r.code, r.data)

    def metadata_get(self, doi):
        """Get the XML metadata associated to a DOI name.

        :param doi: DOI name of the resource.
        """
        headers = {'Accept': 'application/xml',
                   'Accept-Encoding': 'UTF-8'}

        r = self._request_factory()
        r.get("metadata/" + doi, headers=headers)

        if r.code == 200:
            return r.data
        else:
            raise DataCiteError.factory(r.code, r.data)

    def metadata_post(self, metadata):
        """Set new metadata for an existing DOI.

        Metadata should follow the DataCite Metadata Schema:
        http://schema.datacite.org/

        :param metadata: XML format of the metadata.
        :return: "CREATED" or "HANDLE_ALREADY_EXISTS"
        """
        headers = {'Content-Type': 'application/xml;charset=UTF-8', }

        r = self._request_factory()
        r.post("metadata", body=metadata, headers=headers)

        if r.code == 201:
            return r.data
        else:
            raise DataCiteError.factory(r.code, r.data)

    def metadata_delete(self, doi):
        """Mark as 'inactive' the metadata set of a DOI resource.

        :param doi: DOI name of the resource.
        :return: "OK"
        """
        r = self._request_factory()
        r.delete("metadata/" + doi)

        if r.code == 200:
            return r.data
        else:
            raise DataCiteError.factory(r.code, r.data)

    def media_get(self, doi):
        """Get list of pairs of media type and URLs associated with a DOI.

        :param doi: DOI name of the resource.
        """
        r = self._request_factory()
        r.get("media/" + doi)

        if r.code == 200:
            values = {}
            for line in r.data.splitlines():
                mimetype, url = line.split("=", 1)
                values[mimetype] = url
            return values
        else:
            raise DataCiteError.factory(r.code, r.data)

    def media_post(self, doi, media):
        """Add/update media type/urls pairs to a DOI.

        Standard domain restrictions check will be performed.

        :param media: Dictionary of (mime-type, URL) key/value pairs.
        :return: "OK"
        """
        headers = {'Content-Type': 'text/plain;charset=UTF-8'}

        # Use \r\n for HTTP client data.
        body = "\r\n".join(["%s=%s" % (k, v) for k, v in media.items()])

        r = self._request_factory()
        r.post("media/" + doi, body=body, headers=headers)

        if r.code == 200:
            return r.data
        else:
            raise DataCiteError.factory(r.code, r.data)
