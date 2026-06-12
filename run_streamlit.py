from __future__ import annotations

import ssl
import sys
from pathlib import Path


def _load_default_certs_without_windows_store(
    context: ssl.SSLContext,
    purpose: ssl.Purpose = ssl.Purpose.SERVER_AUTH,
) -> None:
    """
    Avoid a startup crash caused by malformed certificates in the Windows store.

    Some Windows/conda setups raise ``ssl.SSLError: [ASN1: NOT_ENOUGH_DATA]``
    while Tornado imports ``ssl.create_default_context``. Streamlit only needs
    to start a local server here, so using OpenSSL/certifi defaults is enough.
    """
    try:
        import certifi

        context.load_verify_locations(cafile=certifi.where())
    except Exception:
        pass

    context.set_default_verify_paths()


ssl.SSLContext.load_default_certs = _load_default_certs_without_windows_store

app_path = Path(__file__).resolve().parent / "src" / "app.py"
sys.argv = ["streamlit", "run", str(app_path), *sys.argv[1:]]

from streamlit.web.cli import main

raise SystemExit(main())
