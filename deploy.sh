#!/bin/bash

# Build das imagens
echo "Construindo as imagens..."
docker-compose build

# Push das imagens
echo "Fazendo push das imagens..."
docker push crisbid/fastapi-gateway:latest
docker push crisbid/fastapi-auth:latest
docker push crisbid/fastapi-transacao:latest

# Aplicar configurações no Kubernetes
echo "Aplicando os deployments e services no Kubernetes..."
kubectl apply -f deployment/deployment.yaml
kubectl apply -f deployment/service.yaml

echo "Implantação concluída!"
