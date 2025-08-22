## Database Service Overview ##
Rrepository for the REST API that handles all order management for our e-commerce platform.

## Setup ##
Install Docker and Docker Compose on your local system.

The database is designed to be provisioned as a container. For local development, you can use the provided docker-compose.yml file.

1. Clone this repository:
git clone <your-repo-url>

2. Navigate to the project directory:
cd database

3. Start the PostgreSQL container in detached mode:
docker-compose up -d

This will create a running PostgreSQL instance that your microservices can connect to.

## Project Architecture ##

Technology Stack: We use PostgreSQL, a robust and reliable open-source relational database.

Database Schemas: This repository holds the SQL scripts for creating and managing the database schemas for both the Product and Order services. This ensures that the database structure is version-controlled and can be easily replicated across environments.

Data Persistence: In a production environment, the database data is stored on a persistent volume to ensure that data is not lost when the container restarts or is moved. For local development, data is stored in a Docker volume.

## CI/CD Pipeline ##
IaC with Terraform: Instead of being managed by a traditional CI/CD pipeline, the database infrastructure is provisioned and managed using Terraform. This allows us to define our infrastructure in code, ensuring consistency across dev, staging, and prod environments.

State Management: Terraform uses local state management to track the provisioned infrastructure, preventing environment conflicts and providing a reliable way to manage database configurations.

Configuration: All database credentials and sensitive information are handled as Kubernetes Secrets in production and through environment variables in local development, ensuring they are not hardcoded.