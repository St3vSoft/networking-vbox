from oslo_config import cfg


network_opts = [
    cfg.ListOpt(
        'network_mappings',
        default=[],
        help='VirtualBox physical network mappings'
    )
]

virtualbox_opts = [
    cfg.StrOpt(
        'api_url',
        default='http://192.168.1.12:8000'
    ),
    cfg.StrOpt(
        'api_key',
        default='',
        secret=True
    ),
    cfg.IntOpt(
        'api_timeout',
        default=10
    )
]


def register_opts():

    cfg.CONF.register_opts(
        network_opts,
        group='network'
    )

    cfg.CONF.register_opts(
        virtualbox_opts,
        group='virtualbox'
    )