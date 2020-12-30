import argparse
import logging
import sys

from twisted.internet import reactor

from fake_switches import switch_factory
from fake_switches.transports.ssh_service import SwitchSshService


logging.basicConfig(level="DEBUG")
logger = logging.getLogger()

# NOTE(mmitchell): This is necessary because some imports will initialize the root logger.
logger.setLevel("DEBUG")


def main():
    parser = argparse.ArgumentParser(
        description="Fake-switch simulator launcher",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="cisco_generic",
        help=(
            "Switch model, allowed values are "
            + ", ".join(switch_factory.DEFAULT_MAPPING.keys())
        ),
    )
    parser.add_argument(
        "--hostname", type=str, default="switch", help="Switch hostname"
    )
    parser.add_argument("--username", type=str, default="root", help="Switch username")
    parser.add_argument("--password", type=str, default="root", help="Switch password")
    parser.add_argument(
        "--listen-host", type=str, default="0.0.0.0", help="Listen host"
    )
    parser.add_argument("--listen-port", type=int, default=2222, help="Listen port")
    parser.add_argument("-c", "--config-file", type=str, help="JSON config to load")
    parser.add_argument(
        "-v",
        "--shell-variant",
        type=str,
        default="cli",
        help="tl1, cli: depends on vendor",
    )

    args = parser.parse_args()
    args.password = args.password.encode()

    try:
        factory = switch_factory.SwitchFactory()
        switch_core = factory.get(
            args.model, args.hostname, args.password, config_file=args.config_file
        )

        ssh_service = SwitchSshService(
            ip=args.listen_host,
            port=args.listen_port,
            switch_core=switch_core,
            users={args.username: args.password} if args.username != "None" else {},
            variant=args.shell_variant,
        )
        ssh_service.hook_to_reactor(reactor)

        logger.info("Starting reactor")
        reactor.run()
    except:
        logging.exception("Failed to start switch")
        return -1


if __name__ == "__main__":
    sys.exit(main())
