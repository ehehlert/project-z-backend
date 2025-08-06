# 1) Rebuild your Docker image
docker build -t project-z-backend .

# 2) Tear down the old container
docker rm -f project-z-backend

# 3) Run a new one (mapping host 5001 → container 5000)
docker run -d \
  --name project-z-backend \
  -p 5001:5000 \
  project-z-backend