pipeline {
    agent any

    environment {
        APP_NAME = "deploiement-project-django-app"
        NEXUS_URL = "localhost:5000"
        // Credentials Jenkins
        NEXUS_CREDS = credentials('razi') // ton ID Nexus
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
                script {
                    docker.build("${APP_NAME}:latest")
                }
            }
        }

        stage('Tag & Push to Nexus') {
            steps {
                script {
                    sh """
                        echo ${NEXUS_CREDS_PSW} | docker login ${NEXUS_URL} -u ${NEXUS_CREDS_USR} --password-stdin
                        docker tag ${APP_NAME}:latest ${NEXUS_URL}/${APP_NAME}:latest
                        docker push ${NEXUS_URL}/${APP_NAME}:latest
                    """
                }
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
