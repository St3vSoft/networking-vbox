import abc

from neutron_lib import constants as n_const
from neutron_lib.api.definitions import portbindings
from neutron_lib.plugins.ml2 import api

from oslo_config import cfg
from oslo_log import log

from . import config
from .common.network_mapping import NetworkMapping
from .common.vmrest_client import VirtualBoxRESTClient

LOG = log.getLogger(__name__)


class VirtualBoxMechanismDriver(api.MechanismDriver):

    def __init__(self):
        super().__init__()
        self.network_mapping = None

    def initialize(self):

        LOG.info("Initializing VirtualBox ML2 Mechanism Driver")

        config.register_opts()

        self.network_mapping = NetworkMapping(
            cfg.CONF.network.network_mappings
        )

        self.rest_client = VirtualBoxRESTClient(
            endpoint=cfg.CONF.virtualbox.api_url,
            api_key=cfg.CONF.virtualbox.api_key,
            timeout=cfg.CONF.virtualbox.api_timeout
        )

        LOG.info(
            "Loaded VirtualBox mappings: %s",
            self.network_mapping.get_all_mappings()
        )

    def bind_port(self, context):

        port = context.current

        LOG.debug(
            "VirtualBox binding requested for port %s",
            port['id']
        )

        vnic_type = port.get(
            portbindings.VNIC_TYPE,
            portbindings.VNIC_NORMAL
        )

        if vnic_type != portbindings.VNIC_NORMAL:
            LOG.debug(
                "Unsupported VNIC type: %s",
                vnic_type
            )
            return

        for segment in context.segments_to_bind:

            network_type = segment[api.NETWORK_TYPE]

            # Per ora supportiamo esclusivamente flat
            if network_type != n_const.TYPE_FLAT:
                LOG.debug(
                    "Unsupported network type: %s",
                    network_type
                )
                continue

            physnet = segment.get(api.PHYSICAL_NETWORK)

            if not physnet:
                continue

            mapping = self.network_mapping.get_mapping(
                physnet
            )

            if not mapping:
                LOG.debug(
                    "No VirtualBox mapping for physnet %s",
                    physnet
                )
                continue

            LOG.info(
                "Binding port %(port)s using physnet "
                "%(physnet)s and interface %(interface)s",
                {
                    'port': port['id'],
                    'physnet': physnet,
                    'interface': mapping['interface']
                }
            )

            context.set_binding(
                segment[api.ID],
                portbindings.VIF_TYPE_OTHER,
                {
                    'physical_network': physnet,
                    'interface': mapping['interface'],
                    'network_mode': mapping['mode'],
                    'network': mapping['virtualbox_network']
                }
            )

            return

class SimpleAgentMechanismDriverBase(
    VirtualBoxMechanismDriver,
    metaclass=abc.ABCMeta
):

    def __init__(
        self,
        agent_type,
        vif_type,
        vif_details,
        supported_vnic_types=None
    ):

        super().__init__(
            agent_type,
            supported_vnic_types
        )

        self.vif_type = vif_type
        self.vif_details = vif_details

    def try_to_bind_segment_for_agent(
        self, context, segment, agent
    ):

        if self.check_segment_for_agent(segment, agent):

            context.set_binding(
                segment[api.ID],
                self.vif_type,
                self.vif_details
            )

            return True

        return False

    @abc.abstractmethod
    def get_allowed_network_types(self, agent=None):
        raise NotImplementedError

    @abc.abstractmethod
    def get_mappings(self, agent):
        raise NotImplementedError

    def physnet_in_mappings(self, physnet, mappings):
        return physnet in mappings

    def check_segment_for_agent(self, segment, agent):

        mappings = self.get_mappings(agent)

        allowed_network_types = (
            self.get_allowed_network_types(agent)
        )

        network_type = segment[api.NETWORK_TYPE]

        LOG.debug(
            "Checking segment %(segment)s, mappings %(mappings)s, "
            "network types %(network_types)s",
            {
                'segment': segment,
                'mappings': mappings,
                'network_types': allowed_network_types
            }
        )

        if network_type not in allowed_network_types:

            LOG.debug(
                "Network segment %(segment)s has unsupported "
                "network type %(network_type)s",
                {
                    'segment': segment[api.ID],
                    'network_type': network_type
                }
            )

            return False

        if network_type in (
            n_const.TYPE_FLAT,
            n_const.TYPE_VLAN
        ):

            physnet = segment[api.PHYSICAL_NETWORK]

            if not self.physnet_in_mappings(
                physnet, mappings
            ):

                LOG.debug(
                    "Physical network %(physnet)s not present "
                    "in agent mappings %(mappings)s",
                    {
                        'physnet': physnet,
                        'mappings': mappings
                    }
                )

                return False

        return True