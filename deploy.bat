@echo off
echo Construindo as imagens...
docker-compose build

echo Fazendo push das imagens...
docker push crisbid/fastapi-gateway:latest
docker push crisbid/fastapi-auth:latest
docker push crisbid/fastapi-transacao:latest
docker push crisbid/fastapi-chavepix:latest
docker push crisbid/fastapi-usuario:latest

echo Criando o Secret para o certificado SSL...
REM kubectl create secret tls cloudflare-cert --cert=Nginx/cloudflare.crt --key=Nginx/cloudflare.key

echo Aplicando o Ingress com SSL...
REM kubectl apply -f Nginx/nginx.yaml

echo Aplicando os deployments e services no Kubernetes...

REM kubectl apply -f deployment/cassandra-deployment.yaml
REM kubectl apply -f deployment/cassandra-service.yaml

docker run --name cassandra -d -p 9042:9042 cassandra:latest

echo Aguardando Cassandra iniciar...
REM timeout /t 90

kubectl apply -f deployment/rabbitmq-deployment.yaml
kubectl apply -f deployment/rabbitmq-service.yaml

echo Aguardando RabbitMQ iniciar...
timeout /t 60

echo Aplicando os deployments e services no Kubernetes...

kubectl apply -f deployment/deployment.yaml
kubectl apply -f deployment/service.yaml

cloudflared tunnel --url http://localhost:30000 run projetosd-tunnel

echo Implantação concluída!
pause
