<#
PowerShell helper para instruções rápidas de provisionamento Azure
Uso: abra PowerShell e execute os comandos abaixo passo-a-passo.
#>

Write-Host "1) Faça login no Azure"
Write-Host "az login"

Write-Host "2) Exporte a chave pública (substitua o caminho se necessário)"
Write-Host "$env:ADMIN_PUBKEY = Get-Content $env:USERPROFILE\.ssh\id_rsa.pub"

Write-Host "3) Execute Terraform (no diretório terraform):"
Write-Host "cd terraform"
Write-Host "terraform init"
Write-Host "terraform apply -var \"admin_public_key=$env:ADMIN_PUBKEY\""

Write-Host "Após o apply, execute o script de orquestração bash ou gere o inventory para Ansible."
