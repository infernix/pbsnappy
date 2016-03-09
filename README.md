pbsnappy
===================
pbsnappy is a simple python script to automate the creation of snapshots for virtual servers in ProfitBricks Datacenters.

It is intended to run through cron anywhere, but most practically on the server that needs to be automatically snapshotted itself.

Configuration is straightforward and documented in config.py.example.

It is recommended to name your volumes in the PB interface with names related to the server, e.g. if the server is called 'mywebserver' the volumes should be called 'mywebserver OS', 'mywebserver DB' etc.
