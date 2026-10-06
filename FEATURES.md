
[0.0.2] initial python-backend
- create FastAPI Python
- sqlalchemy with migrations to sqlite database
- create environment configurations for backend
- create environment configurations for engine
- add address zones
- add address type
- add ping interval
- add go backend client
- decode ping destinations
- add support for enabled ping destination
- support for host resolution for IPV4 addresses
- support for IPV4 dotted decimal addresses
- added initial support for a frontend
- add support for ping destination setup
- add initial GUI implementation (Codex)
- added support for TradingView
- fix trading view 1h look back
- added support for resume button
    - when scrolled the system will disable updates
- added update time 1s, etc.
- fixed timeout ui, now provides blank space

[0.0.1] initial testing of ping-engine in golang
- ping-engine in go
- worker manager for pinger
    - worker stop
    - worker status
- send_ping function
- receive function
    - ping stats
- log function
- http controller
    - workers
    - global ping stats
    - whole engine shutdown
