
#!/bin/bash
set -eux

sudo apt-get update -y
sudo apt-get install -y gnupg lsb-release unzip python3-pip

# 2. Install required packages for apt to use HTTPS
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 3. Add Docker’s official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 4. Set up the Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. Update apt package index again (with Docker repo now)
sudo apt-get update

# 6. Install Docker
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
sudo apt  install -y awscli

# 7. Enable Docker on boot
sudo systemctl enable docker

# 8. Start Docker
sudo systemctl start docker

# 9. (Optional) Add user to docker group to run without sudo
sudo usermod -aG docker $USER

pip3 install awscli --upgrade --user
export PATH=$PATH:/root/.local/bin

# download app.zip from S3 (bucket name will be substituted by Terraform)
BUCKET_NAME="${bucket_name}"
aws s3 cp s3://myapp-bucket/app.zip /tmp/app.zip
sudo mkdir -p /opt/pocapp
sudo mkdir -p /var/log/myapp
sudo chown $USER:$USER /var/log/myapp
sudo unzip /tmp/app.zip -d /opt/pocapp
cd /opt/pocapp

# install docker-compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# assume docker-compose.yml present at root of archive
sudo docker-compose config   # Optional: validate config
/usr/local/bin/docker-compose up -d

sudo docker-compose up -d