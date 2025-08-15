# PostgreSQL image
FROM postgres:15-alpine

# Environment variables (these can be overridden at runtime)
ENV POSTGRES_DB=subscriptions
ENV POSTGRES_USER=dbuser  
ENV POSTGRES_PASSWORD=dbpassword

# Copy initialization script
COPY scripts/init.sql /docker-entrypoint-initdb.d/

# Copy and setup healthcheck script
COPY scripts/healthcheck.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/healthcheck.sh

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# Expose PostgreSQL port
EXPOSE 5432

# Use default PostgreSQL entrypoint and command
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["postgres"]