# Data Analyzer on Kubernetes

A Streamlit-based data analytics application that lets users upload CSV/XLSX files and get instant exploratory analysis, visualizations, and automated data-quality insights.  
This repository includes everything needed to run the app locally, package it with Docker, and deploy it to Minikube with Kubernetes.

## Features

- Upload `CSV` and `XLSX` datasets from the browser
- Automatic overview metrics (rows, columns, missing values, numeric columns)
- Descriptive statistics for numeric columns
- Correlation heatmap for multi-numeric datasets
- Auto-generated insights (missing data, correlations, skewness, cardinality hints)
- Interactive line, bar, and scatter charts
- Kubernetes-ready deployment with health probes and resource limits

## Project Structure

```text
data_analytics_app/
|-- app.py
|-- requirements.txt
|-- Dockerfile
|-- deployment.yaml
|-- service.yaml
`-- README.md
```

## Tech Stack

- Python 3.11
- Streamlit
- Pandas
- NumPy
- Matplotlib
- Docker
- Kubernetes (Minikube)

## Prerequisites

Install the following tools before you begin:

- [Python 3.11+](https://www.python.org/downloads/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Minikube](https://minikube.sigs.k8s.io/docs/start/)

## Run Locally (Without Docker)

From the `data_analytics_app` directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

App URL: `http://localhost:8501`

## Build and Run with Docker (Local Docker Daemon)

```powershell
docker build -t data-analyzer:latest .
docker run --rm -p 8501:8501 data-analyzer:latest
```

App URL: `http://localhost:8501`

## Deploy to Minikube

### 1) Start Minikube

```powershell
minikube start
```

### 2) Point Docker to Minikube's Docker daemon

Use the command that matches your shell:

- **PowerShell (Windows):**

```powershell
minikube -p minikube docker-env --shell powershell | Invoke-Expression
```

- **bash/zsh (Linux/macOS):**

```bash
eval $(minikube docker-env)
```

### 3) Build the image inside Minikube

```powershell
docker build -t data-analyzer:latest .
```

### 4) Apply Kubernetes manifests

```powershell
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### 5) Verify deployment

```powershell
kubectl get pods -w
kubectl get deploy,svc
```

Wait until pod status is `Running` and readiness is `1/1`.

### 6) Open the app

```powershell
minikube service data-analyzer-service
```

This command opens the app URL in your browser.

## Kubernetes Resources

- `deployment.yaml`
  - Deployment name: `data-analyzer`
  - Replicas: `1`
  - Container image: `data-analyzer:latest`
  - `imagePullPolicy: Never` (expects image built in Minikube Docker daemon)
  - Readiness and liveness probes on `/_stcore/health`

- `service.yaml`
  - Service name: `data-analyzer-service`
  - Type: `NodePort`
  - Service port: `80`
  - Target port: `8501`

## Useful Commands

```powershell
# Check resources
kubectl get all

# Inspect pod details
kubectl describe pod -l app=data-analyzer

# View application logs
kubectl logs -l app=data-analyzer --tail=200

# Clean up Kubernetes resources
kubectl delete -f service.yaml
kubectl delete -f deployment.yaml

# Reset Docker env to your default daemon (PowerShell)
minikube docker-env --unset | Invoke-Expression
```

## Troubleshooting

- **`eval` not recognized on Windows PowerShell**
  - Use:
    - `minikube -p minikube docker-env --shell powershell | Invoke-Expression`

- **Image pull errors (`ErrImagePull` / `ImagePullBackOff`)**
  - Ensure image was built after switching Docker to Minikube daemon.
  - Confirm deployment uses `image: data-analyzer:latest` and `imagePullPolicy: Never`.

- **Service not reachable**
  - Run `minikube status` and verify cluster is running.
  - Run `kubectl get pods,svc` and confirm resources are healthy.
  - Use `minikube service data-analyzer-service` instead of manually guessing NodePort.

- **App crashes on startup**
  - Check logs: `kubectl logs -l app=data-analyzer`
  - Verify dependencies from `requirements.txt` installed successfully during image build.

## Notes for Contributors

- Keep dependency versions explicit in `requirements.txt` for reproducibility.
- If you change ports, update `Dockerfile`, probes in `deployment.yaml`, and `service.yaml` consistently.
- Test both local and Minikube workflows before submitting changes.
