# Como lançar uma nova versão do Gestão Inteligente

Guia passo a passo para lançar atualizações do sistema. Siga na ordem.

> **Exemplo:** vamos supor que você está lançando a versão **3.0.4** (a atual é 3.0.3).

---

## Passo 1 — Atualizar o número da versão (3 arquivos)

### 1.1 — `app/config.py`
```python
APP_VERSION = "3.0.4"
```

### 1.2 — `instalador/setup.iss`
```iss
#define AppVersion "3.0.4"
...
VersionInfoVersion=3.0.4.0
```

### 1.3 — `instalador/atualizacao.iss`
```iss
#define AppVersion "3.0.4"
...
VersionInfoVersion=3.0.4.0
```

> **Importante:** o número deve ser igual nos 3 arquivos. O nome dos instaladores é gerado automaticamente a partir dessa versão (ex: `gestaointeligente3.0.4.exe`).

---

## Passo 1.5 — Rodar os testes (recomendado)

Antes de gerar o instalador, rode os testes para garantir que nada quebrou:

```powershell
cd "c:\Users\renat\OneDrive\Área de Trabalho\Projeto Sistema\Gestão Inteligente 3.0"
& ".venv\Scripts\python.exe" -m pytest tests/
```

Deve aparecer **"N passed"** (todos passando). Se algum falhar, **corrija antes de continuar** — assim você evita enviar uma versão com problema para os clientes.

> Na primeira vez, instale as dependências de desenvolvimento:
> ```powershell
> & ".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
> ```

---

## Passo 2 — Gerar os instaladores

Abra o **PowerShell** na pasta do projeto e rode os comandos abaixo.

### 2.1 — Gerar o executável do sistema (PyInstaller)
```powershell
cd "c:\Users\renat\OneDrive\Área de Trabalho\Projeto Sistema\Gestão Inteligente 3.0\instalador\build"
& "c:\Users\renat\OneDrive\Área de Trabalho\Projeto Sistema\Gestão Inteligente 3.0\.venv\Scripts\python.exe" -m PyInstaller --noconfirm GestaoInteligente.spec
```

### 2.2 — Gerar o instalador completo (para máquinas novas)
```powershell
cd "c:\Users\renat\OneDrive\Área de Trabalho\Projeto Sistema\Gestão Inteligente 3.0\instalador"
& "C:\Users\renat\AppData\Local\Programs\Inno Setup 6\ISCC.exe" setup.iss
```
Gera: `gestaointeligente3.0.4.exe`

### 2.3 — Gerar o pacote de atualização (para clientes existentes)
```powershell
& "C:\Users\renat\AppData\Local\Programs\Inno Setup 6\ISCC.exe" atualizacao.iss
```
Gera: `atualizacao_gestaointeligente3.0.4.exe`

> Os dois arquivos ficam na pasta `instalador\`.

---

## Passo 3 — Enviar o código para o GitHub

```powershell
cd "c:\Users\renat\OneDrive\Área de Trabalho\Projeto Sistema\Gestão Inteligente 3.0"
git add -A
git commit -m "v3.0.4: descreva aqui o que mudou"
git push origin main
```

---

## Passo 4 — Criar a Release no GitHub (ativa o auto-update)

1. Acesse: `https://github.com/renatof-dev/gestaointeligente3.0/releases/new`
2. **Choose a tag:** digite `3.0.4` e clique em **Create new tag: 3.0.4**
3. **Target:** deixe `main`
4. **Release title:** `Versão 3.0.4`
5. **Release notes (opcional):** descreva o que mudou, por exemplo:
   ```
   Versão 3.0.4

   - Correção de ...
   - Melhoria em ...
   ```
6. **Anexar o arquivo:** arraste **`atualizacao_gestaointeligente3.0.4.exe`** para a área de anexos
   - ⚠️ Anexe o arquivo de **ATUALIZAÇÃO**, NÃO o instalador completo
7. **Release label:** deixe em **None** (NÃO marque "Pre-release")
8. Clique em **Publish release**

---

## Pronto! 🎉

A partir do momento em que a release é publicada, **todos os clientes** com versão anterior serão notificados automaticamente na próxima vez que abrirem o sistema, e poderão atualizar com um clique.

---

## ⚠️ Regras de ouro (não esqueça)

1. **A tag deve ser o número da versão** (`3.0.4`, `3.0.5`...). O sistema compara esse número para saber se há atualização.
2. **Anexe o arquivo de ATUALIZAÇÃO** (`atualizacao_gestaointeligente...exe`). O sistema procura especificamente por esse nome.
3. **NÃO marque "Pre-release"** — senão o sistema não detecta a atualização.
4. **O número da versão deve ser igual** nos 3 arquivos do Passo 1 e na tag do GitHub.

---

## Resumo visual do fluxo

```
1. Mudar versão (config.py + 2 arquivos .iss)
        ↓
2. Gerar instaladores (PyInstaller + Inno Setup)
        ↓
3. git commit + push
        ↓
4. Criar Release no GitHub (tag + anexar atualizacao_....exe)
        ↓
5. Clientes atualizam sozinhos ao abrir o sistema ✅
```

---

## Dica: para máquinas NOVAS

Envie o arquivo **`gestaointeligente3.0.4.exe`** (instalador completo). Esse não precisa ir para o GitHub — você envia direto para o cliente novo.

---

## Dica: trocar a senha de e-mail SEM recompilar o instalador

O sistema lê as credenciais de e-mail do arquivo `.env`. Há **dois** lugares onde ele procura, nesta ordem de prioridade:

1. `%LOCALAPPDATA%\GestaoInteligente\.env` → **prioridade maior** (pasta de dados do usuário)
2. Pasta de instalação (`C:\Program Files\Gestao Inteligente 3.0\.env`) → padrão

**Para trocar a senha de e-mail de um cliente** (sem recompilar/reinstalar nada):

1. Abra a pasta `%LOCALAPPDATA%\GestaoInteligente` na máquina do cliente
2. Crie ou edite o arquivo `.env` com o conteúdo:
   ```
   EMAIL_REM=renato.gestaointeligente@gmail.com
   EMAIL_SENHA=nova_senha_de_app
   ```
3. Reinicie o sistema

O sistema passa a usar essa senha imediatamente, ignorando a que veio embutida no instalador.
