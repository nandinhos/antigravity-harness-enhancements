
# 🛡️ Diretrizes do Agente - Antigravity Harness Enhancements

## 🎯 Objetivo Estrito do Projeto

Implementar a integração combinada e complementar de DUAS ferramentas existentes no harness do Antigravity (ambiente WSL):

1. **Graphify (`graphifyy`)**: Gerador de Grafo de Conhecimento Arquitetural via Tree-Sitter (AST). Usado para navegação e descoberta de código.
2. **Headroom (`headroom-ai`)**: Compressor Reversível de Conteúdo (CCR) via Proxy/MCP. Usado para encurtar logs pesados e saídas de terminal.

## 🚫 Regras Absolutas (Proibições)

1. **NÃO invente novos frameworks ou harnesses do zero.** O foco é integrar `graphifyy` e `headroom-ai`.
2. **NÃO tente criar algoritmos próprios de AST ou compressão.** Use as bibliotecas oficiais e existentes.
3. **Mantenha o foco em 4 etapas sequenciais:**
   - Etapa 1: Instalação das ferramentas no WSL.
   - Etapa 2: Criação da Skill do Graphify.
   - Etapa 3: Integração do Headroom MCP/Proxy.
   - Etapa 4: Versionamento Git e benchmarks.
