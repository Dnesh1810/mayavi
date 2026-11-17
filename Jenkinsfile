pipeline {
    agent any

    stages {
        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        sonar-scanner \
                          -Dsonar.projectKey=mayavi \
                          -Dsonar.sources=mayavi \
                          -Dsonar.projectName=Mayavi
                    '''
                }
            }
        }
    }
}
