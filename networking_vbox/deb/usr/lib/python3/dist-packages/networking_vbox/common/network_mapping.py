
from oslo_log import log

LOG = log.getLogger(__name__)


class NetworkMapping:

    def __init__(self, mappings):

        self.mappings = {}

        for mapping in mappings:

            parts = [
                part.strip()
                for part in mapping.split(':', 3)
            ]

            if len(parts) != 4 or not all(parts):
                LOG.warning(
                    "Invalid network mapping: %s",
                    mapping
                )
                continue

            physnet, interface, mode, network = parts

            if physnet in self.mappings:
                raise ValueError(
                    f"Duplicate physnet mapping: {physnet}"
                )

            self.mappings[physnet] = {
                'interface': interface,
                'mode': mode,
                'virtualbox_network': network
            }

    def get_mapping(self, physnet):
        return self.mappings.get(physnet)

    def get_all_mappings(self):
        return self.mappings
