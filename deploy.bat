@echo off
echo Construindo as imagens...
docker-compose build

echo Fazendo push das imagens...
docker push crisbid/fastapi-gateway:latest
docker push crisbid/fastapi-auth:latest
docker push crisbid/fastapi-transacao:latest

echo Aplicando os deployments e services no Kubernetes...
kubectl apply -f deployment/deployment.yaml
kubectl apply -f deployment/service.yaml

echo Implantação concluída!
pause
