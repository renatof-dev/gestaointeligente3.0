# Gestao Inteligente 3.0

Sistema desktop local em Python para gestao de vendas com PDV, fluxo de caixa, usuarios, estoque, clientes e fornecedores.

## Rodando local

1. Crie/ative um ambiente Python.
2. Instale dependencias:
   - `pip install -r requirements.txt`
3. Execute:
   - `python main.py`

## Login padrao inicial

- Usuario: `admin`
- Senha: `admin123`

## Banco de dados

- SQLite local em `data/gestao_inteligente.db`.

## Regras de lucro real no PDV

O calculo considera:

- Total bruto dos itens
- Desconto aplicado na venda
- Taxas por meio de pagamento (debito, credito a vista, credito parcelado, pix maquininha)
- Custo total dos produtos

Formula principal:

- `total_liquido = total_bruto - desconto`
- `taxas = soma(valor_pagamento * taxa_do_metodo)`
- `valor_recebido_real = total_liquido - taxas`
- `lucro_real = valor_recebido_real - custo_total`

## Backup automatico no encerramento

Ao fechar o sistema:

1. O backup local do banco e gerado em `backups/`.
2. O sistema tenta enviar por email para o endereco cadastrado em Configuracoes > Dados da Empresa.

Para habilitar envio SMTP (Gmail), configure variaveis de ambiente:

- `GI_SMTP_SENDER`
- `GI_SMTP_PASSWORD`

Exemplo (PowerShell):

```powershell
setx GI_SMTP_SENDER "seu-email@gmail.com"
setx GI_SMTP_PASSWORD "sua-senha-app"
```

## Direitos reservados

Renato dos Santos Fernandes
