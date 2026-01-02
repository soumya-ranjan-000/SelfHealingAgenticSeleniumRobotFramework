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
                // creating a venv is recommended, but for simplicity on a reusable agent, 
                // we assume direct pip or use a virtualenv if tools allow. 
                // simpler for windows agent often just uses the system python or a pre-configured venv.
                // We will assume 'pip' is on PATH.
                bat 'pip install -r requirements.txt'
            }
        }

        stage('Run Robot Tests') {
            steps {
                // Using catchError to ensure the pipeline continues to the post stage 
                // even if tests fail (Robot returns non-zero exit code on test failure)
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    bat 'robot -d results tests/'
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
