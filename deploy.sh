# get AWS login
aws ecr get-login-password \
  --region us-east-2 \
| docker login \
  --username AWS \
  --password-stdin 637423518604.dkr.ecr.us-east-2.amazonaws.com

# build for amazon linux
docker build \
  --platform linux/amd64 \
  -t 637423518604.dkr.ecr.us-east-2.amazonaws.com/pgz:latest \
  .

# push to ECR
docker push 637423518604.dkr.ecr.us-east-2.amazonaws.com/pgz:latest

# set .pem permissions (requires EC2 key pair to be in ~/.ssh folder in your computer)
chmod 400 ~/.ssh/pgz-backend-dev-kp.pem

# ssh into EC2 and auto-run build steps (requires EC2 key pair to be in ~/.ssh folder in your computer)
ssh -i ~/.ssh/pgz-backend-dev-kp.pem ec2-user@ec2-3-137-156-71.us-east-2.compute.amazonaws.com << 'EOF'
  aws ecr get-login-password --region us-east-2 \
    | docker login --username AWS --password-stdin 637423518604.dkr.ecr.us-east-2.amazonaws.com

  docker pull 637423518604.dkr.ecr.us-east-2.amazonaws.com/pgz:latest
  docker rm -f project-z-backend || true
  docker run -d --name project-z-backend -p 80:5000 637423518604.dkr.ecr.us-east-2.amazonaws.com/pgz:latest

  exit
EOF