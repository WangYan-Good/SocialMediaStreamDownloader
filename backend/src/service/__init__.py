"""Application services that coordinate platform access for the web layer.

Modules here sit above the platform packages and below the HTTP routes.  They own
scheduling, batching and caching decisions; they do not build responses and never
import Flask.
"""
