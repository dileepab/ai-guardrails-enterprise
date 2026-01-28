#!/bin/bash
set -e

# Default to 8000 if PORT is not set (local dev)
PORT="${PORT:-8000}"

echo "🚀 Starting App on PORT=$PORT"

# Replace the placeholder in supervisord.conf with the actual PORT
# We use a temp file to avoid issues with modifying the file in place if it's mounted (though here it's copied)
sed "s/REPLACE_WITH_PORT/$PORT/g" /etc/supervisor/conf.d/supervisord.template.conf > /etc/supervisor/conf.d/supervisord.conf

echo "✅ Configured supervisord.conf:"
cat /etc/supervisor/conf.d/supervisord.conf

# Start Supervisor
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
