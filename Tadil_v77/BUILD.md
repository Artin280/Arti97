# Build version 77

Use a Windows 64-bit Python 3.13.9 virtual environment. Install build-requirements.txt, then run:

    python build_windows.py app
    python build_windows.py installer

Outputs: dist/Tadil_v77/ and dist/Setup_Tadil_v77.exe. PyInstaller embeds Python, Tk/Tcl, SQLite and Pillow. The application ZIP and its file-level SHA-256 manifest are generated between the builds. No customer data is included.

This build was produced using Windows Python and Windows PyInstaller under Wine 10.0 on Linux, with signed Debian package metadata and verified HTTPS downloads. Windows third-party packages were installed from downloaded wheels without network use inside Wine. Wine is a compatibility test environment, not a native Windows machine.

Test reports describe what was actually run. The data-dependent regression tests require the separately supplied version 76 databases and source; private database fixtures are intentionally omitted from the source archive. The application's --smoke-test <isolated-directory> and --verify-saved-smoke <same-directory> modes use synthetic data and support testing the frozen executable in two separate processes. Never pass the user's real data directory to a smoke test.

For future releases, increase the version above 77 in the application, launcher, installer, version resource and output filenames. Do not replace customer data or alter formulas or index values without the user's approval and supporting documents.
