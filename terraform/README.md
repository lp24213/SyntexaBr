# Terraform — Provisionar VM Azure para ExLlama

Passos rápidos:

1. Instale Terraform >= 1.1.0 e autentique no Azure com `az login`.

2. Ajuste `variables.tf` ou passe variáveis na linha de comando. Você precisa fornecer `admin_public_key` com sua chave SSH pública.

Exemplo de execução:

```bash
cd terraform
terraform init
terraform apply -var "admin_public_key=$(cat ~/.ssh/id_rsa.pub)" -auto-approve
```

3. Após execução, pegue o IP público:

```bash
terraform output public_ip
```

4. Use o IP para preencher o `ansible/inventory.ini` ou use o script `scripts/generate_inventory_from_terraform.sh`.

Observações:
- O `vm_size` padrão é `Standard_NC6s_v3`. Ajuste conforme disponibilidade de GPU/region.
- Este Terraform cria apenas a VM e recursos de rede. A instalação de drivers NVIDIA, Docker e deployment do container é responsabilidade do Ansible playbook (existente em `ansible/playbook.yml`).
