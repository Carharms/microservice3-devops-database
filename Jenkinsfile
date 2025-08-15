pipeline {
    agent any
    
    environment {
        // Docker Hub credentials (configure in Jenkins)
        DOCKER_HUB_CREDENTIALS = credentials('docker-hub-credentials')
        DOCKER_HUB_REPO = 'carharms/subscription-db'
        IMAGE_TAG = "${BUILD_NUMBER}"
        SONAR_TOKEN = credentials('sonar-token')
        
        // Environment-specific variables
        DB_NAME = 'subscriptions'
        DB_USER = 'dbuser'
        DB_PASSWORD = credentials('db-password')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build Stage') {
            steps {
                script {
                    echo "=== BUILD STAGE ==="
                    echo "Branch: ${env.BRANCH_NAME}"
                    
                    // Validate SQL syntax
                    sh '''
                        echo "Validating SQL syntax..."
                        # Basic SQL syntax validation
                        if [ -f "scripts/init.sql" ]; then
                            echo "✓ init.sql exists"
                            # Check for basic SQL syntax issues
                            grep -i "CREATE TABLE" scripts/init.sql && echo "✓ CREATE TABLE statements found"
                            grep -i "INSERT INTO" scripts/init.sql && echo "✓ INSERT statements found"
                        else
                            echo "✗ init.sql not found"
                            exit 1
                        fi
                    '''
                    
                    // Validate Dockerfile
                    sh '''
                        echo "Validating Dockerfile..."
                        if [ -f "Dockerfile" ]; then
                            echo "✓ Dockerfile exists"
                            docker --version
                        else
                            echo "✗ Dockerfile not found"
                            exit 1
                        fi
                    '''
                }
            }
        }
        
        stage('Test Stage') {
            steps {
                script {
                    echo "=== TEST STAGE ==="
                    
                    // Start test database
                    sh '''
                        echo "Starting test database..."
                        docker-compose -f docker-compose.yml down --remove-orphans || true
                        docker-compose -f docker-compose.yml up -d postgres
                        
                        echo "Waiting for database to be ready..."
                        timeout 60 bash -c 'until docker-compose exec -T postgres pg_isready -U dbuser -d subscriptions; do sleep 2; done'
                    '''
                    
                    // Run unit tests
                    sh '''
                        echo "Installing test dependencies..."
                        pip3 install psycopg2-binary pytest
                        
                        echo "Running unit tests..."
                        export DB_HOST=localhost
                        export DB_PORT=5432
                        export POSTGRES_DB=subscriptions
                        export POSTGRES_USER=dbuser
                        export POSTGRES_PASSWORD=dbpassword
                        
                        python3 -m pytest tests/test_db_init.py -v --tb=short
                    '''
                }
            }
            post {
                always {
                    sh 'docker-compose -f docker-compose.yml down --remove-orphans || true'
                }
            }
        }
        
        stage('Security Scan') {
            when {
                anyOf {
                    branch 'develop'
                    branch 'main'
                    changeRequest target: 'develop'
                    changeRequest target: 'main'
                }
            }
            steps {
                script {
                    echo "=== SECURITY SCAN STAGE ==="
                    
                    // SonarQube analysis
                    withSonarQubeEnv('SonarQube') {
                        sh '''
                            sonar-scanner \
                                -Dsonar.projectKey=subscription-db-service \
                                -Dsonar.projectName="Subscription DB Service" \
                                -Dsonar.sources=scripts/ \
                                -Dsonar.tests=tests/ \
                                -Dsonar.language=sql \
                                -Dsonar.sourceEncoding=UTF-8
                        '''
                    }
                    
                    // Wait for SonarQube quality gate
                    timeout(time: 10, unit: 'MINUTES') {
                        def qg = waitForQualityGate()
                        if (qg.status != 'OK') {
                            error "Pipeline aborted due to quality gate failure: ${qg.status}"
                        }
                    }
                }
            }
        }
        
        stage('Container Build') {
            when {
                anyOf {
                    branch 'develop'
                    branch 'release/*'
                    branch 'main'
                }
            }
            steps {
                script {
                    echo "=== CONTAINER BUILD STAGE ==="
                    
                    // Build Docker image
                    def image = docker.build("${DOCKER_HUB_REPO}:${IMAGE_TAG}")
                    
                    // Tag with latest for main branch
                    if (env.BRANCH_NAME == 'main') {
                        image.tag("latest")
                    }
                    
                    // Tag with environment-specific tags
                    if (env.BRANCH_NAME == 'develop') {
                        image.tag("dev-latest")
                    } else if (env.BRANCH_NAME.startsWith('release/')) {
                        def releaseVersion = env.BRANCH_NAME.replaceAll('release/', '')
                        image.tag("${releaseVersion}")
                        image.tag("staging-latest")
                    }
                    
                    // Container security scanning with Trivy
                    sh '''
                        echo "Running container security scan..."
                        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                            -v $HOME/Library/Caches:/root/.cache/ \
                            aquasec/trivy:latest image --exit-code 0 --severity HIGH,CRITICAL \
                            --format table ${DOCKER_HUB_REPO}:${IMAGE_TAG}
                    '''
                }
            }
        }
        
        stage('Container Push') {
            when {
                anyOf {
                    branch 'develop'
                    branch 'release/*'
                    branch 'main'
                }
            }
            steps {
                script {
                    echo "=== CONTAINER PUSH STAGE ==="
                    
                    docker.withRegistry('https://index.docker.io/v1/', 'docker-hub-credentials') {
                        def image = docker.image("${DOCKER_HUB_REPO}:${IMAGE_TAG}")
                        image.push()
                        image.push("${env.BRANCH_NAME}-${BUILD_NUMBER}")
                        
                        if (env.BRANCH_NAME == 'main') {
                            image.push("latest")
                        } else if (env.BRANCH_NAME == 'develop') {
                            image.push("dev-latest")
                        } else if (env.BRANCH_NAME.startsWith('release/')) {
                            def releaseVersion = env.BRANCH_NAME.replaceAll('release/', '')
                            image.push("${releaseVersion}")
                            image.push("staging-latest")
                        }
                    }
                }
            }
        }
        
        stage('Deploy to Dev') {
            when {
                branch 'develop'
            }
            steps {
                script {
                    echo "=== DEPLOY TO DEV ==="
                    
                    sh '''
                        echo "Deploying to dev environment..."
                        # Replace with your actual dev deployment commands
                        # Example: kubectl set image deployment/subscription-db subscription-db=${DOCKER_HUB_REPO}:dev-latest
                        
                        echo "Deployment to dev completed with image: ${DOCKER_HUB_REPO}:dev-latest"
                    '''
                }
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'release/*'
            }
            steps {
                script {
                    echo "=== DEPLOY TO STAGING ==="
                    
                    sh '''
                        echo "Deploying to staging environment..."
                        # Replace with your actual staging deployment commands
                        
                        echo "Deployment to staging completed with image: ${DOCKER_HUB_REPO}:staging-latest"
                    '''
                }
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "=== DEPLOY TO PRODUCTION ==="
                    
                    // Manual approval for production deployment
                    timeout(time: 10, unit: 'MINUTES') {
                        input message: 'Deploy to Production?', 
                              ok: 'Deploy',
                              parameters: [
                                  choice(name: 'DEPLOY_CONFIRMATION', 
                                         choices: ['Deploy', 'Abort'], 
                                         description: 'Confirm production deployment')
                              ]
                    }
                    
                    sh '''
                        echo "Deploying to production environment..."
                        # Replace with your actual production deployment commands
                        
                        echo "Deployment to production completed with image: ${DOCKER_HUB_REPO}:latest"
                    '''
                }
            }
        }
    }
    
    post {
        always {
            // Cleanup
            sh '''
                docker-compose -f docker-compose.yml down --remove-orphans || true
                docker system prune -f || true
            '''
            
            // Archive test results if they exist
            archiveArtifacts artifacts: '**/*.log', allowEmptyArchive: true
        }
        
        success {
            echo 'Pipeline completed successfully!'
            
            // Send notification for main branch deployments
            script {
                if (env.BRANCH_NAME == 'main') {
                    // Add your notification logic here (Slack, email, etc.)
                    echo "Production deployment successful for build ${BUILD_NUMBER}"
                }
            }
        }
        
        failure {
            echo 'Pipeline failed!'
            
            // Send failure notification
            script {
                // Add your failure notification logic here
                echo "Pipeline failed for branch ${env.BRANCH_NAME}, build ${BUILD_NUMBER}"
            }
        }
    }
}