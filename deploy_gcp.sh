#!/bin/bash


set -e

echo "=================================="
echo "Dance Analysis Server - GCP Deployment"
echo "=================================="


APP_NAME="dance-analysis-server"
APP_DIR="/home/$USER/$APP_NAME"
DOCKER_IMAGE="dance-analysis-api"
CONTAINER_NAME="dance-analysis-container"
PORT=8000

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'


echo -e "${GREEN}[1/8] Updating system packages...${NC}"
sudo apt-get update
sudo apt-get upgrade -y

echo -e "${GREEN}[2/8] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    

    newgrp docker <<EONG
    echo -e "${GREEN}Docker installed successfully${NC}"
EONG
else
    echo -e "${YELLOW}Docker already installed${NC}"
fi


echo -e "${GREEN}[3/8] Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}Docker Compose installed successfully${NC}"
else
    echo -e "${YELLOW}Docker Compose already installed${NC}"
fi


echo -e "${GREEN}[4/8] Installing Git...${NC}"
if ! command -v git &> /dev/null; then
    sudo apt-get install -y git
    echo -e "${GREEN}Git installed successfully${NC}"
else
    echo -e "${YELLOW}Git already installed${NC}"
fi


echo -e "${GREEN}[5/8] Setting up application directory...${NC}"
if [ ! -d "$APP_DIR" ]; then
    mkdir -p $APP_DIR
    echo -e "${GREEN}Created directory: $APP_DIR${NC}"
else
    echo -e "${YELLOW}Directory already exists: $APP_DIR${NC}"
fi


echo -e "${GREEN}[6/8] Deploying application code...${NC}"
cd $APP_DIR
echo -e "${YELLOW}Ensure your application files are in: $APP_DIR${NC}"


echo -e "${GREEN}[7/8] Building Docker image...${NC}"
docker build -t $DOCKER_IMAGE .

if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo -e "${YELLOW}Stopping existing container...${NC}"
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi


echo -e "${GREEN}[8/8] Starting application...${NC}"
docker-compose up -d


echo -e "${YELLOW}Waiting for service to start...${NC}"
sleep 10


EXTERNAL_IP=$(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip)

if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo -e "${GREEN}✓ Container is running${NC}"
    
    echo ""
    echo "=================================="
    echo -e "${GREEN}Deployment Successful!${NC}"
    echo "=================================="
    echo ""
    echo "API Endpoints:"
    echo "  - Root: http://$EXTERNAL_IP:$PORT/"
    echo "  - Health: http://$EXTERNAL_IP:$PORT/health"
    echo "  - Upload: http://$EXTERNAL_IP:$PORT/api/v1/analyze"
    echo "  - Status: http://$EXTERNAL_IP:$PORT/api/v1/status/{job_id}"
    echo ""
    echo "View logs: docker logs -f $CONTAINER_NAME"
    echo "Stop server: docker-compose down"
    echo ""
else
    echo -e "${RED}✗ Container failed to start${NC}"
    echo "Check logs: docker logs $CONTAINER_NAME"
    exit 1
fi


echo ""
echo -e "${YELLOW}Configuring GCP firewall rule...${NC}"
FIREWALL_RULE_NAME="allow-dance-analysis-api"

if gcloud compute firewall-rules describe $FIREWALL_RULE_NAME &> /dev/null; then
    echo -e "${YELLOW}Firewall rule already exists${NC}"
else
    
    gcloud compute firewall-rules create $FIREWALL_RULE_NAME \
        --allow tcp:$PORT \
        --source-ranges 0.0.0.0/0 \
        --description "Allow traffic to Dance Analysis API" \
        --direction INGRESS
    
    echo -e "${GREEN}✓ Firewall rule created${NC}"
fi

echo ""
echo "To test the API:"
echo "curl http://$EXTERNAL_IP:$PORT/health"
echo ""
echo "Deployment complete!"
