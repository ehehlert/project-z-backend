### How to deploy to ECR

From console within this project directory:

```bash
aws ecr get-login-password \
  --region us-east-2 \
| docker login \
  --username AWS \
  --password-stdin 637423518604.dkr.ecr.us-east-2.amazonaws.com
```

```bash
docker build \
  --platform linux/amd64 \
  -t 637423518604.dkr.ecr.us-east-2.amazonaws.com/pgz:latest \
  .
```

```bash
docker push 637423518604.dkr.ecr.us-east-2.amazonaws.com/pgz:latest
```

### How to pull updated image into EC2 and restart service

Navigate / SSH into EC2 instance

```bash
aws ecr get-login-password --region us-east-2   | docker login     --username AWS     --password-stdin 637423518604.dkr.ecr.us-east-2.amazonaws.com
```

```bash
docker pull 637423518604.dkr.ecr.us-east-2.amazonaws.com/pgz:latest
```

```bash
docker rm -f project-z-backend
```

```bash
docker run -d   --name project-z-backend   -p 80:5000   637423518604.dkr.ecr.us-east-2.amazonaws.com/pgz:latest
```
