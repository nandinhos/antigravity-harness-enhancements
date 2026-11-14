---
trigger: always_on
description: Resolução canônica de symlinks (/var -> /private/var) e hermeticidade de Git em testes multi-plataforma (macOS vs Linux).
---

# Regra: Resolução de Symlinks em Testes Multi-Plataforma (macOS vs Linux)

Ao escrever testes automatizados em Python ou scripts que manipulem caminhos no sistema de arquivos:

1. **Invariante de macOS (`/var` -> `/private/var`):**
   - No macOS, `/tmp` e `/var` são symlinks para `/private/tmp` e `/private/var`.
   - Comandos como `git rev-parse --show-toplevel` e `pwd -P` sempre resolvem para o caminho canônico `/private/...`.
   - O Python `tempfile.mkdtemp()` retorna o caminho sem resolver `/var/...`.

2. **Diretriz de Implementação de Testes:**
   - Sempre chame `.resolve()` em diretórios temporários criados em testes: `Path(tempfile.mkdtemp()).resolve()`.
   - Proibido usar asserções ingênuas como `output.startswith(str(tmp_dir))`. Use sempre pertinência canônica via `path.resolve().relative_to(base.resolve())`.

3. **Hermeticidade de Testes de Git:**
   - Não use `GIT_DIR=""` para simular ausência de Git em subprocessos. O Git aborta com erro fatal dependendo do SO. Para testar fallbacks sem Git, execute o teste dentro de um diretório sem `.git` apontando para um script isolado fora de repositórios Git.