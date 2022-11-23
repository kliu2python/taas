import argparse

from taascli.conf import init_config
from taascli.upgrade.func import cancel_update
from taascli.upgrade.func import clear_history
from taascli.upgrade.func import generate_config
from taascli.upgrade.func import update_sys
from taascli.upgrade.func import show_update

parser = argparse.ArgumentParser(prog="taas")
sub_parsers = parser.add_subparsers(help="TaaS Functions to use", required=True)

# ### config init subparsers###
init_parser = sub_parsers.add_parser("init",
                                     help="Init TaaS cli, this is one time "
                                          "setup, by default TaaS is using IP: "
                                          "10.160.83.213, if you want user "
                                          "different TaaS backend, use: -ip")
init_parser.set_defaults(func=init_config)
init_parser.add_argument(
    "-ip", help="IP of TaaS backend", default="10.160.83.213"
)

# ### Upgrade subparsers ###
# Upgrade - top sub parser
upgrade_parser = sub_parsers.add_parser(
    "upgrade", help="upgrade Fortiproduct system this can upgrade upgrade image"
                    ", av , ips. supported platform: fgt,fac(later),fmg(later),"
                    "faz(later). execute taas upgrade -h for details"
)
upgrade_sub_parsers = upgrade_parser.add_subparsers()

# upgrade sys - sub parser
upgrade_update_parser = upgrade_sub_parsers.add_parser(
    "update", help="Perform Upgrade"
)

upgrade_update_parser.set_defaults(func=update_sys)
# upgrade sys -- parameters
upgrade_update_parser.add_argument(
    "-m", default="fos", dest="platform", type=str, help="platform to upgrade, "
                                                         "for now only fos "
                                                         "supported, "
                                                         "fos is default"
)
upgrade_update_parser.add_argument(
    "-d", "--product", type=str, default="fgt", help="Product to upgrade, "
                                                     "by default this is fgt"
)
upgrade_update_parser.add_argument(
    "-r", "--repo", type=str, default=None, help="Code Repo to use, like "
                                                 "FortiOS, FortiOS-6K7K"
)
upgrade_update_parser.add_argument(
    "-c", "--branch", type=str, default="", help="Special branch to use, "
                                                 "by default it is '', means "
                                                 "trunk not special branch"
)
upgrade_update_parser.add_argument(
    "-e", "--release", type=str, help="Release, 7.2.1 means 7.2.1 latst "
                                      "build if build = 0, 7.2.1ga means "
                                      "7.2.1 ga build, if just want to upgrade "
                                      "to latest build no matter release, "
                                      "use single digits 7")
upgrade_update_parser.add_argument(
    "-b", "--build", type=int, default=0, help="Build number,build = 0 means"
                                               " latest build fpr release "
                                               "on trunk or special branch,"
                                               "default it is 0(latest build)"
)
upgrade_update_parser.add_argument(
    "-t", "--type", type=str, default="image", help="Upgrade type, supported:"
                                                    " image, av, ips, "
                                                    "default is image"
)
upgrade_update_parser.add_argument(
    "-i", "--ip", type=str, help="Target Device IP to upgrade"
)
upgrade_update_parser.add_argument(
    "-u", "--username", type=str, help="Target device username"
)
upgrade_update_parser.add_argument(
    "-p", "--password", type=str, default="", help="Target device password, "
                                                   "default is empty"
)
upgrade_update_parser.add_argument(
    "-f", "--file", type=str, dest="file", default=None, help="config file "
                                                              "to use"
)
upgrade_update_parser.add_argument(
    "-n", "--file-pattern", type=str, default=None, help="File name pattern if "
                                                         "use type rather "
                                                         "than image"
)
upgrade_update_parser.add_argument(
    "-w", "--wait", action="store_true",
    help="hold command until upgrade complete command"
)

# upgrade cancel - sub parser
upgrade_cancel_parser = upgrade_sub_parsers.add_parser(
    "cancel", help="Cancel upgrade, Note: upgrade cancel is not grantee"
)
upgrade_cancel_parser.set_defaults(func=cancel_update)
upgrade_cancel_parser.add_argument(
    "--id", required=True, help="upgrade id to cancel"
)

# upgrade show - sub parser
upgrade_show_parser = upgrade_sub_parsers.add_parser(
    "show", help="show upgrade status"
)
upgrade_show_parser.set_defaults(func=show_update)
upgrade_show_parser.add_argument(
    "-w", "--wait", action="store_true", help="wait for upgrade complete"
)
upgrade_show_parser.add_argument(
    "--id", default=None, help="upgrade id to show"
)

# upgrade show clear - sub parser
upgrade_show_sub_parsers = upgrade_show_parser.add_subparsers()
upgrade_show_clear_parser = upgrade_show_sub_parsers.add_parser(
    "clear", help="clear upgrade history"
)
upgrade_show_clear_parser.set_defaults(func=clear_history)

# upgrade generate - sub parser
upgrade_generate_parser = upgrade_sub_parsers.add_parser(
    "generate", help="generate sample config file, it support multiple device "
                     "upgrade at same time"
)
upgrade_generate_parser.set_defaults(func=generate_config)
upgrade_generate_parser.add_argument(
    "-o", "--out", required=True, help="output file location and name"
)
