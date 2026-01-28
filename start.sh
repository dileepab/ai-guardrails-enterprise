#!/bin/bash
set -e

echo "🚀 Starting App (Public: 8000, Internal: 8081)"

# Start Supervisor
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
