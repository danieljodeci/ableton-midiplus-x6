from __future__ import absolute_import, print_function, unicode_literals

import Live
from _Framework.ControlSurface import ControlSurface

# -- Device SysEx signature -------------------------------------------------
# The MIDIPlus X6 transport buttons, when set to MMC ("red" backlight) mode,
# emit Standard MIDI MMC messages of the form:
#
#     F0 7F 74 06 <command> F7
#     (240 127 116 6 <command> 247)
#
# i.e. the leading bytes below, followed by a single command byte, followed by
# the SysEx End byte (247). We match on the leading bytes and read the command
# as the second-to-last byte of the message.
#
# NOTE: the third byte is 0x74 (116 decimal), confirmed by capturing live SysEx
# from an X6 mini. The original Live 10 script used 74 *decimal* (0x4A) here,
# which is why it never matched this unit -- watch the hex-vs-decimal trap.
X6_SIG = (240, 127, 116, 6)

# -- Command byte table -----------------------------------------------------
# All six command bytes CONFIRMED by capturing live SysEx from an X6 mini.
CMD_STOP = 1            # CONFIRMED on device (0x01)
CMD_PLAY = 2            # CONFIRMED on device (0x02)
CMD_RECORD = 6          # CONFIRMED on device (0x06)
CMD_REWIND = 5          # CONFIRMED on device (0x05)
CMD_FAST_FORWARD = 4    # CONFIRMED on device (0x04)
CMD_RETURN_TO_ZERO = 55  # CONFIRMED on device (0x37)

# How far rewind / fast-forward jump per button press, in beats.
JUMP_BEATS = 4.0

# Set True to log every incoming SysEx message (raw bytes) to Log.txt. Use this
# to discover what the device actually sends, then set back to False.
DEBUG = False


class X6(ControlSurface):
    """
    MIDIPlus X6 transport support for Ableton Live 12 (Python 3).

    Listens for the X6's MMC SysEx transport messages and drives Live's
    transport directly through the Song API, sidestepping the MIDI-map UI
    (the X6 transport buttons cannot send note messages, so they cannot be
    natively mapped to Live's transport bar).
    """

    def __init__(self, c_instance):
        self._c_instance = c_instance
        ControlSurface.__init__(self, c_instance)
        with self.component_guard():
            self._suggested_input_port = 'X6'
            self._suggested_output_port = 'X6'
            # command byte -> handler
            self._commands = {
                CMD_STOP: self.stop,
                CMD_PLAY: self.play,
                CMD_RECORD: self.record,
                CMD_REWIND: self.rewind,
                CMD_FAST_FORWARD: self.fast_forward,
                CMD_RETURN_TO_ZERO: self.return_to_zero,
            }
        self.log_message("X6 control surface loaded (Live 12 / Py3).")

    def handle_sysex(self, midi_bytes):
        # Live hands us a tuple of ints; normalise to a list so behaviour is
        # predictable regardless of the incoming sequence type.
        data = list(midi_bytes)
        if DEBUG:
            self.log_message(
                "SysEx IN ({n} bytes): {raw}".format(
                    n=len(data),
                    raw=" ".join("{0:02X}".format(b) for b in data),
                )
            )
        if tuple(data[0:-2]) == X6_SIG:
            command = data[-2]
            handler = self._commands.get(command)
            if handler is not None:
                handler()
            else:
                self.log_message(
                    "Unrecognized X6 command byte: {dec} (0x{hex:02X}). "
                    "Full SysEx: {raw}. If you pressed Rewind / Fast-Forward / "
                    "Return-to-Zero, copy this byte into the matching "
                    "CMD_* constant in X6.py.".format(
                        dec=command,
                        hex=command,
                        raw=" ".join("{0:02X}".format(b) for b in data),
                    )
                )

    def song(self):
        """Reference to the Live Song instance we control."""
        return self._c_instance.song()

    # -- transport handlers --------------------------------------------------
    def play(self):
        # continue_playing() resumes from the current position. To make Play
        # always jump to the arrangement start instead, switch the line below
        # to: self.song().start_playing()
        self.song().continue_playing()

    def stop(self):
        self.song().stop_playing()

    def record(self):
        self.song().record_mode = not self.song().record_mode

    def rewind(self):
        # Alternative: self.song().jump_to_prev_cue() to jump between locators.
        self.song().jump_by(-JUMP_BEATS)

    def fast_forward(self):
        # Alternative: self.song().jump_to_next_cue() to jump between locators.
        self.song().jump_by(JUMP_BEATS)

    def return_to_zero(self):
        self.song().current_song_time = 0.0
