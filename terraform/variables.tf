variable "resource_group_name" {
  type    = string
  default = "syntexa-rg"
}

variable "location" {
  type    = string
  default = "eastus"
}

variable "vm_name" {
  type    = string
  default = "exllama-vm"
}

# GPU / inferência local: NC/ND (6 VCPU + V100) ou maior conforme carga. API-only (sem GPU nesta VM):
# p.ex. Standard_D32s_v5 / Standard_D48s_v5. Para 10k+ ligações simultâneas: múltiplas VMs + Load Balancer + DB gerido + Redis, não 1 vCPU
variable "vm_size" {
  type    = string
  default = "Standard_NC6s_v3" # Ajuste conforme disponibilidade e custo; API tier pode usar SKU D* separado
}

variable "admin_username" {
  type    = string
  default = "azureuser"
}

variable "admin_public_key" {
  description = "Chave SSH pública para acesso ao VM (ex: cat ~/.ssh/id_rsa.pub)"
  type        = string
}
