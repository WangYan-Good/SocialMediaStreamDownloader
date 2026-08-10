"""Read-only query objects that serve the web UI.

Modules here own SELECT shapes that span more than one table.  They never write,
and they never import Flask, so they stay testable without a request context.
"""
