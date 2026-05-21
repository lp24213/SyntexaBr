# ============================================================
# VEREDA / SYNTEXA — AWS GPU Cluster (Terraform)
# Região: us-east-1
# ============================================================
terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ── VPC PRIVADA ────────────────────────────────────────────
resource "aws_vpc" "vereda" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name    = "vereda-vpc"
    Project = "syntexa"
  }
}

# ── SUBNETS ────────────────────────────────────────────────
resource "aws_subnet" "private_gpu" {
  vpc_id            = aws_vpc.vereda.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name    = "vereda-private-gpu"
    Project = "syntexa"
  }
}

resource "aws_subnet" "private_orchestrator" {
  vpc_id            = aws_vpc.vereda.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}b"

  tags = {
    Name    = "vereda-private-orchestrator"
    Project = "syntexa"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.vereda.id
  cidr_block              = "10.0.100.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name    = "vereda-public"
    Project = "syntexa"
  }
}

# ── INTERNET GATEWAY ───────────────────────────────────────
resource "aws_internet_gateway" "vereda" {
  vpc_id = aws_vpc.vereda.id
  tags = {
    Name    = "vereda-igw"
    Project = "syntexa"
  }
}

# ── NAT GATEWAY ────────────────────────────────────────────
resource "aws_eip" "nat" {
  domain = "vpc"
  tags = {
    Name = "vereda-nat-eip"
  }
}

resource "aws_nat_gateway" "vereda" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public.id
  tags = {
    Name    = "vereda-nat"
    Project = "syntexa"
  }
  depends_on = [aws_internet_gateway.vereda]
}

# ── ROUTE TABLES ───────────────────────────────────────────
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.vereda.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.vereda.id
  }
  tags = {
    Name = "vereda-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.vereda.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.vereda.id
  }
  tags = {
    Name = "vereda-private-rt"
  }
}

resource "aws_route_table_association" "private_gpu" {
  subnet_id      = aws_subnet.private_gpu.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_orch" {
  subnet_id      = aws_subnet.private_orchestrator.id
  route_table_id = aws_route_table.private.id
}

# ── SECURITY GROUPS ──────────────────────────────────────
resource "aws_security_group" "gpu_cluster" {
  name_prefix = "vereda-gpu-"
  vpc_id      = aws_vpc.vereda.id
  description = "Security group for VEREDA GPU cluster"

  # Internal VPC only
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.vereda.cidr_block]
    description = "Allow all internal VPC traffic"
  }

  # SSH via bastion only (Cloudflare Tunnel)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [aws_subnet.public.cidr_block]
    description = "SSH from public subnet only"
  }

  # Egress
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "vereda-gpu-sg"
    Project = "syntexa"
  }
}

resource "aws_security_group" "orchestrator" {
  name_prefix = "vereda-orch-"
  vpc_id      = aws_vpc.vereda.id
  description = "Security group for VEREDA orchestrator"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH access"
  }

  ingress {
    from_port   = 8000
    to_port     = 8003
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "VEREDA services"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "vereda-orch-sg"
    Project = "syntexa"
  }
}

# ── IAM ROLE ─────────────────────────────────────────────
resource "aws_iam_role" "gpu_role" {
  name = "vereda-gpu-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "gpu_policy" {
  name = "vereda-gpu-policy"
  role = aws_iam_role.gpu_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "arn:aws:s3:::vereda-models-*/*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "gpu_profile" {
  name = "vereda-gpu-profile"
  role = aws_iam_role.gpu_role.name
}

# ── GPU CLUSTER (g5.xlarge) ──────────────────────────────
data "aws_ami" "ubuntu_gpu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Spot instance request para economia de ~70%
resource "aws_spot_instance_request" "gpu_cluster" {
  count                  = var.use_spot ? 1 : 0
  ami                    = data.aws_ami.ubuntu_gpu.id
  instance_type          = var.gpu_instance_type
  subnet_id              = aws_subnet.private_gpu.id
  vpc_security_group_ids = [aws_security_group.gpu_cluster.id]
  iam_instance_profile   = aws_iam_instance_profile.gpu_profile.name

  spot_price             = "5.00"  # Max spot price (on-demand g5.12xlarge ~$5.20/h)
  wait_for_fulfillment   = true
  spot_type              = "one-time"

  root_block_device {
    volume_size = 200
    volume_type = "gp3"
  }

  user_data = base64encode(templatefile("${path.module}/gpu-bootstrap.sh", {
    vereda_version = "3.0.0"
    model_name     = var.model_name
  }))

  tags = {
    Name      = "vereda-gpu-cluster-spot"
    Project   = "syntexa"
    ManagedBy = "terraform"
  }
}

