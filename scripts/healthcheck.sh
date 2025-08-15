#!/bin/bash
# PostgreSQL health check script

set -e

# Check if PostgreSQL is accepting connections
pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" -h localhost -p 5432

# If pg_isready succeeds, try a simple query to ensure database is fully initialized
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" > /dev/null 2>&1

echo "PostgreSQL is healthy"