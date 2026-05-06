**Guia rápido — Deploy produção (ExLlama na Azure + Backend Hetzner)**

- Pré-requisitos locais:
  - `az` CLI autenticado (`az login`)
  - `ansible` instalado e collections `community.docker`
  - Chave SSH com acesso às VMs

1) Criar VM na Azure (pode usar `scripts/deploy_llm_azure.sh` ou portal).

2) Após obter IP público da VM, edite `ansible/inventory.ini.example` copiando para `ansible/inventory.ini` e preenchendo:

   - seção `[exllama]` com IP da Azure
   - seção `[hetzner]` com IP do Hetzner

3) Ajuste `llm-server/docker-compose.exllama.yml` se precisar trocar imagem do servidor ExLlama.

4) Execute o playbook Ansible (substitua `inventory.ini` conforme usado):

```bash
cd syntexabr/ansible
ansible-playbook -i inventory.ini playbook.yml --ask-become-pass
```

5) Verifique health no Hetzner:

```bash
ssh -i /path/to/key root@HETZNER_IP 'curl -sf http://127.0.0.1:8000/health | jq'
```

Observações:
- Este fluxo NÃO roda nada no seu computador local além de rodar os scripts/ansible; todo processamento LLM fica na VM Azure.
- Se preferir automação total (Terraform + Ansible), eu posso gerar os manifests Terraform para criar VM e rede.
- Siga o checklist de produção: firewall, monitoramento, backups de modelos, e alertas (Prometheus/Alertmanager ou Azure Monitor).