# On-demand fallback (se spot não estiver disponível)
resource "aws_instance" "gpu_cluster" {
  count                  = var.use_spot ? 0 : 1
  ami                    = data.aws_ami.ubuntu_gpu.id
  instance_type          = var.gpu_instance_type
  subnet_id              = aws_subnet.private_gpu.id
  vpc_security_group_ids = [aws_security_group.gpu_cluster.id]
  iam_instance_profile   = aws_iam_instance_profile.gpu_profile.name

  root_block_device {
    volume_size = 200
    volume_type = "gp3"
  }

  user_data = base64encode(templatefile("${path.module}/gpu-bootstrap.sh", {
    vereda_version = "3.0.0"
    model_name     = var.model_name
  }))

  tags = {
    Name      = "vereda-gpu-cluster"
    Project   = "syntexa"
    ManagedBy = "terraform"
  }
}

# ── BASTION / ORCHESTRATOR ───────────────────────────────
resource "aws_instance" "orchestrator" {
  ami                    = data.aws_ami.ubuntu_gpu.id
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.orchestrator.id]
  iam_instance_profile   = aws_iam_instance_profile.gpu_profile.name

  root_block_device {
    volume_size = 50
    volume_type = "gp3"
  }

  user_data = base64encode(templatefile("${path.module}/orchestrator-bootstrap.sh", {
    vereda_version = "3.0.0"
  }))

  tags = {
    Name      = "vereda-orchestrator"
    Project   = "syntexa"
    ManagedBy = "terraform"
  }
}

# ── LOAD BALANCER (privado) ──────────────────────────────
resource "aws_lb" "gpu_internal" {
  name               = "vereda-gpu-lb"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.gpu_cluster.id]
  subnets            = [aws_subnet.private_gpu.id, aws_subnet.private_orchestrator.id]

  tags = {
    Name    = "vereda-gpu-lb"
    Project = "syntexa"
  }
}

resource "aws_lb_target_group" "gpu_vllm" {
  name     = "vereda-gpu-vllm"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.vereda.id

  health_check {
    path                = "/health"
    interval            = 30
    timeout             = 10
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_target_group_attachment" "gpu_vllm" {
  target_group_arn = aws_lb_target_group.gpu_vllm.arn
  target_id        = var.use_spot ? aws_spot_instance_request.gpu_cluster[0].spot_instance_id : aws_instance.gpu_cluster[0].id
  port             = 8000
}

# ── OUTPUTS ──────────────────────────────────────────────
output "gpu_cluster_private_ip" {
  value       = var.use_spot ? aws_spot_instance_request.gpu_cluster[0].private_ip : aws_instance.gpu_cluster[0].private_ip
  description = "Private IP of GPU cluster (no public IP)"
}

output "gpu_cluster_type" {
  value       = var.use_spot ? "spot" : "on-demand"
  description = "Tipo de instância GPU (spot ou on-demand)"
}

output "estimated_hourly_cost" {
  value       = var.use_spot ? "~$1.50/h (spot g5.12xlarge)" : "~$5.20/h (on-demand)"
  description = "Custo estimado por hora da GPU"
}

output "estimated_monthly_cost_24_7" {
  value       = var.use_spot ? "~$1,080/mês (24/7 spot)" : "~$3,744/mês (24/7 on-demand)"
  description = "Custo estimado 24/7 — use auto-shutdown para economizar"
}

output "orchestrator_public_ip" {
  value       = aws_instance.orchestrator.public_ip
  description = "Public IP of orchestrator"
}

output "vpc_id" {
  value = aws_vpc.vereda.id
}

output "gpu_sg_id" {
  value = aws_security_group.gpu_cluster.id
}
