# 🛡️ Guia Oficial do Harness de Otimização: Antigravity IDE
### **Graphify (Navegação Relacional AST) + Headroom (Compressão CCR de Contexto)**

---

## 📐 1. Visão Geral e Arquitetura

O **Harness Antigravity Enhancements** é um sistema de otimização de contexto e economia de tokens projetado para o **Antigravity IDE** no ambiente WSL. Ele combina duas ferramentas complementares de ponta:

1. **Graphify (`graphifyy`)**: Analisa a estrutura do código-fonte utilizando parsers AST determinísticos via **Tree-Sitter**. Em vez de fazer buscas cegas por arquivo ou rodar múltiplos comandos `grep`/`find` custosos, a IA consulta um grafo relacional (`graph.json`) com custo zero de tokens de LLM.
2. **Headroom (`headroom-ai`)**: Atua como um proxy e servidor MCP intermediário que intercepta e aplica **Compressão Reversível de Conteúdo (CCR - Compress-Cache-Retrieve)**. Saídas longas de terminal, logs de testes e retornos extensos de ferramentas são reduzidos em até **90%** antes de serem enviados à janela de contexto da IA.

```
┌────────────────────────────────────────────────────────────────────────┐
│                             ANTIGRAVITY IDE                            │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
      (1) Consultas Arquiteturais           (2) Execuções de Terminal / Logs
                    │                                │
                    ▼                                ▼
       ┌────────────────────────┐       ┌────────────────────────┐
       │   Graphify (AST Graph) │       │ Headroom Proxy / MCP   │
       │   - zero cost parsing  │       │ - 90% token reduction  │
       │   - graphify-out/      │       │ - CCR compression      │
       └────────────────────────┘       └────────────────────────┘
```

---

## ⚡ 2. Pré-requisitos do Ambiente WSL

Certifique-se de que seu ambiente WSL possui as dependências base instaladas:

* **Python**: `3.10` ou superior (recomendado: 3.12+)
* **Git**: `2.40` ou superior
* **uv** (gerenciador rápido de ferramentas Python):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

---

## 📦 3. Instalação Global no WSL

Execute os seguintes comandos no terminal do WSL uma única vez para instalar as CLIs globalmente:

### 3.1 Instalar Graphify e Headroom
```bash
# Instala o Graphify (fornece 'graphify' e 'graphify-mcp')
uv tool install graphifyy

# Instala o Headroom com suporte completo (fornece 'headroom')
uv tool install "headroom-ai[all]"
```

### 3.2 Verificar Versões Instaladas
```bash
graphify --version
headroom --version
```

### 3.3 Inicializar e Registrar o Headroom MCP / Proxy
```bash
# Registrar o servidor MCP do Headroom nas ferramentas de agente
headroom mcp install

# Verificar o status de saúde do proxy e integrações
headroom doctor
```

> **Nota:** O serviço de Proxy do Headroom rodará automaticamente em segundo plano na porta `http://127.0.0.1:8787`.

---

## 🚀 4. Guia de Ativação por Projeto

Para ativar o Harness em qualquer repositório de projeto (ex: Laravel, Node.js, Python, Go, etc.), siga estes **4 passos simples** no terminal da pasta do projeto:

### **Passo 1: Gerar a análise AST inicial do projeto**
```bash
graphify extract . --code-only
graphify cluster-only .
```
* **O que faz:** Mapeia todos os arquivos de código via Tree-Sitter local, cria as comunidades de código e gera o relatório `graphify-out/GRAPH_REPORT.md` e o visualizador `graphify-out/graph.html`.

### **Passo 2: Instalar Regras e Workflows no Antigravity**
```bash
graphify antigravity install
```
* **O que faz:** Cria a pasta `.agents/` no repositório contendo `.agents/rules/graphify.md` e `.agents/workflows/graphify.md`. Isso instrui o assistente do Antigravity a usar o grafo automaticamente.

### **Passo 3: Ativar Atualização Automática via Git Hook**
```bash
graphify hook install
```
* **O que faz:** Instala um hook `post-commit` / `post-checkout` leve no Git. Sempre que você ou a IA fizerem um commit ou trocarem de branch, o grafo de código será atualizado incrementalmente em frações de segundo.

### **Passo 4: (Opcional) Registrar o `.mcp.json` Local no Repositório**
Crie um arquivo `.mcp.json` na raiz do projeto para permitir chamadas MCP diretas:
```json
{
  "mcpServers": {
    "graphify": {
      "command": "graphify-mcp",
      "args": ["${workspace.path}/graphify-out/graph.json"]
    },
    "headroom": {
      "command": "headroom",
      "args": ["mcp", "serve", "--proxy-url", "http://127.0.0.1:8787"]
    }
  }
}
```

---

## 🔄 5. Funcionamento e Workflow no Dia a Dia

Depois de instalado no projeto, **o uso é 100% transparente**:

### 1. **Perguntas sobre o Código e Arquitetura**
* Quando você digita no chat do Antigravity: *"Como funciona a autenticação?"* ou *"Qual classe chama a classe X?"*:
* A IA lê a regra `.agents/rules/graphify.md` e executa a busca direto no `graph.json` via AST.
* **Economia:** Nenhuma leitura cega de dezenas de arquivos brutos. A resposta vem direta e precisa.

### 2. **Execução de Testes e Comandos Longos**
* Quando a IA executa suítes de testes, comandos de terminal ou lê logs pesados:
* O **Headroom Proxy** intercepta o texto e o comprime com marcadores CCR reversíveis.
* **Economia:** Economiza até 90% dos tokens da resposta do terminal. Se a IA precisar ler um detalhe específico sem compressão, ela usa a ferramenta `headroom_retrieve` automaticamente.

### 3. **Manutenção e Atualização do Código**
* Conforme código é adicionado ou alterado:
* **Com Commit:** O Git Hook (`graphify hook install`) atualiza o grafo automaticamente.
* **Sem Commit (durante o trabalho):** Você ou a IA podem rodar a qualquer momento:
  ```bash
  graphify update .
  ```
  *(Analisa apenas os arquivos modificados de forma incremental em < 2s).*

---

## 📊 6. Comandos Úteis e Métricas

### Consultar Métricas de Economia do Headroom
```bash
headroom savings
```

### Verificar Saúde do Proxy Headroom
```bash
headroom doctor
```

### Fazer Consultas Rápidas ao Grafo no Terminal
```bash
# Fazer uma pergunta sobre o código diretamente no CLI do Graphify
graphify query "Onde estão os controllers?"

# Encontrar o menor caminho/relação entre duas classes
graphify path "UserController" "AuthRepository"

# Explicar um conceito ou módulo
graphify explain "PaymentGateway"
```

---

## ✅ Resumo do Workflow

| Componente | Função | Instalação no Projeto | Execução no Dia a Dia |
| :--- | :--- | :--- | :--- |
| **Graphify** | Navegação Relacional AST | `graphify extract . --code-only`<br>`graphify antigravity install`<br>`graphify hook install` | **Invisível**: A IA lê a regra `.agents/rules/graphify.md` e consulta o grafo `graph.json`. |
| **Headroom** | Compressão de Logs (CCR) | `uv tool install "headroom-ai[all]"`<br>`headroom mcp install` | **Transparente**: Intercepta comandos de terminal e reduz logs em até 90%. |

---
*Documentação gerada para o Antigravity IDE (WSL).*
