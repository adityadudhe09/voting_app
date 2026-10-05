# Voting App on Kubernetes

This repository contains a Flask voting API and Kubernetes manifests for running
it with DynamoDB Local. The local database is created and seeded automatically
when the application starts.

## Prerequisites

- Docker
- A Kubernetes cluster with `kubectl` configured (for example, Docker Desktop,
  kind, or minikube)

## Build and deploy

Build the application image from the repository root:

```sh
docker build -t votingapp:local .
```

If you use kind or minikube, load the image into that cluster after building:

```sh
kind load docker-image votingapp:local
```

or:

```sh
minikube image load votingapp:local
```

Create the namespace, then deploy DynamoDB Local and the application:

```sh
kubectl apply -f k8s/namespace.yaml
kubectl apply -k k8s/
kubectl rollout status deployment/dynamodb -n votingapp
kubectl rollout status deployment/votingapp -n votingapp
```

The application deployment runs an initialization container before the Flask
container. It waits for DynamoDB Local, creates the `votingapp-restaurants`
table if needed, and initializes missing restaurant records to zero without
resetting existing vote counts.

Forward the service to your machine:

```sh
kubectl port-forward -n votingapp service/votingapp 8080:8080
```

In another terminal, call the API:

```sh
curl http://localhost:8080/
curl http://localhost:8080/api/getvotes
curl http://localhost:8080/api/outback
```

Other vote endpoints are `/api/bucadibeppo`, `/api/ihop`, and `/api/chipotle`.
The `/api/getheavyvotes` endpoint is experimental and intentionally consumes
additional CPU and memory.

## Local database behavior

DynamoDB Local runs in memory for this setup. Vote data is lost if its pod is
recreated; this keeps the from-scratch local deployment simple and avoids
requiring a cluster-specific persistent-volume provisioner. The manifests use
dummy AWS credentials only for DynamoDB Local and do not require an AWS account.

The application can also be configured with `DDB_AWS_REGION`, `DDB_TABLE_NAME`,
and `DDB_ENDPOINT_URL`. Leave `DDB_ENDPOINT_URL` unset when connecting to AWS
DynamoDB; configure AWS credentials using the deployment platform's recommended
identity mechanism.

## Remove the deployment

```sh
kubectl delete namespace votingapp
```

## License

This application is made available under the [MIT license](./LICENSE).
