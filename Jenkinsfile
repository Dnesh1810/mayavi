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

        stage('Check SonarQube Severity') {
            steps {
                withCredentials([
                    string(credentialsId: 'sonarqube-token',
                           variable: 'SONAR_TOKEN')
                ]) {
                    script {
                        def sonarUrl =
                            'http://sonarqube-sonarqube.cicd.svc.cluster.local:9000'

                        // Wait for SonarQube to finish processing this scan
                        def taskFile = '.scannerwork/report-task.txt'

                        if (!fileExists(taskFile)) {
                            error("SonarQube task file not found")
                        }

                        def taskId = readFile(taskFile)
                            .readLines()
                            .find { it.startsWith('ceTaskId=') }
                            ?.split('=', 2)?.last()

                        if (!taskId) {
                            error("Cannot find SonarQube task ID")
                        }

                        def completed = false

                        for (int i = 0; i < 36; i++) {
                            def response = sh(
                                script: """
                                    curl -fsS -u "\$SONAR_TOKEN:" \
                                    "${sonarUrl}/api/ce/task?id=${taskId}"
                                """,
                                returnStdout: true
                            ).trim()

                            def data = new groovy.json.JsonSlurperClassic()
                                .parseText(response)

                            def status = data.task.status

                            if (status == 'SUCCESS') {
                                completed = true
                                break
                            }

                            if (status == 'FAILED' || status == 'CANCELED') {
                                error("SonarQube processing failed: ${status}")
                            }

                            sleep(time: 5, unit: 'SECONDS')
                        }

                        if (!completed) {
                            error("Timed out waiting for SonarQube analysis")
                        }

                        // Query unresolved legacy severity classifications
                        def issuesJson = sh(
                            script: """
                                curl -fsS -u "\$SONAR_TOKEN:" \
                                "${sonarUrl}/api/issues/search?componentKeys=mayavi&resolved=false&severities=MAJOR%2CCRITICAL%2CBLOCKER&ps=1"
                            """,
                            returnStdout: true
                        ).trim()

                        def issues = new groovy.json.JsonSlurperClassic()
                            .parseText(issuesJson)

                        def count = issues.total as Integer

                        echo "Major/Critical/Blocker issues: ${count}"

                        if (count > 0) {
                            error("BLOCKED: ${count} serious SonarQube issues. Hadoop skipped.")
                        }

                        echo "PASSED: No blocking issues. Hadoop is allowed."
                    }
                }
            }
        }
    }
}
