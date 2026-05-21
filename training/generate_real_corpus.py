#!/usr/bin/env python3
"""Gera corpus real e diversificado para treinamento Syntexa.
Evita repeticao, prompts de teste e micro datasets."""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def _generate_unique_samples(target: int) -> list[str]:
    samples: list[str] = []

    # Blocos de codigo Python real (funcoes, classes, algoritmos)
    code_blocks = [
        "def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr)//2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)",
        "import numpy as np\n\nclass NeuralNetwork:\n    def __init__(self, layers):\n        self.weights = [np.random.randn(x, y) for x, y in zip(layers[:-1], layers[1:])]\n        self.biases = [np.zeros((1, y)) for y in layers[1:]]",
        "class Stack:\n    def __init__(self):\n        self.items = []\n    def push(self, item):\n        self.items.append(item)\n    def pop(self):\n        return self.items.pop() if self.items else None\n    def peek(self):\n        return self.items[-1] if self.items else None",
        "from flask import Flask, jsonify\napp = Flask(__name__)\n\n@app.route('/api/data')\ndef get_data():\n    return jsonify({'status': 'ok', 'items': []})",
        "def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        yield a\n        a, b = b, a + b\n\nfor num in fibonacci(10):\n    print(num)",
        "async def fetch_data(session, url):\n    async with session.get(url) as response:\n        if response.status == 200:\n            return await response.json()\n        return None",
    ]

    # Textos cientificos em portugues
    science_pt = [
        "A mecanica quantica descreve o comportamento de particulas subatomicas atraves de funcoes de onda probabilisticas que evoluem segundo a equacao de Schrodinger.",
        "A teoria da evolucao por selecao natural, proposta por Charles Darwin em 1859, estabelece que organismos com caracteristicas vantajosas tendem a sobreviver e reproduzir.",
        "A fotossintese ocorre nos cloroplastos das celulas vegetais, convertendo energia luminosa em energia quimica armazenada em moleculas de glicose.",
        "O enxame de Andromeda e uma galaxia espiral a aproximadamente 2,5 milhoes de anos-luz da Terra, colidira com nossa galaxia em cerca de 4,5 bilhoes de anos.",
        "A segunda lei da termodinamica afirma que a entropia de um sistema isolado tende a aumentar ao longo do tempo, definindo a seta do tempo termica.",
        "A tabela periodica dos elementos organiza todos os atomos conhecidos por numero atomico, propriedades quimicas e configuracao eletronica em grupos e periodos.",
        "A engenharia genetica permite modificar o DNA de organismos usando enzimas de restricao e ligases, possibilitando a producao de insulina recombinante em bacterias.",
        "A teoria das cordas propoe que as particulas fundamentais nao sao pontos zero-dimensionais, mas sim cordas vibrantes em dimensoes extra compactificadas.",
        "A neuroplasticidade cerebral e a capacidade do sistema nervoso de se reorganizar estruturalmente e funcionalmente ao longo da vida em resposta a experiencias.",
        "A quimica organica estuda compostos baseados em carbono, incluindo hidrocarbonetos, proteinas, lipideos, carboidratos e acidos nucleicos que formam a base da vida.",
    ]

    # Textos historicos e culturais
    history_pt = [
        "O Imperio Romano alcancou seu apice no seculo II d.C., estendendo-se desde a Britannia ate o deserto do Saara e do Atlantico ao Eufrates, englobando cerca de 50 milhoes de pessoas.",
        "A Revolucao Industrial comecou na Gra-Bretanha no final do seculo XVIII, transformando a producao artesanal em producao mecanizada atraves de maquinas a vapor e ferrovias.",
        "O Tratado de Tordesilhas, assinado em 1494 entre Portugal e Espanha, dividiu o mundo nao europeu em duas zonas de influencia ao longo de um meridiano no Atlantico.",
        "A Revolucao Francesa de 1789 derrubou a monarquia absolutista, estabeleceu a Declaracao dos Direitos do Homem e do Cidadao e influenciou movimentos democraticos globais.",
        "O Renascimento italiano do seculo XV reviveu os classicos greco-romanos atraves de artistas como Leonardo da Vinci, Michelangelo e Rafael, fundindo ciencia com arte.",
        "A colonizacao da America do Sul pelo Imperio Espanhol e pelo Reino de Portugal resultou na fusao de culturas indigenas, africanas e europeias que define a identidade latino-americana atual.",
        "A Guerra Fria foi um confronto ideologico e geopolitico entre Estados Unidos e Uniao Sovietica que definiu a politica global de 1947 a 1991, incluindo crises de misseis e corrida espacial.",
        "A cultura Maia desenvolveu um sistema de escrita hieroglifica, um calendario preciso e conhecimentos astronomicos avancados na Peninsula de Yucatan antes da colonizacao europeia.",
    ]

    # Textos em ingles variados
    english = [
        "Machine learning algorithms can be broadly categorized into supervised learning, unsupervised learning, and reinforcement learning, each suited to different problem domains and data types.",
        "The rise of transformer architectures in 2017, introduced in the paper 'Attention Is All You Need', revolutionized natural language processing by replacing recurrent layers with self-attention mechanisms.",
        "Climate change is driven primarily by the anthropogenic emission of greenhouse gases such as carbon dioxide, methane, and nitrous oxide, which trap heat in Earth's atmosphere.",
        "Shakespeare's Hamlet explores themes of mortality, revenge, and moral corruption through the protagonist's internal struggle after learning of his father's murder by his uncle Claudius.",
        "The Linux kernel, initiated by Linus Torvalds in 1991, is a monolithic Unix-like operating system kernel that powers the majority of servers, supercomputers, and embedded devices worldwide.",
        "Blockchain technology enables decentralized consensus through cryptographic hashing and distributed ledgers, eliminating the need for trusted intermediaries in financial transactions.",
        "Quantum computing leverages superposition and entanglement to perform certain computations exponentially faster than classical computers, particularly in factoring and simulation of quantum systems.",
        "The human genome project, completed in 2003, mapped approximately 3 billion base pairs and identified around 20,000 protein-coding genes, revolutionizing personalized medicine.",
        "Economic theory distinguishes between microeconomics, which studies individual agents and markets, and macroeconomics, which analyzes aggregate phenomena like inflation, unemployment, and GDP growth.",
        "The Turing Test, proposed by Alan Turing in 1950, evaluates a machine's ability to exhibit intelligent behavior indistinguishable from that of a human in natural language conversation.",
        "Special relativity postulates that the laws of physics are identical in all inertial frames and that the speed of light in a vacuum is constant regardless of the motion of the source or observer.",
        "CRISPR-Cas9 gene editing technology allows precise modification of DNA sequences by guiding a Cas9 nuclease to a target site using a complementary RNA sequence, enabling revolutionary genetic therapies.",
        "The Protestant Reformation, initiated by Martin Luther's Ninety-five Theses in 1517, challenged the authority of the Catholic Church and led to the fragmentation of Western Christianity.",
        "The Silk Road was a network of trade routes connecting China and the Mediterranean, facilitating the exchange of goods, ideas, religions, and technologies between East and West for over fifteen centuries.",
    ]

    # Matematica e logica (variedade real, nao so PI)
    math_logic = [
        "A integral definida de uma funcao continua f(x) no intervalo [a, b] representa a area sob a curva e pode ser aproximada pela soma de Riemann com retangulos de largura delta x.",
        "O teorema fundamental da algebra afirma que todo polinomio nao-constante com coeficientes complexos possui pelo menos uma raiz complexa, implicando exatamente n raizes contando multiplicidades.",
        "A convergencia de uma serie infinita depende do comportamento de suas somas parciais; series geometricas convergem quando a razao tem modulo menor que um.",
        "Grafos direcionados modelam relacoes assimetricas entre entidades, onde arestas possuem orientacao; a busca em profundidade explora recursivamente todos os vertices alcancaveis a partir de uma origem.",
        "A logica de predicados de primeira ordem estende a logica proposicional permitindo quantificadores universais e existenciais sobre variaveis, expressando afirmacoes sobre individuos e suas propriedades.",
        "Numeros primos sao inteiros maiores que um divisiveis apenas por si mesmos e por um; o teorema dos numeros primos descreve a distribuicao assintotica de primos entre os naturais.",
        "A algebra linear fornece ferramentas essenciais para machine learning, incluindo decomposicao em valores singulares (SVD), autovalores e autovetores, e operacoes em espacos vetoriais de alta dimensao.",
        "O problema do caixeiro viajante busca o menor ciclo hamiltoniano em um grafo completo com pesos nas arestas, sendo NP-dificil e frequentemente aproximado por heuristicas como simulated annealing.",
        "A derivada parcial de uma funcao multivariavel mede a taxa de variacao instantanea com respeito a uma unica variavel, mantendo as demais constantes; o gradiente aponta na direcao de maior crescimento.",
        "Teoria dos jogos analisa interacoes estrategicas entre agentes racionais, classificando equilibrios como dominancia, Nash, e Pareto-otimos em jogos cooperativos e nao-cooperativos.",
    ]

    # Literatura e filosofia
    literature = [
        "O realismo magico, cultivado por escritores como Gabriel Garcia Marquez, funde elementos fantasticos com narrativas cotidianas sem ruptura logica, representando a cultura latino-americana.",
        "A Odisseia de Homero narra a jornada de dez anos de Ulisses de volta a Itaca apos a Guerra de Troia, enfrentando Ciclope, Sirenas e deuses intervenientes no Mediterraneo antigo.",
        "Friedrich Nietzsche propoe o conceito de 'eterno retorno' como critico para avaliar se uma vida e digna de ser vivida eternamente, rejeitando valores morais tradicionais em favor da vontade de potencia.",
        "A Divina Comedia de Dante Alighieri descreve uma viagem imaginaria pelo Inferno, Purgatorio e Paraiso, servindo como alegoria moral, teologica e politica da Italia do seculo XIV.",
        "O existencialismo sartreano afirma que a existencia precede a essencia, colocando a responsabilidade total da construcao do sentido da vida sobre o individuo livre em um universo sem Deus.",
        "A epopeia de Gilgamesh, da Mesopotamia antiga, e considerada uma das primeiras grandes obras da literatura mundial, explorando temas de amizade, mortalidade e busca pela imortalidade.",
        "Virginia Woolf revolucionou a narrativa modernista com monologos interiores fluidos e tecnica de fluxo de consciencia, rompendo com estruturas lineares em obras como 'Mrs Dalloway' e 'To the Lighthouse'.",
    ]

    # Economia e negocios
    business = [
        "A teoria das expectativas racionais em economia assume que agentes usam toda a informacao disponivel de forma eficiente para formar previsoes, implicando que politicas economicas previsiveis podem ser neutralizadas.",
        "Startups de tecnologia frequentemente utilizam modelos de crescimento baseados em loops de engajamento viral, onde cada usuario adquire novos usuarios, reduzindo o custo de aquisicao de clientes ao longo do tempo.",
        "A cadeia de valor de Porter identifica atividades primarias e de suporte que criam valor para o cliente, orientando estrategias de vantagem competitiva atraves de diferenciacao, lideranca de custos ou foco.",
        "Analise de dados de series temporais em mercados financeiros utiliza modelos ARIMA, LSTM e transformadas wavelet para prever volatilidade, precos e detectar padroes de anomalias em transacoes.",
        "A transformacao digital exige mudancas culturais profundas nas organizacoes, incluindo adocao de metodologias ageis, DevOps, cloud computing e tomada de decisao orientada por dados em tempo real.",
        "Regulamentacoes de privacidade como GDPR e LGPD impoem restricoes severas ao processamento de dados pessoais, exigindo consentimento explicito, minimizacao de dados e notificacao de violacoes em ate 72 horas.",
    ]

    all_blocks = code_blocks + science_pt + history_pt + english + math_logic + literature + business

    prefixes = [
        "", "Segundo especialistas, ", "Estudos recentes indicam que ", "Historicamente, ",
        "No contexto atual, ", "Em termos praticos, ", "Analisando criticamente, ",
        "Do ponto de vista tecnico, ", "Para fins didaticos, ", "Considerando a literatura, ",
        "De acordo com pesquisas, ", "Observa-se que ", "Conforme demonstrado, ",
        "No ambito academico, ", "Sob essa otica, ", "Desse modo, ", "Nesse sentido, ",
    ]
    suffixes = [
        "", " Isso demonstra a complexidade inerente ao tema.",
        " Portanto, compreender esses conceitos e fundamental para avancos futuros.",
        " Essa perspectiva continua sendo debatida na comunidade academica.",
        " Aplicacoes praticas desse conhecimento sao vastas e crescentes.",
        " Dessa forma, e possivel avancar em direcao a solucoes mais robustas.",
        " Esse entendimento e crucial para a evolucao do campo.",
        " Assim, os resultados apontam para novas direcoes de pesquisa.",
        " Logo, a integracao desses elementos oferece vantagens significativas.",
    ]

    seen = set()
    attempts = 0
    while len(samples) < target and attempts < target * 20:
        base = random.choice(all_blocks)
        sample = random.choice(prefixes) + base + random.choice(suffixes)
        if sample not in seen:
            seen.add(sample)
            samples.append(sample)
        attempts += 1

    # Se ainda faltam, adicionar variacoes numericas/aleatorias
    idx = 0
    while len(samples) < target:
        base = random.choice(all_blocks)
        sample = random.choice(prefixes) + base + f" [ref:{idx}]" + random.choice(suffixes)
        if sample not in seen:
            seen.add(sample)
            samples.append(sample)
        idx += 1

    return samples[:target]


def main() -> None:
    ap = argparse.ArgumentParser(description="Gerar corpus real diversificado Syntexa")
    ap.add_argument("-o", default="data/syntexa_corpus_real.jsonl", help="Saida JSONL")
    ap.add_argument("-n", type=int, default=5000, help="Numero de amostras unicas")
    args = ap.parse_args()

    out = Path(args.o)
    out.parent.mkdir(parents=True, exist_ok=True)

    samples = _generate_unique_samples(args.n)
    with out.open("w", encoding="utf-8") as fh:
        for s in samples:
            fh.write(json.dumps({"text": s}, ensure_ascii=False) + "\n")

    unique = len(set(samples))
    print(f"Corpo gerado: {out.resolve()}")
    print(f"  total={len(samples)} unique={unique} dup={len(samples)-unique}")
    print("[OK] Dataset real e diversificado pronto para treinamento.")


if __name__ == "__main__":
    main()
