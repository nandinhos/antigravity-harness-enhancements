---
trigger: always_on
description: Diretrizes e guardrails globais de segurança para banco de dados, sistema de arquivos e Git.
---

# Diretrizes e Guardrails Restritivos de Segurança (Global)

Regras invioláveis para execução de código, banco de dados e sistema no Antigravity:

1. **Banco de Dados e Migrações**:
   - NUNCA executar `php artisan migrate:fresh`, `php artisan migrate:reset`, `php artisan db:wipe`, `DROP DATABASE`, `DROP SCHEMA`, `TRUNCATE TABLE` ou `DELETE FROM` sem `WHERE`.
   - Alterações de schema via migrações incrementais (`php artisan make:migration`) com `up()`/`down()` idempotentes; operações multi-tabela em `DB::transaction(...)`.
   - Em projetos Laravel Docker/Sail, executar Artisan/DB dentro dos containers (ou MCP Laravel Boost); nunca rodar schema/seeding em produção ou staging.
2. **Sistema de Arquivos e SO**:
   - NUNCA executar `rm -rf /`, `rm -rf ~`, `chmod 777 /`, `mkfs`, `dd` ou remover o diretório `.git` do projeto.
   - Restringir edições ao workspace; toda exclusão de arquivo não temporário exige justificativa explícita.
3. **Git e Versionamento**:
   - NUNCA executar `git push --force`/`-f` em `main`, `master` ou `production`.
   - Verificar `git status` antes de `git reset --hard` ou `git checkout -- .` para evitar perda de trabalho.
4. **Hook de Interceptação Automática**:
   - Comandos e ferramentas passam pelo dispatcher unificado `~/.gemini/config/hooks/hooks_dispatcher.py`; violações são rejeitadas antes da execução.
5. **Proteção de Segredos e Chat Masking Mandatório**:
   - PROIBIDO exibir chaves de API, bearer tokens, senhas ou credenciais completas no chat (mesmo lidas de `.env`/configs ou solicitadas pelo usuário).
   - Sempre mascarar preservando apenas prefixo/sufixo (ex.: `Bearer 8XhNLp****************************TDNpmm`, `sk-ant-********************1234`).
