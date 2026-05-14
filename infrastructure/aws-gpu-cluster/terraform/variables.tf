variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "gpu_instance_type" {
  description = "GPU instance type for inference"
  type        = string
  default     = "g5.xlarge"
  # Options: g5.xlarge (1x A10G, 4 vCPU, 16GB), g5.2xlarge (1x A10G, 8 vCPU, 32GB)
}

variable "model_name" {
  description = "Default model to load"
  type        = string
  default     = "microsoft/DialoGPT-medium"
}

variable "ssh_key_name" {
  description = "AWS EC2 key pair name"
  type        = string
  default     = "vereda-key"
}
