import configparser

def read_config(file_path) -> dict[str, any]:

    config = configparser.ConfigParser()

    if not config.read(file_path):
        raise RuntimeError(
            f"Configuration file not found: {file_path}"
        )

    settings = {
        "server": {
            "host": config.get(
                "server", "host", fallback="127.0.0.1"
            ),
            "port": config.getint(
                "server", "port", fallback=8000
            ),
            "workers": config.getint(
                "server", "workers", fallback=1
            )
        },

        "openstack": {
            "auth_url": config.get("openstack", "auth_url"),
            "username": config.get("openstack", "username"),
            "password": config.get("openstack", "password"),
            "project_name": config.get("openstack", "project_name"),
            "user_domain_name": config.get(
                "openstack", "user_domain_name", fallback="Default"
            ),
            "project_domain_name": config.get(
                "openstack", "project_domain_name", fallback="Default"
            ),
            "region_name": config.get(
                "openstack", "region_name", fallback="RegionOne"
            ),
            "interface": config.get(
                "openstack", "interface", fallback="internal"
            ),
            "verify_ssl": config.getboolean(
                "openstack", "verify_ssl", fallback=True
            ),
            "neutron_url": config.get("openstack", "neutron_url")
        },

        "virtualbox": {
            "vboxmanage": config.get(
                "virtualbox", "vboxmanage"
            ),
            "command_timeout": config.getint(
                "virtualbox", "command_timeout",
                fallback=30
            ),
            "controller_vm": config.get(
                "virtualbox", "controller_vm", fallback=""
            ),
        },

        "network": {
            "network_mappings": config.get(
                "network", "network_mappings",
                fallback=""
            )
        },

        "security": {
            "authentication": config.getboolean(
                "security", "authentication",
                fallback=True
            ),
            "api_key": config.get(
                "security", "api_key", fallback=""
            )
        },

        "logging": {
            "level": config.get(
                "logging", "level", fallback="INFO"
            ),
            "file": config.get(
                "logging", "file",
                fallback="logs/vmrest.log"
            )
        }
    }

    return settings