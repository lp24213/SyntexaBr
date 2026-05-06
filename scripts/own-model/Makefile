# Alvos úteis (GNU Make). Raiz do repo: make -C scripts/own-model <alvo>
PYTHON ?= python
REPO_ROOT := $(abspath $(CURDIR)/../..)

.PHONY: lint-registry validate-manifests attestation-roundtrip local-dump probe-chat

lint-registry:
	cd $(REPO_ROOT) && $(PYTHON) scripts/own-model/lint_model_registry.py

validate-manifests:
	cd $(REPO_ROOT) && $(PYTHON) scripts/own-model/validate_all_manifests_glob.py

attestation-roundtrip:
	cd $(REPO_ROOT) && PYTHONPATH=$(REPO_ROOT) $(PYTHON) -c "from vereda_ai.syntexa_core.promotion_attestation import build_llm_promotion_attestation, verify_attestation_document; d,_=build_llm_promotion_attestation(promotion_type='make', previous_active=None, candidate_model='a', active_after='a', readiness_report={'ready':True,'active_model':'a','checks':[]}, policy_snapshot={'policy_version':'m','policy_sha256':'x','policy_profile':'production'}, admin_user_id=None); assert verify_attestation_document(d)[0]; print('ok')"

local-dump:
	cd $(REPO_ROOT) && PYTHONPATH=$(REPO_ROOT) $(PYTHON) scripts/own-model/dump_local_llm_state.py

probe-chat:
	cd $(REPO_ROOT) && $(PYTHON) scripts/own-model/minimal_chat_probe.py --base-url http://127.0.0.1:8000
