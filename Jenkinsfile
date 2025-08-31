pipeline {
    agent any

    environment {
        APP_NAME = "deploiement-project-django-app"
        NEXUS_URL = "localhost:5000"
        // Credentials Jenkins
        NEXUS_CREDS = credentials('razi') // ton ID Nexus
        IMAGE_NAME = 'deploiement-project-django-app'
        IMAGE_TAG  = "${env.BUILD_NUMBER}"
        REGISTRY_URL = 'localhost:8081'   // e.g. nexus.example.com:8083
    }

    stages {
        stage('Checkout') {
            steps {
                // Utilisation du token GitHub
                git branch: 'main', url: 'https://github.com/razi773/Pfe.git', credentialsId: 'github_token'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    set -e
                    echo "Logging into Nexus registry..."
                    docker login -u "$NEXUS_CREDS_USR" -p "$NEXUS_CREDS_PSW" "$REGISTRY_URL"

                    echo "Building image..."
                    docker build -t "$REGISTRY_URL/$IMAGE_NAME:$IMAGE_TAG" -t "$REGISTRY_URL/$IMAGE_NAME:latest" .

                    echo "Pushing image..."
                    docker push "$REGISTRY_URL/$IMAGE_NAME:$IMAGE_TAG"
                    docker push "$REGISTRY_URL/$IMAGE_NAME:latest"
                '''
            }
        }

        stage('Tag & Push to Nexus') {
            when { expression { false } }
            steps {
                echo 'Handled during build stage.'
            }
        }

        stage('Deploy to Server') {
            when { expression { false } } // No remote host provided
            steps {
                echo 'No remote host configured; skipping deploy.'
            }
        }
    }

    post {
        always { echo "Pipeline terminé !" }
        success { echo "Build et déploiement réussis ✅" }
        failure { echo "Erreur dans le pipeline ❌" }
    }
}
            when { expression { false } }
            steps {
                echo 'Handled during remote build stage.'
            }
        }

        stage('Deploy to Server') {
            steps {
                sshagent(['server-ssh-key']) {
                    sh """
                        ssh ${SERVER_USER}@${SERVER_HOST} \\
                        "cd /opt/app && docker-compose pull && docker-compose up -d"
                    """
                }
            }
        }
    }

    post {
        always { echo "Pipeline terminé !" }
        success { echo "Build et déploiement réussis ✅" }
        failure { echo "Erreur dans le pipeline ❌" }
    }
}
