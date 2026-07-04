#!/usr/bin/env python3

from cli.commands import app 
from terminal.output import handle_ctrl_c


if __name__ == "__main__":
    handle_ctrl_c()
    app()
