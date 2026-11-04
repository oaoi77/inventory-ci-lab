pipeline {
  agent any
  options { timestamps(); disableConcurrentBuilds(); timeout(time: 20, unit: 'MINUTES') }
  parameters {
    booleanParam(name: 'SIMULATE_BAD_DEPLOY', defaultValue: false,
                 description: 'Test failure recovery: the new colour crashes on start')
  }
  environment {
    IMAGE = 'inventory-api'
    CANDIDATE = 'inventory-candidate'
    LIVE = 'inventory-live'
  }
  stages {
    stage('Checkout') {
      steps { checkout scm; sh 'git rev-parse --short HEAD' }
    }
    stage('Lint') {
      steps {
        sh '''
          set -eu
          python3 -m venv .venv
          .venv/bin/pip install -r requirements-dev.txt
          .venv/bin/ruff check app tests
        '''
      }
    }
    stage('Unit tests') {
      steps {
        sh '''
          set -eu
          python3 -m venv .venv
          .venv/bin/pip install -r requirements-dev.txt
          mkdir -p reports
          .venv/bin/python -m pytest -v --junitxml=reports/pytest.xml
        '''
      }
    }
    stage('Build image') {
      steps {
        sh '''
          set -eu
          docker build -t "$IMAGE:$BUILD_NUMBER" .
        '''
      }
    }
    stage('Container smoke test') {
      steps {
        sh '''
          set -eu
          docker rm -f "$CANDIDATE" >/dev/null 2>&1 || true
          docker run -d --name "$CANDIDATE" -p 127.0.0.1:5051:5000 "$IMAGE:$BUILD_NUMBER"
          ready=0
          for i in $(seq 1 20); do
            if curl -fsS http://127.0.0.1:5051/health | grep -q '"status":"ok"'; then ready=1; break; fi
            sleep 1
          done
          test "$ready" -eq 1
          curl -fsS http://127.0.0.1:5051/api/items | grep -q 'router'
        '''
      }
    }
    stage('Image security checks') {
      steps {
        sh '''
          set -eu
          uid=$(docker run --rm --entrypoint id "$IMAGE:$BUILD_NUMBER" -u)
          echo "Container UID: $uid"
          test "$uid" != "0"
          if docker run --rm --entrypoint pip "$IMAGE:$BUILD_NUMBER" list 2>/dev/null | grep -Ei '^(pytest|ruff) '; then
            echo "Dev dependencies found in image"; exit 1
          fi
          if docker run --rm --entrypoint ls "$IMAGE:$BUILD_NUMBER" -a /service | grep -E '^(\\.env|\\.venv|tests)$'; then
            echo "Secrets or dev files found in image"; exit 1
          fi
          echo "Image security checks passed"
        '''
      }
    }
    stage('Blue/green deploy') {
      steps {
        sh '''
          set -eu
          PROXY=inventory-proxy
          NET=inventory-net

          # 1. Which colour is live now? (read the switch inside nginx)
          if docker exec "$PROXY" grep -q inventory-green /etc/nginx/conf.d/default.conf; then
            ACTIVE=green; IDLE=blue
          else
            ACTIVE=blue; IDLE=green
          fi
          echo "Live colour: $ACTIVE -> deploying new version to: $IDLE"

          # 2. Start the new version in the idle colour (users still on $ACTIVE)
          docker rm -f "inventory-$IDLE" >/dev/null 2>&1 || true
          if [ "${SIMULATE_BAD_DEPLOY:-false}" = "true" ]; then
            echo "SIMULATION: new version crashes on start"
            docker run -d --name "inventory-$IDLE" --network "$NET" --entrypoint false "$IMAGE:$BUILD_NUMBER"
          else
            docker run -d --restart unless-stopped --name "inventory-$IDLE" --network "$NET" "$IMAGE:$BUILD_NUMBER"
          fi

          # 3. Health-check the idle colour from inside the network
          ok=0
          for i in $(seq 1 15); do
            if docker exec "$PROXY" wget -qO- "http://inventory-$IDLE:5000/health" 2>/dev/null | grep -q '"status":"ok"'; then ok=1; break; fi
            sleep 1
          done
          if [ "$ok" -ne 1 ]; then
            echo "NEW VERSION UNHEALTHY: traffic stays on $ACTIVE, removing inventory-$IDLE"
            docker logs "inventory-$IDLE" 2>&1 | tail -n 20 || true
            docker rm -f "inventory-$IDLE" >/dev/null 2>&1 || true
            exit 1
          fi

          # 4. Flip the switch: graceful nginx reload, in-flight requests finish on $ACTIVE
          docker cp "deploy/nginx-$IDLE.conf" "$PROXY:/etc/nginx/conf.d/default.conf"
          docker exec "$PROXY" nginx -t
          docker exec "$PROXY" nginx -s reload
          sleep 2

          # 5. Verify through the public port; if it fails, switch back
          if curl -fsS http://127.0.0.1:5050/health | grep -q '"status":"ok"'; then
            echo "SWITCHED: $IDLE is live ($IMAGE:$BUILD_NUMBER); $ACTIVE kept running for rollback"
          else
            echo "POST-SWITCH CHECK FAILED: switching back to $ACTIVE"
            docker cp "deploy/nginx-$ACTIVE.conf" "$PROXY:/etc/nginx/conf.d/default.conf"
            docker exec "$PROXY" nginx -s reload
            exit 1
          fi
        '''
      }
    }
  }
  post {
    always {
      sh 'docker rm -f inventory-candidate >/dev/null 2>&1 || true'
      junit allowEmptyResults: true, testResults: 'reports/pytest.xml'
      archiveArtifacts artifacts: 'reports/*.xml', allowEmptyArchive: true
    }
  }
}
