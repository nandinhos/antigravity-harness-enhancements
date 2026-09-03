
# 🛡️ Diretrizes do Agente - Antigravity Harness Enhancements

## 🎯 Objetivo

Manter o harness de otimização do Antigravity (agy) com duas camadas complementares:

1. **Graphify (`graphifyy`)** — conhecimento de código via grafo AST (Tree-Sitter, zero-LLM).
2. **context-mode** — higiene de contexto (sandbox de tool output, continuidade de sessão, think-in-code).

## 🚫 Regras Absolutas

1. **NÃO reintegre o Headroom** — o proxy CCR não atende Gemini/Antigravity (só Anthropic/OpenAI) e foi removido por não se encaixar na metodologia.
2. **NÃO adicione proxies de compressão** (Headroom/RTK) nem brevidade agressiva de prosa (caveman).
3. **NÃO invente frameworks próprios** de AST ou compressão — use `graphify` e `context-mode`.
4. **Mantenha o grafo atualizado**: rode `graphify update .` após edições de código.
