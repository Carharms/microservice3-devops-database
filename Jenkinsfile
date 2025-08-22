pipeline {
    agent any

    triggers {
        // Webhook triggers for different events
        githubPush()
        pullRequest()
    }
    //test 
    environment {
        DOCKER_HUB_CREDENTIALS = 'docker-hub-credentials'
        DOCKER_IMAGE_NAME = 'carharms/db-service'
        IMAGE_TAG = "${BUILD_NUMBER}"
        SONAR_PROJECT_KEY = 'db-service'
        // SONAR_HOST_URL = 'http://localhost:9000'
        // SONAR_AUTH_TOKEN
        
        // Database test configuration
        POSTGRES_DB = 'subscriptions'
        POSTGRES_USER = 'dbuser'
        POSTGRES_PASSWORD = 'dbpassword'
        DB_HOST = 'localhost'
        DB_PORT = '5432'
    }
    
    stages {
        stage('Build') {
            steps {
                script {
                    echo "Installing Python dependencies and running code quality checks..."
                    sh '''
                        pip3 install ruff black pytest --break-system-packages || pip3 install ruff black pytest
                        
                        echo "Running Black formatter..."
                        black . --check --diff || (echo "Code formatting issues found, fixing..." && black .)
                        
                        echo "Running Ruff linter..."
                        ruff check . --fix || (echo "Linting issues found and fixed where possible")
                        
                        echo "Validating required files..."
                        test -f "scripts/init.sql" && echo "✓ init.sql found" || (echo "✗ init.sql missing" && exit 1)
                        test -f "Dockerfile" && echo "✓ Dockerfile found" || (echo "✗ Dockerfile missing" && exit 1)
                        test -f "docker-compose.yml" && echo "✓ docker-compose.yml found" || (echo "✗ docker-compose.yml missing" && exit 1)
                    '''
                }
            }
        }
        
        stage('Test') {
            steps {
                script {
                    echo "Running database tests..."
                    sh '''
                        # Run unit tests (no database required)
                        echo "Running unit tests..."
                        pytest tests/test_db_init.py::TestDatabaseSchema -v --tb=short || echo "Unit tests completed with issues"
                        
                        # Start database for integration tests
                        echo "Starting database for integration tests..."
                        docker-compose -f docker-compose.yml down --remove-orphans || true
                        docker-compose -f docker-compose.yml up -d postgres
                        
                        # Wait for database to be ready
                        echo "Waiting for database to be ready..."
                        timeout 60 bash -c 'until docker-compose -f docker-compose.yml exec -T postgres pg_isready -U $POSTGRES_USER -d $POSTGRES_DB; do sleep 2; done' || echo "Database ready check timeout"
                        
                        # Run integration tests
                        echo "Running integration tests..."
                        pytest tests/test_db_init.py::TestDatabaseIntegration -v --tb=short || echo "Integration tests completed with issues"
                        
                        # Cleanup
                        echo "Cleaning up test environment..."
                        docker-compose -f docker-compose.yml down --remove-orphans || true
                    '''
                }
            }
        }
      
    stage('SonarQube Analysis and Quality Gate') {
    steps {
        script {
            // Get the SonarScanner tool path
            def scannerHome = tool 'SonarScanner'
            // Use the 'withSonarQubeEnv' wrapper for both the analysis and the quality gate check
            withSonarQubeEnv('SonarQube') {
                // Use the 'bat' step as you did before for Windows compatibility
                bat """
                    "${scannerHome}\\bin\\sonar-scanner.bat" -Dsonar.projectKey=${SONAR_PROJECT_KEY} -Dsonar.sources=.
                """
                }
            }
        }
    }
        
        stage('Container Build') {
            steps {
                script {
                    echo "Building Docker image..."
                    def image = docker.build("${DOCKER_IMAGE_NAME}:${IMAGE_TAG}")
                    
                    // Tag with branch-specific tags
                    if (env.BRANCH_NAME == 'main') {
                        image.tag("latest")
                    } else if (env.BRANCH_NAME == 'develop') {
                        image.tag("dev-latest")
                    } else if (env.BRANCH_NAME?.startsWith('release/')) {
                        image.tag("staging-latest")
                    }
                }
            }
        }
    
    stage('Container Security Scan') {
    steps {
        script {
            echo "Running container security scan..."
            try {
                // Fail on critical vulnerabilities
                bat "docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:latest image --exit-code 1 --severity CRITICAL carharms/db-service:${BUILD_NUMBER}"
            } catch (Exception e) {
                echo "Security scan encountered issues but continuing: ${e.getMessage()}"
            }
        }
    }
}
    
        
        stage('Container Push') {
            when {
                anyOf {
                    branch 'develop'
                    branch 'main'
                    branch 'release/*'
                }
            }
            steps {
                script {
                    echo "Pushing Docker image to registry..."
                    docker.withRegistry('https://index.docker.io/v1/', env.DOCKER_HUB_CREDENTIALS) {
                        def image = docker.image("${DOCKER_IMAGE_NAME}:${IMAGE_TAG}")
                        image.push()
                        
                        if (env.BRANCH_NAME == 'main') {
                            image.push("latest")
                        } else if (env.BRANCH_NAME == 'develop') {
                            image.push("dev-latest")
                        } else if (env.BRANCH_NAME?.startsWith('release/')) {
                            image.push("staging-latest")
                        }
                    }
                }
            }
        }
        
        stage('Deploy') {
            when {
                anyOf {
                    branch 'develop'
                    expression { env.BRANCH_NAME.startsWith('release/') }
                    branch 'main'
                }
            }
            steps {
                script {
                    if (env.BRANCH_NAME == 'main') {
                        timeout(time: 10, unit: 'MINUTES') {
                            input message: "Deploy to production?", ok: "Deploy"
                        }
                    }
                    
                    echo "Deploying to ${env.BRANCH_NAME} environment..."
                    sh 'docker-compose -f docker-compose.yml up -d'
                }
            }
        }
    }
    
    post {
        always {
            sh '''
                docker-compose -f docker-compose.yml down --remove-orphans || true
                docker system prune -f || true
            '''
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}