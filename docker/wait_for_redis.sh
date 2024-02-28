#!/bin/bash

# Function to check Redis status
check_redis_status() {
  local ping_response=$(redis-cli -u $REDIS_URL ping)
  if [ "$ping_response" == "PONG" ]; then
    echo "Redis is ready!"
    return 0
  else
    echo "Redis is not ready yet. Retrying..."
    return 1
  fi
}


# Wait for Redis to be ready
while ! check_redis_status; do
  sleep 1
done

# Add additional logic here if needed
# For example, check if specific data is available in Redis before proceeding

echo "Redis is ready. Starting the dependent service..."
exec "$@"
