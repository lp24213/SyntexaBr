#!/usr/bin/env python3
"""Gera corpus massivo em portugues para treino Syntexa."""
import json
import random
import sys
from pathlib import Path

# Templates de frases variadas
TEMPLATES = {
    "saudacao": [
        "Oi, tudo bem?",
        "Ola! Como posso ajudar?",
        "Bom dia! Em que posso ser util?",
        "E ai, beleza?",
        "Oi! Sou a Syntexa, sua assistente.",
        "Boa tarde! Como vai?",
    ],
    "pergunta_simples": [
        "Qual a capital do Brasil?",
        "Quanto e 2 mais 2?",
        "O que e Python?",
        "Como funciona a internet?",
        "Quem foi Albert Einstein?",
        "O que e machine learning?",
        "Como se calcula a area de um circulo?",
        "O que e DNA?",
    ],
    "resposta_simples": [
        "A capital do Brasil e Brasilia.",
        "2 mais 2 e igual a 4.",
        "Python e uma linguagem de programacao popular.",
        "A internet funciona atraves de protocolos como TCP/IP.",
        "Albert Einstein foi um fisico alemao famoso pela teoria da relatividade.",
        "Machine learning e uma area da inteligencia artificial.",
        "A area de um circulo e pi vezes o raio ao quadrado.",
        "DNA e o acido desoxirribonucleico, material genetico.",
    ],
    "conversa": [
        "Usuario: Oi, qual e o clima hoje?\nAssistente: Nao tenho acesso ao clima em tempo real, mas posso ajudar com outras coisas!",
        "Usuario: Me explique o que e um algoritmo\nAssistente: Um algoritmo e uma sequencia de passos para resolver um problema.",
        "Usuario: Como faco uma omelete?\nAssistente: Bata ovos, tempere, despeje na frigideira e cozinhe ate firmar.",
        "Usuario: Qual a formula da agua?\nAssistente: A formula da agua e H2O, dois atomos de hidrogenio e um de oxigenio.",
        "Usuario: Me conte uma curiosidade\nAssistente: O polvo tem tres coracoes e sangue azul!",
    ],
    "codigo": [
        "def hello_world():\n    print('Ola, mundo!')",
        "for i in range(10):\n    print(i)",
        "if x > 5:\n    return True\nelse:\n    return False",
        "import numpy as np\narr = np.array([1, 2, 3])",
        "class Pessoa:\n    def __init__(self, nome):\n        self.nome = nome",
        "lista = [1, 2, 3, 4, 5]\nprint(len(lista))",
    ],
    "ciencia": [
        "A fotossintese e o processo pelo qual plantas convertem luz solar em energia quimica.",
        "A gravidade e uma forca que atrai corpos com massa um para o outro.",
        "O atomo e composto por protons, neutrons e eletrons.",
        "A evolucao das especies foi proposta por Charles Darwin.",
        "A Terra tem aproximadamente 4,5 bilhoes de anos.",
        "A velocidade da luz no vacuo e cerca de 300 mil quilometros por segundo.",
        "O sistema solar tem oito planetas orbitando o Sol.",
        "A agua ferve a 100 graus Celsius ao nivel do mar.",
    ],
    "historia": [
        "O Brasil foi descoberto por Pedro Alvares Cabral em 1500.",
        "A independencia do Brasil foi proclamada em 7 de setembro de 1822.",
        "A Proclamacao da Republica ocorreu em 15 de novembro de 1889.",
        "A escravidao foi abolida no Brasil em 1888.",
        "A Segunda Guerra Mundial terminou em 1945.",
        "A Revolucao Francesa comecou em 1789.",
    ],
    "tecnologia": [
        "Inteligencia artificial e a capacidade de maquinas realizarem tarefas que exigiriam inteligencia humana.",
        "Redes neurais artificiais sao inspiradas no funcionamento do cerebro humano.",
        "O blockchain e uma tecnologia de registro distribuido e imutavel.",
        "A computacao quantica utiliza qubits para processar informacoes.",
        "A nuvem permite armazenar e acessar dados pela internet.",
        "5G e a quinta geracao de redes moveis, mais rapida e com menor latencia.",
    ],
    "geografia": [
        "O Brasil e o maior pais da America do Sul.",
        "O rio Amazonas e o maior rio do mundo em volume de agua.",
        "A cordilheira dos Andes e a maior cadeia de montanhas do mundo.",
        "O deserto do Saara e o maior deserto quente do mundo.",
        "O Oceano Pacifico e o maior oceano da Terra.",
        "A Russia e o maior pais do mundo em area territorial.",
    ],
    "matematica": [
        "O numero pi e aproximadamente 3,14159.",
        "Um triangulo equilatero tem tres lados iguais.",
        "O teorema de Pitagoras afirma que a^2 + b^2 = c^2 em um triangulo retangulo.",
        "O numero de ouro e aproximadamente 1,618.",
        "Zero e um numero par.",
        "A soma dos angulos internos de um triangulo e 180 graus.",
    ],
    "saude": [
        "Beber agua e essencial para a saude do organismo.",
        "A pratica regular de exercicios fisicos melhora a qualidade de vida.",
        "O sono adequado e fundamental para a recuperacao do corpo.",
        "Uma alimentacao balanceada inclui frutas, verduras e proteinas.",
        "A vacinacao e importante para prevenir doencas.",
        "O estresse cronico pode causar problemas de saude.",
    ],
    "economia": [
        "Inflacao e o aumento generalizado de precos na economia.",
        "O PIB mede a producao total de bens e servicos de um pais.",
        "Juros sao o custo do dinheiro emprestado.",
        "O mercado de acoes e onde se negociam partes de empresas.",
        "Desemprego e a taxa de pessoas sem trabalho.",
        "Exportacoes sao vendas de produtos para outros paises.",
    ],
    "portugues": [
        "O sujeito e o termo da oracao que realiza ou sofre a acao.",
        "O predicado e tudo que se declara sobre o sujeito.",
        "Substantivo e a classe de palavra que nomeia seres.",
        "Verbo e a classe que expressa acao, estado ou fenomeno.",
        "Adjetivo qualifica ou caracteriza o substantivo.",
        "A concordancia verbal exige que o verbo combine com o sujeito.",
    ],
    "filosofia": [
        "Socrates foi um filosofo grego que desenvolveu o metodo maietico.",
        "Platao foi discipulo de Socrates e fundou a Academia.",
        "Aristoteles foi discipulo de Platao e criou a logica formal.",
        "Descartes afirmou: Penso, logo existo.",
        "Nietzsche propos o conceito do super-homem.",
        "Kant desenvolveu a filosofia critica.",
    ],
}

