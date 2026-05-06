Deploy orquestrado (resumo rápido)

1) Certifique-se de ter `az` e `terraform` instalados e autenticados (`az login`).
2) Ajuste `terraform/variables.tf` se quiser trocar região, nome da vm ou tamanho.
3) Execute `bash scripts/run_full_deploy.sh` e siga instruções.
4) Se preferir Windows, siga `scripts/azure_provision_instructions.ps1` e depois rode Ansible.

Observação: Este repositório fornece a orquestração; a execução final requer suas credenciais.
