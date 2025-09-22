
#!/bin/bash
set -eux

# This script will:
# 1. Check for terraform binary
# 2. Generate SSH keypair locally (used by terraform to create aws_key_pair)
# 3. Initialize terraform, run plan, and apply
# Usage: AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... ./deploy.sh

if ! command -v terraform >/dev/null 2>&1; then
  echo "terraform is required but not found in PATH. Please install Terraform v1.2+ and re-run."
  exit 2
fi

# working dir is script location
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# generate local ssh key (private key will be printed by terraform output)
if [ ! -f ./deploy_key ]; then
  ssh-keygen -t rsa -b 4096 -f ./deploy_key -N "" -C "poc-deploy-key"
fi

export TF_IN_AUTOMATION=1

terraform init -input=false
terraform plan -input=false -out=tfplan
terraform apply -input=false -auto-approve tfplan

# print useful outputs
echo "==== Terraform outputs ===="
terraform output
echo "Done."
