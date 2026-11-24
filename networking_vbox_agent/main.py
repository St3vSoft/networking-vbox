import argparse
import uvicorn

import logging

from pathlib import Path

from .utils.config import read_config

from .api import app

def setup_logging(config):

    log_config = config["logging"]

    log_level = log_config.get("level", "INFO").upper()
    log_file = Path(log_config["file"])

    if log_file.suffix == "":
        log_file.mkdir(parents=True, exist_ok=True)
        log_file = log_file / "neutron-vbox-agent.log"
    else:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=(
            "%(asctime)s "
            "%(levelname)s "
            "%(name)s "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(
                log_file,
                encoding="utf-8"
            ),
            logging.StreamHandler()
        ],
        force=True
    )

def main():

    parser = argparse.ArgumentParser(
        description="Neutron Agent for VirtualBox Networking"
    )

    parser.add_argument(
        "--config-file",
        type=Path,
        required=True,
        help="Path of neutron-vbox-agent.conf"
    )

    args = parser.parse_args()

    config = read_config(args.config_file)

    app.state.config = config

    # Configurazione logging
    setup_logging(config)

    logger = logging.getLogger(__name__)

    server_host = config["server"]["host"]
    server_port = config["server"]["port"]
    server_workers = config["server"]["workers"]

    logger.info("Starting VirtualBox Neutron Agent")
    logger.info("Listening on %s:%s", server_host, server_port)

    try:
        uvicorn.run(
            app,
            host=server_host,
            port=server_port,
            workers=server_workers
        )

    except KeyboardInterrupt:
        logger.info("VirtualBox Neutron Agent terminated by the user")

    except Exception:
        logger.exception("VirtualBox Neutron Agent terminated with an exception")