def generate_sample():
    category = random.choice(list(TEMPLATES.keys()))
    template = random.choice(TEMPLATES[category])
    return template

def main():
    output_file = Path("data/syntexa_corpus_real.jsonl")
    target_size = 200_000  # 200K amostras
    
    # Abre arquivo existente e conta
    existing = []
    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as f:
            existing = [json.loads(line) for line in f if line.strip()]
    
    current_size = len(existing)
    to_generate = max(0, target_size - current_size)
    
    print(f"[CORPUS] Existente: {current_size}, Gerar: {to_generate}, Alvo: {target_size}")
    
    with open(output_file, "a", encoding="utf-8") as f:
        for i in range(to_generate):
            text = generate_sample()
            # Variacao: as vezes adiciona contexto ou pergunta/resp
            if random.random() < 0.3:
                text = text + " " + generate_sample()
            json.dump({"text": text}, f, ensure_ascii=False)
            f.write("\n")
            if (i + 1) % 10_000 == 0:
                print(f"[CORPUS] Gerados: {i + 1}/{to_generate}")
    
    # Verifica total
    with open(output_file, "r", encoding="utf-8") as f:
        total = sum(1 for _ in f if _.strip())
    
    print(f"[CORPUS] Total final: {total} amostras")
    print(f"[CORPUS] Estimativa tokens: ~{total * 20} tokens")

if __name__ == "__main__":
    main()
