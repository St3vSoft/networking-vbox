
import requests

from oslo_log import log

LOG = log.getLogger(__name__)


class VirtualBoxRESTClient:

    def __init__(self, endpoint, api_key=None, timeout=10):

        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout

    def _request(self, method, path):

        headers = {}

        if self.api_key:
            headers['X-API-Key'] = self.api_key

        response = requests.request(
            method,
            f"{self.endpoint}{path}",
            headers=headers,
            timeout=self.timeout
        )

        response.raise_for_status()

        return response.json()

    def get_controller_networks(self):

        return self._request(
            'GET',
            '/controller/networks'
        )

    def get_network_by_slot(self, slot):

        networks = self.get_controller_networks()

        for network in networks.get('networks', []):

            if network['slot'] == slot:
                return network

        return None
