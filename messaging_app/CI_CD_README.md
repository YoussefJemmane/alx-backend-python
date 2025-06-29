# CI/CD Setup for Django Messaging App

This repository contains a complete CI/CD setup for the Django messaging application using both Jenkins and GitHub Actions.

## Overview

The CI/CD pipeline includes:
- **Jenkins Pipeline**: For containerized CI/CD with Docker
- **GitHub Actions**: For cloud-based CI/CD
- **Automated Testing**: Using pytest and Django's testing framework
- **Code Quality**: Using flake8 for linting
- **Docker**: For containerization and deployment
- **MySQL**: Database support for testing and production

## Files Structure

```
messaging_app/
├── .github/
│   └── workflows/
│       ├── ci.yml          # GitHub Actions CI workflow
│       └── dep.yml         # GitHub Actions deployment workflow
├── Jenkinsfile             # Jenkins pipeline script
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Local development setup
├── requirements.txt        # Python dependencies
├── pytest.ini            # Pytest configuration
├── .flake8               # Flake8 configuration
├── test_messaging_app.py  # Test suite
└── CI_CD_README.md        # This file
```

## Task 0: Jenkins Setup

### Prerequisites
- Docker installed and running
- GitHub repository with your code

### 1. Run Jenkins in Docker

```bash
docker run -d --name jenkins -p 8080:8080 -p 50000:50000 -v jenkins_home:/var/jenkins_home jenkins/jenkins:lts
```

### 2. Initial Jenkins Setup

1. Access Jenkins at `http://localhost:8080`
2. Get the initial admin password:
   ```bash
   docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
   ```
3. Install suggested plugins
4. Create an admin user

### 3. Required Jenkins Plugins

Install these plugins through Jenkins Plugin Manager:
- **Git Plugin**: For GitHub integration
- **Pipeline Plugin**: For pipeline support
- **ShiningPanda Plugin**: For Python environment management
- **Docker Pipeline Plugin**: For Docker integration
- **HTML Publisher Plugin**: For test reports

### 4. Configure Credentials

#### GitHub Credentials:
1. Go to Jenkins → Manage Jenkins → Manage Credentials
2. Add new credential (Username with password)
3. ID: `github-credentials`
4. Username: Your GitHub username
5. Password: Your GitHub personal access token

#### Docker Hub Credentials:
1. Add new credential (Username with password)
2. ID: `docker-hub-credentials`
3. Username: Your Docker Hub username
4. Password: Your Docker Hub password

### 5. Create Jenkins Pipeline

1. New Item → Pipeline
2. In Pipeline section, select "Pipeline script from SCM"
3. SCM: Git
4. Repository URL: Your GitHub repository
5. Credentials: Select your GitHub credentials
6. Script Path: `messaging_app/Jenkinsfile`

### 6. Update Jenkinsfile Variables

Edit the `Jenkinsfile` and update:
```groovy
environment {
    DOCKER_IMAGE = 'your-dockerhub-username/messaging-app'
    // ... other variables
    git credentialsId: "${GITHUB_CREDENTIALS_ID}",
        url: 'https://github.com/your-username/alx-backend-python.git',
        branch: 'main'
}
```

## Task 2 & 3: GitHub Actions Setup

### 1. Repository Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

- `DOCKER_USERNAME`: Your Docker Hub username
- `DOCKER_PASSWORD`: Your Docker Hub password

### 2. Update GitHub Actions Workflows

Edit `.github/workflows/dep.yml` and update:
```yaml
env:
  DOCKER_IMAGE: your-dockerhub-username/messaging-app
```

### 3. Workflow Features

#### CI Workflow (`ci.yml`):
- Runs on every push and pull request
- Sets up Python 3.11 environment
- Installs dependencies
- Sets up MySQL database for testing
- Runs pytest with coverage
- Performs flake8 code quality checks
- Generates and uploads coverage reports
- Comments coverage on pull requests

#### Deployment Workflow (`dep.yml`):
- Runs on main branch pushes and releases
- Builds multi-platform Docker images (amd64, arm64)
- Pushes to Docker Hub with multiple tags
- Performs security scanning with Trivy
- Creates deployment summaries
- Creates issues on deployment failures

## Local Development

### Using Docker Compose

1. **Start the application:**
   ```bash
   docker-compose up --build
   ```

2. **Run tests:**
   ```bash
   docker-compose exec web python manage.py test
   # or
   docker-compose exec web pytest
   ```

3. **Run migrations:**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

### Manual Setup

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run tests:**
   ```bash
   pytest
   # or
   python manage.py test
   ```

4. **Code quality check:**
   ```bash
   flake8 .
   ```

## Testing

### Test Structure

The test suite includes:
- **Unit Tests**: Model and basic functionality tests
- **Integration Tests**: API endpoint tests
- **Pytest Integration**: Modern Python testing
- **Coverage Reports**: HTML and XML coverage reports

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest test_messaging_app.py

# Run with verbose output
pytest -v
```

## Code Quality

### Flake8 Configuration

The `.flake8` file configures:
- Maximum line length: 127 characters
- Maximum complexity: 10
- Excludes: migrations, cache directories, virtual environments
- Custom rules for Django settings and test files

### Running Code Quality Checks

```bash
# Basic check
flake8 .

# Detailed check with statistics
flake8 . --count --statistics --show-source
```

## Docker

### Building the Image

```bash
# Build locally
docker build -t messaging-app .

# Build with specific tag
docker build -t your-username/messaging-app:v1.0 .
```

### Running the Container

```bash
# Run with SQLite (default)
docker run -p 8000:8000 messaging-app

# Run with MySQL
docker run -p 8000:8000 \
  -e MYSQL_DATABASE=messaging_app \
  -e MYSQL_USER=user \
  -e MYSQL_PASSWORD=password \
  -e MYSQL_HOST=mysql-host \
  messaging-app
```

## Troubleshooting

### Common Issues

1. **Jenkins Build Fails**: Check Docker daemon is running and credentials are correct
2. **GitHub Actions Timeout**: MySQL service might take time to start
3. **Test Failures**: Ensure database permissions and migrations are correct
4. **Docker Build Fails**: Check Dockerfile and requirements.txt

### Debug Commands

```bash
# Check Jenkins logs
docker logs jenkins

# Check application logs
docker-compose logs web

# Test database connection
docker-compose exec web python manage.py dbshell
```

## Next Steps

1. **Monitoring**: Add application monitoring (e.g., Prometheus, Grafana)
2. **Security**: Implement security scanning in CI/CD
3. **Deployment**: Set up production deployment (Kubernetes, ECS, etc.)
4. **Notifications**: Configure Slack/email notifications for build status
5. **Performance**: Add performance testing to the pipeline

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all tests pass
5. Submit a pull request

The CI/CD pipeline will automatically run tests and quality checks on your pull request.

