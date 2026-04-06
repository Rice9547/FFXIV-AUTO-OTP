import os
import sys

# Fix tcl/tk path when running in a venv
if sys.exec_prefix != sys.base_exec_prefix:
    tcl_dir = os.path.join(sys.base_exec_prefix, "tcl")
    if os.path.isdir(tcl_dir):
        os.environ.setdefault("TCL_LIBRARY", os.path.join(tcl_dir, "tcl8.6"))
        os.environ.setdefault("TK_LIBRARY", os.path.join(tcl_dir, "tk8.6"))

import gui


def main():
    gui.run()


if __name__ == "__main__":
    main()
