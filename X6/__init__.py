from __future__ import absolute_import, print_function, unicode_literals

from .X6 import X6
from _Framework.Capabilities import (
    CONTROLLER_ID_KEY,
    PORTS_KEY,
    NOTES_CC,
    REMOTE,
    SCRIPT,
    controller_id,
    inport,
    outport,
)


def create_instance(c_instance):
    return X6(c_instance)


def get_capabilities():
    # Optional: enables USB auto-detection so Live can suggest the X6. The
    # script also works when selected manually as a Control Surface, in which
    # case these capabilities are ignored.
    return {
        CONTROLLER_ID_KEY: controller_id(
            vendor_id=6860, product_ids=[6709], model_name='X6'
        ),
        PORTS_KEY: [
            inport(props=[NOTES_CC, REMOTE, SCRIPT]),
            inport(props=[NOTES_CC, REMOTE]),
            outport(props=[NOTES_CC, REMOTE, SCRIPT]),
        ],
    }
