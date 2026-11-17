pipeline {
    agent any

    stages {
        stage('SonarQube Analysis') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'

                    withSonarQubeEnv('SonarQube') {
                        sh """
                            ${scannerHome}/bin/sonar-scanner \
                              -Dsonar.projectKey=mayavi \
                              -Dsonar.sources=mayavi \
                              -Dsonar.projectName=Mayavi
                        """
                    }
                }
            }
        }
    }
}
