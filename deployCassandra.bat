@echo off

echo Aplicando os deployments e services no Kubernetes...
docker run --name cassandra -d -p 9042:9042 cassandra:latest

echo Implantação concluída!
pause
