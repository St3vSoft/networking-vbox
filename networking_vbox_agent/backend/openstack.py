import requests

class KeystoneClient:

    def __init__(self, config: dict):
        self.config = config
        self.token = None

    def authenticate(self):

        url = self.config["auth_url"].rstrip("/") + "/auth/tokens"

        payload = {
            "auth": {
                "identity": {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "name": self.config["username"],
                            "domain": {
                                "name": self.config["user_domain_name"]
                            },
                            "password": self.config["password"]
                        }
                    }
                },
                "scope": {
                    "project": {
                        "name": self.config["project_name"],
                        "domain": {
                            "name": self.config["project_domain_name"]
                        }
                    }
                }
            }
        }

        response = requests.post(
            url,
            json=payload,
            verify=self.config["verify_ssl"],
            timeout=30
        )

        response.raise_for_status()

        self.token = response.headers["X-Subject-Token"]

        return self.token

class NeutronClient:

    def __init__(self, config: dict):
        self.config = config
        self.keystone = KeystoneClient(config)

    def get_networks(self):

        token = self.keystone.authenticate()

        url = self.config["neutron_url"].rstrip("/") + "/v2.0/networks"

        headers = {
            "X-Auth-Token": token,
            "Accept": "application/json"
        }

        networks = []

        while url:
            response = requests.get(
                url,
                headers=headers,
                verify=self.config["verify_ssl"],
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            networks.extend(data.get("networks", []))

            # Gestione paginazione Neutron
            url = data.get("networks_links", [])

            url = next(
                (
                    link["href"]
                    for link in url
                    if link.get("rel") == "next"
                ),
                None
            )

        return networks

    def get_flat_networks(self):

        networks = self.get_networks()

        return [
            network
            for network in networks
            if network.get("provider:network_type") == "flat"
        ]