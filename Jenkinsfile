pipeline {
    agent any

    environment {
        NEXUS_URL = "localhost:5000"
        NEXUS_USER = "admin"
        NEXUS_PASS = "ton_mot_de_passe" // change avec ton mot de passe Nexus
        APP_NAME = "deploiement-project-django-app"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/ton-compte/ton-projet-django.git'
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
                    sh "docker tag ${APP_NAME}:latest ${NEXUS_URL}/${APP_NAME}:latest"
                    sh "echo ${NEXUS_PASS} | docker login ${NEXUS_URL} -u ${NEXUS_USER} --password-stdin"
                    sh "docker push ${NEXUS_URL}/${APP_NAME}:latest"
                }
            }
        }

        stage('Deploy to Server') {
            steps {
                sshagent(['SERVER_SSH_KEY']) {
                    sh '''
                        ssh $SERVER_USER@$SERVER_HOST "cd /opt/app && docker-compose pull && docker-compose up -d"
                    '''
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline terminé !"
        }
        success {
            echo "Build et déploiement réussis ✅"
        }
        failure {
            echo "Erreur dans le pipeline ❌"
        }
    }
}
