# Abaqus AI — Community (local test build 1.0)
Mohamed Amr Software | Commercial support: hiioooom881@gmail.com | +968 99726465

Based on [Abaqus-Control-MCP](https://github.com/Whfkl/Abaqus-Control-MCP), supplied source 2.0.0, MIT. Original copyright and license remain in `payload/app/LICENSE`. This is not an official Dassault Systèmes or Anthropic product. No Abaqus or Claude license is included.

Only ping is exposed; it returns session metadata including model and viewport names. No arbitrary Python or solver tools.

## Install on Windows
1. Extract the entire ZIP. Close Claude and Abaqus. Use your normal account.
2. Ensure licensed Abaqus 2024 and `uv` are installed. Run VERIFY_PACKAGE.bat, then INSTALL.bat (or INSTALL_CLAUDE_CODE.bat for an existing abaqus-ai project).
3. Start Abaqus/CAE, then Plug-ins > Abaqus-Control-MCP > Start MCP Bridge. Run CHECK_CONNECTION.bat. Restart Claude and use ping.
4. Stop the bridge after use. UNDO_LAST_INSTALL.bat restores the previous configuration if it has not been changed.

## Security and limits
Loopback only (127.0.0.1). A random 256-bit token is generated on each install, stored in the installed plugin and Claude config. Do not share those files, receipts, or backups. Other processes with access to the same user files may obtain the token. No TLS, remote access, or security certification. Do not run both editions simultaneously: they share plugin, server name and port; use undo/reinstall when switching. Reinstall/restart all clients after token rotation. The public build must be tested in an actual licensed Abaqus session before a production release. No paid services used to build this kit; existing Abaqus/Claude usage is subject to their own terms.

## Licensing
Upstream MIT rights are unchanged, including redistribution rights. Commercial services and separately owned original additions may be sold under separate agreements. Do not claim exclusive rights over upstream code. Contact the email above for installation, customization and support.
