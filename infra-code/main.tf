
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.2.0"
}

provider "aws" {
  region     = var.aws_region
  # Credentials are expected via environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
}

resource "aws_vpc" "poc_vpc" {
  cidr_block = "10.0.0.0/16"
  tags = { Name = "poc-vpc" }
}

resource "aws_subnet" "poc_subnet" {
  vpc_id            = aws_vpc.poc_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]
  tags = { Name = "poc-subnet" }
}

data "aws_availability_zones" "available" {}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.poc_vpc.id
  tags = { Name = "poc-igw" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.poc_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = { Name = "poc-public-rt" }
}

resource "aws_route_table_association" "rta" {
  subnet_id      = aws_subnet.poc_subnet.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "ssh_http" {
  name        = "poc-sg"
  description = "Allow SSH and HTTP"
  vpc_id      = aws_vpc.poc_vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 3001
    to_port     = 3001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "poc-sg" }
}

resource "aws_key_pair" "deploy_key" {
  key_name   = "deploy_key"
  public_key = tls_private_key.ssh_key.public_key_openssh
}

resource "tls_private_key" "ssh_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# S3 bucket to host the app archive
resource "aws_s3_bucket" "app_bucket" {
  bucket = "${var.project_name}-bucket"
  force_destroy = true
  tags = { Name = "${var.project_name}-bucket" }
}

resource "aws_s3_object" "app_zip" {
  bucket = aws_s3_bucket.app_bucket.id
  key    = "app.zip"
  source = "${path.module}/files/app.zip"
  etag   = filemd5("${path.module}/files/app.zip")
}

# IAM role and instance profile to allow S3 read
data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ec2_role" {
  name               = "${var.project_name}-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_policy" "s3_read_policy" {
  name   = "${var.project_name}-s3-read"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:CreateBucket",
          "s3:PutBucketAcl",
          "s3:PutBucketPolicy",
          "s3:GetBucketLocation",
          "s3:DeleteBucket",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Effect   = "Allow"
        Resource = [
          aws_s3_bucket.app_bucket.arn,
          "${aws_s3_bucket.app_bucket.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.s3_read_policy.arn
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-instance-profile"
  role = aws_iam_role.ec2_role.name
}

resource "aws_instance" "app_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t2.micro"
  subnet_id              = aws_subnet.poc_subnet.id
  vpc_security_group_ids = [aws_security_group.ssh_http.id]
  key_name               = aws_key_pair.deploy_key.key_name
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  associate_public_ip_address = true
  user_data = templatefile("${path.module}/user_data.sh", {
  bucket_name = aws_s3_bucket.app_bucket.bucket
  })

  tags = { Name = "${var.project_name}-instance" }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }
}

output "instance_public_ip" {
  value = aws_instance.app_server.public_ip
}

output "s3_bucket" {
  value = aws_s3_bucket.app_bucket.id
}

output "ssh_private_key_pem" {
  value     = tls_private_key.ssh_key.private_key_pem
  sensitive = true
}
