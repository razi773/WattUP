pipeline {
    agent any

    environment {
        APP_NAME = "deploiement-project-django-app"
        NEXUS_URL = "localhost:5000"
        NEXUS_CREDS = credentials('razi') // ID Jenkins pour Nexus
        IMAGE_NAME = 'deploiement-project-django-app'
        IMAGE_TAG  = "${env.BUILD_NUMBER}"
        REGISTRY_URL = 'localhost:8081'   // Port du repo Docker
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/razi773/Pfe.git', credentialsId: 'github_token'
            }
        }

        stage('Build & Push Docker Image') {
            steps {
                sh '''
                    set -e
                    echo "Logging into Nexus registry..."
                    docker login -u "$NEXUS_CREDS_USR" -p "$NEXUS_CREDS_PSW" "$REGISTRY_URL"

                    echo "Building image..."
                    docker build -t "$REGISTRY_URL/$IMAGE_NAME:$IMAGE_TAG" -t "$REGISTRY_URL/$IMAGE_NAME:latest" .

                    echo "Pushing image..."
                    docker push "$REGISTRY_URL/$IMAGE_TAG"
                    docker push "$REGISTRY_URL/$IMAGE_NAME:latest"
                '''
            }
        }

        stage('Deploy to Server') {
            when { expression { false } } // Désactivé si pas de serveur
            steps {
                echo 'Deploy skipped; no remote host configured.'
                // Si tu veux activer le déploiement via SSH, décommente et configure correctement :
                /*
                sshagent(['server-ssh-key']) {
                    sh """
                        ssh ${SERVER_USER}@${SERVER_HOST} \\
                        "cd /opt/app && docker-compose pull && docker-compose up -d"
                    """
                }
                */
            }
        }
    }

    post {
        always { echo "Pipeline terminé !" }
        success { echo "Build et déploiement réussis ✅" }
        failure { echo "Erreur dans le pipeline ❌" }
    }
}
