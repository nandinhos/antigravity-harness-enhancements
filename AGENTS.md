# 🛡️ Diretrizes do Agente - Antigravity Harness Enhancements

## 🎯 Objetivo

Manter e operar o harness de eficiência de tokens e engenharia orientada a evidências para o **Antigravity (agy)** através da Tríade de Eficiência Zero-LLM:

1. **Graphify (`graphifyy`)** — navegação arquitetural e relacional via grafo AST (Tree-Sitter, custo zero de LLM).
2. **context-mode** — higiene de contexto (sandbox de tool output, continuidade de sessão SQLite FTS5 e think-in-code).
3. **Telemetria & Compactação CLI** — auditoria determinística de tokens (`scripts/harness-telemetry-benchmark.py`) e compactação de terminal (RTK opcional para comandos verbosos de shell).

## 🚫 Regras Absolutas

1. **NÃO reintegre proxies HTTP de rede (Headroom/CCR)** — proxies que interceptam ou reescrevem o tráfego HTTP de LLM não atendem a arquitetura do Gemini/Antigravity e quebram a fidelidade do modelo.
2. **NÃO adicione brevidade agressiva de prosa (caveman)** — a concisão deve seguir o Ponytail Mode (densidade informacional executiva), nunca truncamento tosco de vocabulário.
3. **NÃO invente frameworks caseiros** de AST ou sandbox — utilize estritamente `graphify` e `context-mode`.
4. **Mantenha o grafo atualizado**: execute `graphify update .` após alterações de código para prevenir *graph drift*.
5. **Auditoria de Telemetria**: utilize `python3 scripts/harness-telemetry-benchmark.py` para mensurar a redução real de tokens e latência sempre que evoluir o harness.
