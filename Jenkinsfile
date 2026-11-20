pipeline {
    agent any

    parameters {
        booleanParam(
            name: 'DEMO_CLEAN',
            defaultValue: false,
            description: 'Demo only: scan clean sample instead of Mayavi'
        )
    }

    stages {
	stage('Test Hadoop Connection') {
    steps {
        withCredentials([
            file(credentialsId: 'hadoop-kubeconfig',
                 variable: 'KUBECONFIG')
        ]) {
            sh '''
                set -eu

                echo "Installing Kubernetes CLI..."
                curl -fsSL \
                  https://dl.k8s.io/release/v1.34.1/bin/linux/amd64/kubectl \
                  -o kubectl
                chmod +x kubectl

                echo "Connecting to Hadoop cluster..."
                ./kubectl get pods -n hadoop

                echo "HADOOP CONNECTION SUCCESSFUL"
            '''
        }
    }
}
        stage('SonarQube Analysis') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'
                    def scanKey = params.DEMO_CLEAN ? 'mayavi-clean-demo' : 'mayavi'
                    def scanSources = params.DEMO_CLEAN ? 'ci/clean_demo' : 'mayavi'
                    env.SCAN_KEY = scanKey
                    echo "Scanning project: ${scanKey}" 

                    withSonarQubeEnv('SonarQube') {
                        sh """
                            ${scannerHome}/bin/sonar-scanner \
                              -Dsonar.projectKey=${scanKey} \
                              -Dsonar.sources=${scanSources} \
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
                                "${sonarUrl}/api/issues/search?componentKeys=${env.SCAN_KEY}&resolved=false&severities=MAJOR%2CCRITICAL%2CBLOCKER&ps=1"
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

        stage('Run Hadoop MapReduce') {
            steps {
                withCredentials([
                    file(credentialsId: 'hadoop-kubeconfig',
                         variable: 'KUBECONFIG')
                ]) {
                    sh '''
                        set -eu

                        MASTER=$(./kubectl get pods -n hadoop                           -l app=hadoop-master                           -o jsonpath='{.items[0].metadata.name}')

                        echo "Preparing Hadoop job on $MASTER"

                        ./kubectl cp ci/mapper.py                           "hadoop/$MASTER:/tmp/mapper.py" -c namenode
                        ./kubectl cp ci/reducer.py                           "hadoop/$MASTER:/tmp/reducer.py" -c namenode

                        ./kubectl cp mayavi/filters/mask_points.py                           "hadoop/$MASTER:/tmp/mask_points.py" -c namenode
                        ./kubectl cp mayavi/filters/filter_base.py                           "hadoop/$MASTER:/tmp/filter_base.py" -c namenode

                        ./kubectl exec -n hadoop "$MASTER" -c namenode --                           hdfs dfs -mkdir -p /input-jenkins

                        for FILE in mask_points.py filter_base.py; do
                          ./kubectl exec -n hadoop "$MASTER" -c namenode --                             hdfs dfs -put -f "/tmp/$FILE" /input-jenkins/
                        done

                        ./kubectl exec -n hadoop "$MASTER" -c namenode --                           hdfs dfs -rm -r -f /output-jenkins || true

                        ./kubectl exec -n hadoop "$MASTER" -c namenode --                           hadoop jar                           /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.4.2.jar                           -D mapreduce.job.name=JenkinsMayaviLineCount                           -D mapreduce.job.reduces=1                           -files /tmp/mapper.py,/tmp/reducer.py                           -mapper "python mapper.py"                           -reducer "python reducer.py"                           -input /input-jenkins                           -output /output-jenkins

                        echo "HADOOP MAPREDUCE RESULTS:"
                        ./kubectl exec -n hadoop "$MASTER" -c namenode --                           hdfs dfs -cat /output-jenkins/part-00000

                        echo "HADOOP MAPREDUCE SUCCESSFUL"
                    '''
                }
            }
        }

    }
}
