"""ARTIQ applet that plots the results of a single ndscan experiment.

Typically, applets aren't created manually, but used via ``ndscan.experiment`` (CCB).
"""

from artiq.applets.simple import SimpleApplet
import argparse
import logging
import pyqtgraph
from collections.abc import Iterable
from sipyco import common_args
from typing import Any

from .plots.container_widgets import RootWidget
from .plots.model import Context
from .plots.model.subscriber import SubscriberRoot

logger = logging.getLogger(__name__)


class _MainWidget(RootWidget):
    def __init__(self, args, ctl):
        self.args = args

        common_args.init_logger_from_args(args)

        # TODO: Consider exposing Context in Root.
        context = Context(ctl.set_dataset)
        super().__init__(SubscriberRoot(args.prefix, context), context)

        # Try ensuring a sensible window size on startup (i.e. large enough to show a
        # plot in.
        # FIXME: This doesn't seem to work when used with ARTIQ applet embedding. See if
        # call_later() works around that, or whether this needs to be fixed in ARTIQ.
        self.resize(600, 600)
        self.setWindowTitle("ndscan plot")

    def data_changed(self, values: dict[str, Any], metadata: dict[str, Any],
                     persist: dict[str, bool], mods: Iterable[dict[str, Any]]):
        self.root.data_changed(values, mods)


class NdscanApplet(SimpleApplet):
    def __init__(self):
        # Use a small update delay by default to avoid lagging out the UI by
        # continuous redraws for plots with a large number of points. (20 ms
        # is a pretty arbitrary choice for a latency not perceptible by the
        # user under typical circumstances; could be increased somewhat.)
        super().__init__(_MainWidget,
                         default_update_delay=20e-3,
                         cmd_description="Generic ARTIQ applet for ndscan experiments")

        # --prefix doesn't have a default value anymore and --rid doesn't exist; this
        # is just to be able to print an explicit backwards-incompatibility error.
        self.argparser.add_argument("--prefix",
                                    default=None,
                                    type=str,
                                    help="Root of the ndscan dataset tree")
        self.argparser.add_argument("--rid", default=None, help=argparse.SUPPRESS)

        common_args.verbosity_args(self.argparser)

    def args_init(self):
        super().args_init()
        if self.args.prefix is None:
            raise ValueError(
                "ndscan 0.3+ does not use dataset rid namespaces and requires an " +
                "explicit --prefix to be specified (applet generated by old ndscan " +
                "on master?)")
        if self.args.rid is not None:
            raise ValueError(
                "ndscan 0.3+ does not use dataset rid namespaces and requires an " +
                "explicit --prefix instead of --rid (applet generated by old ndscan " +
                "on master?)")
        # Subscribe to just our sub-tree of interest.
        if not hasattr(self, "dataset_prefixes"):
            raise RuntimeError("Client-side ARTIQ version out of date; update " +
                               "dashboard to m-labs/artiq@e1f9feae8 or newer.")
        self.dataset_prefixes.append(self.args.prefix)


def main():
    pyqtgraph.setConfigOptions(antialias=True)
    NdscanApplet().run()


if __name__ == "__main__":
    main()
