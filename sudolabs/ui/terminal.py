"""Fixed bottom bar using ANSI scrolling regions.

Splits the terminal into a scrollable content area and a pinned bar:

    rows 1..scroll_end   : scrollable (Rich output, command results)
    scroll_end+1          : [cmd] Label   [cmd] Label
    scroll_end+2          : prompt_label >  (user types here)

Falls back to the standard draw_command_bar + Prompt.ask approach on
terminals that don't support ANSI escape sequences.
"""

import os
import sys
import shutil


class FixedBar:
    """Pinned bottom command bar using ANSI scrolling regions."""

    BAR_HEIGHT = 2  # commands + prompt

    def __init__(self, commands: list[tuple[str, str]], prompt_label: str = "sudolabs"):
        self.commands = commands
        self.prompt_label = prompt_label
        self.active = False
        self.supported = self._check_support()

    # ------------------------------------------------------------------
    # Support detection
    # ------------------------------------------------------------------

    @staticmethod
    def _check_support() -> bool:
        """Return True if the terminal supports ANSI scrolling regions."""
        if not sys.stdout.isatty():
            return False
        if os.name == "nt":
            # Enable VT100 processing on Windows Terminal / modern PowerShell
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
                mode = ctypes.c_ulong()
                kernel32.GetConsoleMode(handle, ctypes.byref(mode))
                # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
                return True
            except Exception:
                return False
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _dims(self) -> tuple[int, int, int]:
        """Return (cols, total_rows, scroll_end)."""
        cols, rows = shutil.get_terminal_size((80, 24))
        scroll_end = max(1, rows - self.BAR_HEIGHT)
        return cols, rows, scroll_end

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def activate(self):
        """Set up the ANSI scrolling region and draw the initial bar."""
        if not self.supported:
            return
        cols, _, scroll_end = self._dims()
        sys.stdout.write("\033[2J")                   # clear screen
        sys.stdout.write(f"\033[1;{scroll_end}r")     # set scroll region
        sys.stdout.write("\033[1;1H")                  # cursor to top-left
        sys.stdout.flush()
        self.active = True
        self._render()

    def deactivate(self):
        """Restore full-screen scrolling and clear."""
        if not self.active:
            return
        sys.stdout.write("\033[r")          # reset scroll region
        sys.stdout.write("\033[2J")         # clear screen
        sys.stdout.write("\033[1;1H")       # cursor to top-left
        sys.stdout.flush()
        self.active = False

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render(self):
        """Draw the two fixed rows below the scroll region."""
        cols, _, scroll_end = self._dims()

        sys.stdout.write("\033[s")      # save cursor position
        sys.stdout.write("\033[?7l")   # disable line wrap for bar

        # Row 1: command shortcuts — fit to terminal width
        r1 = scroll_end + 1
        sys.stdout.write(f"\033[{r1};1H\033[2K")

        parts_ansi: list[str] = []
        used = 2  # leading indent
        for i, (shortcut, label) in enumerate(self.commands):
            # visible width: "[shortcut] label" + separator
            vis_len = len(shortcut) + 2 + 1 + len(label)  # [x] label
            sep = 3 if i > 0 else 0  # "   " between items
            if used + sep + vis_len > cols - 1:
                break  # no room — stop adding commands
            parts_ansi.append(
                f"\033[1;91m[{shortcut}]\033[0m \033[2m{label}\033[0m"
            )
            used += sep + vis_len

        sys.stdout.write(f"  {'   '.join(parts_ansi)}")

        # Row 2: prompt prefix (input() fills the rest)
        r2 = scroll_end + 2
        sys.stdout.write(f"\033[{r2};1H\033[2K")
        sys.stdout.write(
            f"  \033[1;91m{self.prompt_label}\033[0m \033[91m>\033[0m "
        )

        sys.stdout.write("\033[?7h")   # re-enable line wrap
        sys.stdout.write("\033[u")     # restore cursor position
        sys.stdout.flush()

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def get_input(self) -> str:
        """Render the bar, read a line of input from the prompt row."""
        if not self.active or not self.supported:
            return self._fallback_input()

        cols, _, scroll_end = self._dims()

        # Ensure scroll region is locked before drawing
        sys.stdout.write(f"\033[1;{scroll_end}r")

        # Draw / refresh the bar
        self._render()

        # Position cursor on the prompt row, right after the prefix
        r2 = scroll_end + 2
        prefix_len = len(self.prompt_label) + 6  # "  label > "
        sys.stdout.write(f"\033[{r2};{prefix_len}H\033[K")

        # Temporarily reset scroll region so the terminal's line
        # editing (backspace, arrow keys) works on the prompt row.
        # Without this, backspace shows ^? instead of deleting.
        sys.stdout.write("\033[r")
        sys.stdout.write(f"\033[{r2};{prefix_len}H")
        sys.stdout.flush()

        try:
            user_input = input()
        except (EOFError, KeyboardInterrupt):
            user_input = ""

        # If the user pasted multi-line text, extra lines are sitting
        # in stdin waiting to be interpreted as commands.  Drain them
        # and append to the input so nothing is lost / misinterpreted.
        extra = self._drain_stdin()
        if extra:
            user_input = user_input + " " + " ".join(extra)

        # Restore scroll region immediately.
        # Enter may have scrolled the full screen (cursor was on the
        # last row with no scroll region), pushing old bar content
        # into row scroll_end.  Clean that row AND the bar rows.
        sys.stdout.write(f"\033[1;{scroll_end}r")

        for row in range(scroll_end, scroll_end + self.BAR_HEIGHT + 1):
            sys.stdout.write(f"\033[{row};1H\033[2K")

        self._render()
        sys.stdout.write(f"\033[{scroll_end};1H")
        sys.stdout.flush()

        return user_input

    @staticmethod
    def _drain_stdin() -> list[str]:
        """Drain any buffered lines from a multi-line paste.

        After input() reads one line, remaining pasted lines sit in
        stdin's buffer.  We grab them here so they don't get fed to the
        command loop as garbage.
        """
        lines: list[str] = []
        if os.name == "nt":
            try:
                import msvcrt
                # On Windows, drain character-by-character
                buf = ""
                while msvcrt.kbhit():
                    ch = msvcrt.getwch()
                    if ch in ("\r", "\n"):
                        if buf.strip():
                            lines.append(buf.strip())
                        buf = ""
                    else:
                        buf += ch
                if buf.strip():
                    lines.append(buf.strip())
            except Exception:
                pass
        else:
            try:
                import select as _sel
                while _sel.select([sys.stdin], [], [], 0.0)[0]:
                    line = sys.stdin.readline()
                    if not line:
                        break
                    stripped = line.strip()
                    if stripped:
                        lines.append(stripped)
            except Exception:
                pass
        return lines

    def _fallback_input(self) -> str:
        """Non-ANSI fallback using Rich panels."""
        from sudolabs.ui.panels import draw_command_bar
        from rich.prompt import Prompt
        from sudolabs.ui.theme import console

        console.print()
        draw_command_bar(self.commands)
        return Prompt.ask(
            f"  [bold bright_red]{self.prompt_label}[/bold bright_red]"
        )

    # ------------------------------------------------------------------
    # Scroll-area management
    # ------------------------------------------------------------------

    def clear_scroll_area(self):
        """Clear the scrollable content area without touching the bar."""
        if not self.active or not self.supported:
            os.system("cls" if os.name == "nt" else "clear")
            return

        _, _, scroll_end = self._dims()

        # Clear every line in the scroll region
        for row in range(1, scroll_end + 1):
            sys.stdout.write(f"\033[{row};1H\033[2K")

        sys.stdout.write("\033[1;1H")
        sys.stdout.flush()

        # Refresh the bar (clearing may push artifacts)
        self._render()

    def update_commands(self, commands: list[tuple[str, str]]):
        """Swap the displayed command list and redraw."""
        self.commands = commands
        if self.active:
            self._render()
