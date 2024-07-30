# Core_Banking_System-SIN142

Este repositório contém uma arquitetura de microsserviços implementados com FastAPI, Docker e Kubernetes. O objetivo é fornecer um sistema modular e escalável para gerenciar aplicações de forma eficiente.

## Estrutura do Projeto

```
fastapi-microservice/
├── app/
│ ├── ... # Código do primeiro microsserviço
├── another_service/
│ ├── Dockerfile # Dockerfile para o segundo microsserviço
│ └── ... # Código do segundo microsserviço
├── deployment/
│ ├── deployment.yaml # Configuração do Kubernetes para deployments
│ ├── service.yaml # Configuração do Kubernetes para serviços
│ └── another-service.yaml # Configuração para o segundo microsserviço
├── .gitignore
├── Dockerfile # Dockerfile para o primeiro microsserviço
├── docker-compose.yml # Arquivo Docker Compose para construção e gerenciamento dos containers
├── requirements.txt # Dependências do Python
└── README.md # Este arquivo
```

## Pré-requisitos

Antes de começar, verifique se você tem os seguintes programas instalados:

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/)
- [Kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Kubernetes](https://kubernetes.io/docs/setup/)

## Como Executar o Projeto

### Construir e Fazer Push das Imagens

Para construir as imagens Docker e enviá-las para o Docker Hub, execute o script:

```bash
./deploy.sh   # Para Linux/Mac
.\deploy.bat  # Para Windows
```

Rodar um Microserviço de Forma Individual
Se você deseja rodar um microserviço de forma individual, use os seguintes comandos:

Construir a imagem:

```bash
docker build -t fastapi-gateway .
```
Constrói a imagem do microserviço fastapi-gateway a partir do Dockerfile na pasta atual.

Fazer push da imagem:

```bash
docker push fastapi-gateway
```

Envia a imagem fastapi-gateway para o Docker Hub.

Executar o container:

```bash
docker run -d --name fastapi-gateway -p 8000:8000 fastapi-gateway
```

Executa o container do microserviço fastapi-gateway em modo destacado e mapeia a porta 8000 do host para a porta 8000 do container.

Implantar no Kubernetes
Após o push das imagens, o script também aplicará as configurações do Kubernetes, criando os deployments e serviços necessários:

```bash
kubectl apply -f deployment/deployment.yaml
kubectl apply -f deployment/service.yaml
```

Verificar Status dos Serviços no Kubernetes
Para monitorar os serviços em execução no Kubernetes, use os seguintes comandos:

Verificar os pods:

```bash
kubectl get pods
```

Lista todos os pods em execução no cluster Kubernetes.

Verificar os serviços:

```bash
kubectl get services
```

Lista todos os serviços configurados no cluster Kubernetes.

Apagar Todos os Serviços Criados
Se você precisar remover todos os serviços e pods criados, execute:

```bash
kubectl delete all --all
```

Remove todos os recursos (pods, services, deployments, etc.) no namespace atual do Kubernetes.

Acessando os Microsserviços
Após a implantação, você pode acessar os microsserviços através das seguintes URLs:

FastAPI Microservice:
http://<Node-IP>:30001

Outro Microservice:
http://<Node-IP>:30002

Substitua <Node-IP> pelo IP do seu nó Kubernetes.

Estrutura dos Arquivos
Dockerfile
Cada microsserviço possui um Dockerfile que define como a imagem é construída.

docker-compose.yml
O arquivo docker-compose.yml é utilizado para construir as imagens dos microsserviços de forma simplificada.

deployment.yaml e service.yaml
Esses arquivos definem os deployments e serviços no Kubernetes para cada microsserviço.

Contribuição
Se você deseja contribuir para este projeto, fique à vontade para abrir uma issue ou enviar um pull request.

Licença
Este projeto é licenciado sob a MIT License.