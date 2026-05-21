variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "gpu_instance_type" {
  description = "GPU instance type for inference"
  type        = string
  default     = "g5.12xlarge"
  # g5.xlarge  = 1x A10G 24GB, 4 vCPU  (só serve modelos <=7B 4-bit)
  # g5.2xlarge = 1x A10G 24GB, 8 vCPU
  # g5.12xlarge = 4x A10G 96GB total, 48 vCPU (roda 13B-32B 4-bit confortável)
  # g5.48xlarge = 8x A10G 192GB total (escala enterprise)
  # p4d.24xlarge = 8x A100 40GB (treinamento, caro)
}

variable "use_spot" {
  description = "Usar spot instances para economizar ~70%"
  type        = bool
  default     = true
}

variable "model_name" {
  description = "Modelo para vLLM/Ollama inference"
  type        = string
  default     = "Qwen/Qwen2.5-14B-Instruct"
  # Alternativas viáveis com $100/mês:
  # - "meta-llama/Llama-3.1-8B-Instruct" (8B, cabe em g5.xlarge)
  # - "Qwen/Qwen2.5-14B-Instruct" (14B, precisa g5.12xlarge)
  # - "microsoft/Phi-4" (14B, excelente qualidade)
  # - "mistralai/Mistral-7B-Instruct-v0.3" (7B, rápido)
}

variable "budget_limit_usd" {
  description = "Limite de orçamento mensal AWS em USD"
  type        = number
  default     = 100
}

variable "ssh_key_name" {
  description = "AWS EC2 key pair name"
  type        = string
  default     = "vereda-key"
}
