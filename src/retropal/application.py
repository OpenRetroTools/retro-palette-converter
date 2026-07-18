"""Application entry points shared by desktop packaging targets."""


def run_gui() -> int:
    """Start the graphical application.

    The GUI is intentionally deferred until milestone M2.
    """
    raise NotImplementedError("The graphical application will be implemented in M2.")
