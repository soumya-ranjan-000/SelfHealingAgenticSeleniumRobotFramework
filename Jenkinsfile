pipeline {
    agent any

    environment {
        // You must add a 'Secret Text' credential in Jenkins with ID 'gemini-api-key'
        GEMINI_API_KEY = credentials('gemini-api-key')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Install Dependencies') {
            steps {
                // Create virtual environment to avoid system permission issues on Linux
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Robot Tests') {
            steps {
                // Using catchError to ensure the pipeline continues to the post stage 
                // even if tests fail (Robot returns non-zero exit code on test failure)
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    // Run inside the virtual environment
                    sh '''
                        . venv/bin/activate
                        robot -d results tests/
                    '''
                }
            }
        }
    }

    post {
        always {
            // Publisher plugin: https://plugins.jenkins.io/robot/
            // Make sure the Robot Framework plugin is installed in Jenkins
            robot outputPath: 'results',
                  logFileName: 'log.html',
                  outputFileName: 'output.xml',
                  reportFileName: 'report.html',
                  passThreshold: 90.0,
                  unstableThreshold: 70.0
            
            // Archive the artifacts so they are downloadable
            archiveArtifacts artifacts: 'results/*.html, results/*.xml, results/*.png', allowEmptyArchive: true
        }
    }
}
