"""One background-task model for every asynchronous action the server runs.

Recording a live room, downloading one post, walking an owner's whole feed and
probing live status are all the same shape to a user: something was submitted,
it is queued, it runs, it reports progress, it ends.  Each of those grew its own
progress structure, so the frontend had to learn four of them.  This package
holds the single lifecycle they will all report against.

The store is process-local and in-memory by design at this stage; nothing here
touches the database or the ORM.
"""
