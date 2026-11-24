import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request

from .backend.virtualbox import VirtualBoxManager, AttachInterfaceRequest
from .backend.openstack import NeutronClient

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Initializing VirtualBox Neutron Agent")

    app.state.vbox = VirtualBoxManager(
        config=app.state.config
    )

    logger.info("VirtualBoxManager initialized")

    app.state.neutron = NeutronClient(
        config=app.state.config["openstack"]
    )

    logger.info("NeutronClient initialized")

    logger.info("VirtualBox Neutron Agent started")

    yield

    logger.info("VirtualBox Neutron Agent shutting down")


app = FastAPI(
    title="VirtualBox Neutron Agent REST Service",
    lifespan=lifespan
)


@app.get("/health")
def health(request: Request):

    logger.info("Health check requested")

    try:
        request.app.state.vbox.list_vms()

        logger.info("Health check successful")

        return {
            "status": "ok",
            "backend": "VBoxManage"
        }

    except Exception:
        logger.exception("Health check failed: VirtualBox unavailable")

        raise HTTPException(
            status_code=503,
            detail="VirtualBox unavailable"
        )


@app.get("/vms")
def list_vms(request: Request):

    logger.info("VM list requested")

    try:
        vbox = request.app.state.vbox

        vms = vbox.list_vms()
        running = vbox.list_running_vms()

        logger.info(
            "VM list retrieved successfully: %d VMs, %d running",
            len(vms),
            len(running)
        )

        return {
            "vms": vms,
            "running": running
        }

    except Exception:
        logger.exception("Unable to retrieve VMs")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve VMs"
        )


@app.get("/controller/networks")
def controller_networks(request: Request):

    logger.info("Controller network mapping requested")

    try:
        vbox = request.app.state.vbox

        networks = vbox.get_network_mapping()

        logger.info("Controller network mapping retrieved successfully")

        return {
            "networks": networks
        }

    except Exception:
        logger.exception("Unable to retrieve controller network mapping")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve controller network mapping"
        )


@app.get("/networks/flat")
def list_flat_networks(request: Request):

    logger.info("Flat Neutron networks requested")

    try:
        neutron = request.app.state.neutron
        vbox = request.app.state.vbox

        networks = neutron.get_flat_networks()

        parsed_networks = vbox.parse_flat_networks(networks)

        logger.info(
            "Flat Neutron networks retrieved successfully: %d networks",
            len(parsed_networks)
        )

        return {
            "networks": parsed_networks
        }

    except Exception:
        logger.exception("Unable to retrieve flat networks")

        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve Neutron networks"
        )


@app.get("/vms/{vm_uuid}")
def get_vm_info(vm_uuid: str, request: Request):

    logger.info("VM information requested: vm_uuid=%s", vm_uuid)

    try:
        vbox = request.app.state.vbox

        vm = vbox.get_vm_info(vm_uuid)

        logger.info(
            "VM information retrieved successfully: vm_uuid=%s",
            vm_uuid
        )

        return {
            "vm": vm
        }

    except ValueError as exc:

        logger.warning(
            "VM not found or invalid UUID: vm_uuid=%s, error=%s",
            vm_uuid,
            exc
        )

        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )

    except Exception:
        logger.exception(
            "Unable to retrieve VM information: vm_uuid=%s",
            vm_uuid
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve VM information"
        )


@app.get("/vms/{vm_uuid}/interfaces/available")
def get_available_adapter(vm_uuid: str, request: Request):

    logger.info(
        "Available network adapter requested: vm_uuid=%s",
        vm_uuid
    )

    try:
        vbox = request.app.state.vbox

        adapter = vbox.get_available_adapter(vm_uuid)

        logger.info(
            "Available adapter found: vm_uuid=%s, adapter=%s",
            vm_uuid,
            adapter
        )

        return {
            "adapter": adapter
        }

    except Exception:
        logger.exception(
            "Unable to find available adapter: vm_uuid=%s",
            vm_uuid
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to find available adapter"
        )


@app.post("/vms/{vm_uuid}/interfaces")
def attach_interface(
    vm_uuid: str,
    payload: AttachInterfaceRequest,
    request: Request
):

    logger.info(
        "Attaching network interface: vm_uuid=%s, physnet=%s, adapter=%s",
        vm_uuid,
        payload.physnet,
        payload.adapter
    )

    try:
        vbox = request.app.state.vbox

        mapping = vbox.get_physnet_mapping(
            payload.physnet
        )

        logger.info(
            "Physical network mapping resolved: physnet=%s",
            payload.physnet
        )

        result = vbox.attach_physnet(
            vm_uuid=vm_uuid,
            physnet=payload.physnet,
            adapter=payload.adapter,
            nic_type=payload.nic_type,
            mac_address=payload.mac_address
        )

        logger.info(
            "Network interface attached successfully: "
            "vm_uuid=%s, physnet=%s, adapter=%s",
            vm_uuid,
            payload.physnet,
            payload.adapter
        )

        return {
            "status": "ok",
            "vm_uuid": vm_uuid,
            "physnet": payload.physnet,
            "adapter": payload.adapter,
            "mac_address": payload.mac_address,
            "mapping": mapping,
            "result": result
        }

    except ValueError as exc:

        logger.warning(
            "Invalid interface attachment request: "
            "vm_uuid=%s, physnet=%s, error=%s",
            vm_uuid,
            payload.physnet,
            exc
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception:
        logger.exception(
            "Unable to attach network interface: vm_uuid=%s, adapter=%s",
            vm_uuid,
            payload.adapter
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to attach network interface"
        )


@app.delete("/vms/{vm_uuid}/interfaces/{adapter}")
def detach_interface(
    vm_uuid: str,
    adapter: int,
    request: Request
):

    logger.info(
        "Detaching network interface: vm_uuid=%s, adapter=%s",
        vm_uuid,
        adapter
    )

    try:
        vbox = request.app.state.vbox

        result = vbox.detach_physnet(
            vm_uuid=vm_uuid,
            adapter=adapter
        )

        logger.info(
            "Network interface detached successfully: "
            "vm_uuid=%s, adapter=%s",
            vm_uuid,
            adapter
        )

        return {
            "status": "ok",
            "vm_uuid": vm_uuid,
            "adapter": adapter,
            "result": result
        }

    except ValueError as exc:

        logger.warning(
            "Invalid interface detachment request: "
            "vm_uuid=%s, adapter=%s, error=%s",
            vm_uuid,
            adapter,
            exc
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception:
        logger.exception(
            "Unable to detach network interface: vm_uuid=%s, adapter=%s",
            vm_uuid,
            adapter
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to detach network interface"
        )
