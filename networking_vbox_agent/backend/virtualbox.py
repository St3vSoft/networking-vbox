import subprocess
import re

from pydantic import BaseModel, Field

class AttachInterfaceRequest(BaseModel):
    physnet: str
    adapter: int = Field(default=1, ge=1, le=8)
    nic_type: str = "82540EM"
    mac_address: str

class AttachNatRequest(BaseModel):
    adapter: int = Field(default=1, ge=1, le=8)

class VirtualBoxManager:
    def __init__(self, config: dict[str, any]):
        self.agent_config = config

        self.vboxmanage_cmd = config["virtualbox"]["vboxmanage"]
        self.cmd_timeout = config["virtualbox"]["command_timeout"]
        self.controller_vm = config["virtualbox"]["controller_vm"]

        self.network_mappings = self._parse_network_mappings(
            config["network"]["network_mappings"]
        )

    def _parse_network_mappings(self, mappings: str) -> dict:
        result = {}

        for mapping in mappings.split(","):
            parts = mapping.strip().split(":", 3)

            if len(parts) != 4:
                raise ValueError(
                    f"Invalid network mapping: {mapping}"
                )

            physnet, interface, network_type, network_name = parts

            if physnet in result:
                raise ValueError(f"Duplicate physnet: {physnet}")

            result[physnet] = {
                "interface": interface,
                "type": network_type,
                "network_name": network_name
            }

        return result

    def get_available_adapter(self, vm_uuid: str) -> int | None:

        output = self.get_vm_info(vm_uuid)

        adapters = {}

        for line in output.splitlines():

            if "=" not in line:
                continue

            key, value = line.split("=", 1)

            key = key.strip().strip('"')
            value = value.strip().strip('"')

            match = re.fullmatch(r"nic(\d+)", key)

            if match:
                adapters[int(match.group(1))] = value

        for adapter in range(1, 9):

            if adapters.get(adapter, "none") == "none":
                return adapter

        return None

    def parse_flat_networks(self, networks: list[dict]) -> list[dict]:

        flat_networks = []

        for network in networks:

            physnet = network.get(
                "provider:physical_network"
            )

            if not physnet:
                continue

            mapping = self.get_physnet_mapping(physnet)

            flat_networks.append({
                "id": network["id"],
                "name": network["name"],
                "physnet": physnet,
                "interface": mapping["interface"],
                "interface_type": mapping["type"],
                "network_name": mapping["network_name"],
                "status": network.get("status"),
                "admin_state_up": network.get("admin_state_up"),
                "shared": network.get("shared")
            })

        return flat_networks

    def get_controller_info(self):
        return self.execute(
            "showvminfo",
            self.controller_vm,
            "--machinereadable"
        )

    def get_controller_adapters(self):

        output = self.get_controller_info()

        adapters = {}

        for line in output.splitlines():

            if "=" not in line:
                continue

            key, value = line.split("=", 1)

            adapters[key.strip().strip('"')] = (
                value.strip().strip('"')
            )

        return adapters

    def get_physnet_mapping(self, physnet):
        mapping = self.network_mappings.get(physnet)

        if not mapping:
            raise ValueError(
                f"No network mapping configured for physnet: {physnet}"
            )

        return mapping

    def get_network_mapping(self):

        adapters = self.get_controller_adapters()

        mapping = []

        for key, mode in adapters.items():

            match = re.fullmatch(r"nic(\d+)", key)

            if not match:
                continue

            slot = match.group(1)

            if mode == "none":
                continue

            if mode == "hostonly":
                network = adapters.get(f"hostonlyadapter{slot}")

            elif mode == "bridged":
                network = adapters.get(f"bridgeadapter{slot}")

            elif mode == "natnetwork":
                network = adapters.get(f"nat-network{slot}")

            elif mode == "nat":
                network = "NAT"

            elif mode == "internal":
                network = adapters.get(f"intnet{slot}")

            else:
                network = None

            mapping.append({
                "slot": int(slot),
                "mode": mode,
                "network": network,
                "mac": adapters.get(f"macaddress{slot}"),
                "adapter_type": adapters.get(f"nictype{slot}"),
                "cable_connected": (
                    adapters.get(f"cableconnected{slot}", "off") == "on"
                )
            })

        return mapping

    def execute(self, *args):

        result = subprocess.run(
            [self.vboxmanage_cmd, *args],
            capture_output=True,
            text=True,
            timeout=int(self.cmd_timeout),
            check=True
        )

        return result.stdout.strip()

    def list_vms(self):
        return self.execute("list", "vms")

    def list_running_vms(self):
        return self.execute("list", "runningvms")

    def detach_interface(self, vm_uuid: str, adapter: int = 1):
        return self.execute("modifyvm", vm_uuid, f"--nic{adapter}", "none")

    def attach_physnet(
        self,
        vm_uuid: str,
        physnet: str,
        adapter: int = 1,
        nic_type: str = "82540EM",
        mac_address: str | None = None
    ):
        if not 1 <= adapter <= 8:
            raise ValueError("Adapter must be between 1 and 8")

        mapping = self.get_physnet_mapping(physnet)

        interface_type = mapping["type"]
        network_name = mapping["network_name"]

        args = [
            "modifyvm",
            vm_uuid,
            f"--nic{adapter}",
            interface_type,
            f"--nictype{adapter}",
            nic_type,
            f"--cableconnected{adapter}",
            "on"
        ]

        if mac_address:
            if not re.fullmatch(r"[0-9a-fA-F]{12}", mac_address):
                raise ValueError("Invalid MAC address")

            args.extend([
                f"--macaddress{adapter}",
                mac_address
            ])

        if interface_type == "bridged":
            args.extend([
                f"--bridge-adapter{adapter}",
                network_name
            ])

        elif interface_type == "hostonly":
            args.extend([
                f"--host-only-adapter{adapter}",
                network_name
            ])

        elif interface_type == "natnetwork":
            args.extend([
                f"--nat-network{adapter}",
                network_name
            ])

        else:
            raise ValueError(
                f"Unsupported network type: {interface_type}"
            )

        return self.execute(*args)

    def detach_physnet(
        self,
        vm_uuid: str,
        adapter: int
    ):
        if not 1 <= adapter <= 8:
            raise ValueError("Adapter must be between 1 and 8")

        return self.execute(
            "modifyvm",
            vm_uuid,
            f"--nic{adapter}",
            "none"
        )

    def attach_interface(
        self,
        vm_uuid: str,
        interface_type: str = "nat",
        adapter: int = 1,
        nic_type: str = "82540EM",
        network_name: str | None = None
    ):
        if not 1 <= adapter <= 8:
            raise ValueError("Adapter must be between 1 and 8")

        if interface_type not in ("nat", "bridged", "hostonly", "intnet"):
            raise ValueError("Unsupported interface type")

        args = [
            "modifyvm",
            vm_uuid,
            f"--nic{adapter}",
            interface_type,
            f"--nictype{adapter}",
            nic_type,
            f"--cableconnected{adapter}",
            "on"
        ]

        if interface_type == "bridged":
            if not network_name:
                raise ValueError("Bridged requires a physical interface name")

            args.extend([
                f"--bridge-adapter{adapter}",
                network_name
            ])

        elif interface_type == "hostonly":
            if not network_name:
                raise ValueError("Host-only requires a host-only interface name")

            args.extend([
                f"--host-only-adapter{adapter}",
                network_name
            ])

        elif interface_type == "intnet":
            if not network_name:
                raise ValueError("Internal network requires a network name")

            args.extend([
                f"--intnet{adapter}",
                network_name
            ])

        return self.execute(*args)

    def get_vm_info(self, uuid):
        return self.execute(
            "showvminfo",
            uuid,
            "--machinereadable"
        )
