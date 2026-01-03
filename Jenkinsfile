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
                
                // Install GitHub CLI (gh) local to the workspace
                // Install GitHub CLI (gh) local to the workspace
                sh '''
                    # Use POSIX compliant redirection (> /dev/null 2>&1) for sh compatibility
                    if ! command -v gh > /dev/null 2>&1; then
                        echo "Installing GitHub CLI..."
                        mkdir -p bin
                        
                        # Download using curl or fallback to wget
                        if command -v curl > /dev/null 2>&1; then
                             curl -fsSL https://github.com/cli/cli/releases/download/v2.40.0/gh_2.40.0_linux_amd64.tar.gz -o ghcli.tar.gz
                        elif command -v wget > /dev/null 2>&1; then
                             wget -O ghcli.tar.gz https://github.com/cli/cli/releases/download/v2.40.0/gh_2.40.0_linux_amd64.tar.gz
                        else
                             echo "Error: Neither curl nor wget found. Cannot install GitHub CLI."
                             exit 1
                        fi

                        # Extract just the binary to ./bin
                        tar -xzf ghcli.tar.gz -C bin --strip-components=2 gh_2.40.0_linux_amd64/bin/gh
                        chmod +x bin/gh
                        rm ghcli.tar.gz
                        echo "GitHub CLI installed to ${WORKSPACE}/bin/gh"
                    else
                        echo "GitHub CLI already installed globally."
                    fi
                '''
            }
        }

        stage('Run Robot Tests') {
            steps {
                // Using catchError to ensure the pipeline continues to the post stage 
                // even if tests fail (Robot returns non-zero exit code on test failure)
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    // Run inside the virtual environment
                    // Use the run_tests_with_healing script to ensure log generation, 
                    // though strictly speaking we can run robot directly if we rely on the GenAIRescuer hooks.
                    // For now, let's stick to standard robot execution since Apply Self-Healing script handles the log processing.
                    sh '''
                        . venv/bin/activate
                        robot -d results -v HEADLESS:True tests/
                    '''
                }
            }
        }

        stage('Apply Self-Healing') {
            when {
                // Only run if the healing log exists
                expression {
                    return fileExists('healing_log.json')
                }
            }
            steps {
                script {
                    echo "Healing log found. Applying updates..."
                    sh '''
                        . venv/bin/activate
                        python scripts/apply_healing_updates.py
                    '''
                }
            }
        }

        stage('Create PR') {
            when {
                // distinct from Apply Self-Healing, strictly checks git status
                expression {
                    // Check if there are any modified files tracked by git
                    return sh(returnStatus: true, script: 'git diff --quiet') != 0
                }
            }
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'github-token', passwordVariable: 'GH_TOKEN', usernameVariable: 'GH_USER')]) {
                        def branchName = "healing/auto-fix-${env.BUILD_NUMBER}"
                        
                        sh """
                            # Add local bin to PATH so 'gh' is found
                            export PATH=${WORKSPACE}/bin:\$PATH
                            
                            git config --global user.email "jenkins-bot@example.com"
                            git config --global user.name "Jenkins Bot"
                            
                            echo "Changes detected. Creating PR..."
                            git checkout -b ${branchName}
                            git add locators/
                            git commit -m "fix(healing): Auto-fix locators [Build ${env.BUILD_NUMBER}]"
                            
                            # Push with credentials
                            git push https://${GH_USER}:${GH_TOKEN}@github.com/soumya-ranjan-000/SelfHealingAgenticSeleniumRobotFramework.git ${branchName}
                            
                            # Create PR using gh cli
                            if command -v gh &> /dev/null; then
                                echo "Creating PR via GitHub CLI..."
                                gh pr create --title "Auto-fix Locators [Build ${env.BUILD_NUMBER}]" --body "Automated PR from Jenkins. Self-healing agent fixed broken locators." --head ${branchName} --base main
                            else
                                echo "gh CLI not found even after installation attempt. Manual PR required for branch ${branchName}"
                            fi
                        """
                    }
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
            archiveArtifacts artifacts: 'results/*.html, results/*.xml, results/*.png, healing_log.json', allowEmptyArchive: true
        }
    }
}
