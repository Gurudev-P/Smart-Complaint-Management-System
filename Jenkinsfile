// CI pipeline: lint -> unit/API tests on PostgreSQL -> browser E2E -> Docker image
pipeline {
  agent any
  options { timestamps(); timeout(time: 30, unit: 'MINUTES') }
  environment {
    PATH = "/Users/gurudev/.docker/bin:/Applications/Docker.app/Contents/Resources/bin:/opt/homebrew/bin:/usr/local/bin:${env.PATH}"
    DOCKER_HOST = 'unix:///Users/gurudev/.docker/run/docker.sock'
    PIP_DISABLE_PIP_VERSION_CHECK = '1'
    TEST_DATABASE_URL = 'postgresql+psycopg://scms:scms@localhost:55432/scms_test'
  }

  stages {
    stage('Setup') {
    steps {
        sh '''
            echo "PATH=$PATH"
            which python3.12
            which docker
            which node

            rm -rf .venv
            /opt/homebrew/bin/python3.12 -m venv .venv
            . .venv/bin/activate
            python --version
            python -m pip install --default-timeout=180 --retries 5 --upgrade pip
            python -m pip install --default-timeout=180 -r requirements-dev.txt
            python -m playwright install --with-deps chromium
        '''

      }
    }
    stage('Lint') {
      steps {
        sh '. .venv/bin/activate && ruff check backend tests'
      }
    }
    stage('Test database') {
      steps {
        sh '''
          docker rm -f scms-ci-db || true
          docker run -d --name scms-ci-db -e POSTGRES_USER=scms -e POSTGRES_PASSWORD=scms -e POSTGRES_DB=scms_test -p 55432:5432 postgres:16-alpine
          for i in $(seq 1 30); do docker exec scms-ci-db pg_isready -U scms && break; sleep 1; done
        '''
      }
    }
    stage('Migrations') {
      steps {
        sh '. .venv/bin/activate && DATABASE_URL=$TEST_DATABASE_URL alembic upgrade head && DATABASE_URL=$TEST_DATABASE_URL alembic check && DATABASE_URL=$TEST_DATABASE_URL alembic downgrade base'
      }
    }
    stage('Unit + API tests') {
      steps {
        sh '. .venv/bin/activate && pytest tests --ignore=tests/e2e --cov=backend/app --cov-report=xml:reports/coverage.xml --cov-fail-under=85 --junitxml=reports/junit-api.xml'
      }
    }
    stage('Front-end unit tests') {
      steps { sh 'node --test tests/frontend/*.test.mjs' }
    }
    stage('E2E tests') {
      steps {
        sh '. .venv/bin/activate && REQ_REPORT_APPEND=1 pytest tests/e2e --junitxml=reports/junit-e2e.xml'
      }
    }
    stage('Docker image') {
      steps { sh 'docker build -t scms:${BUILD_NUMBER} -t scms:latest .' }
    }
  }
  post {
    always {
      junit 'reports/junit-*.xml'
      archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
      sh 'docker rm -f scms-ci-db || true'
    }
  }
}
