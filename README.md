# 📋 Dossiê Operacional Padrão v44 • ABDI + TJPB + TJRN

Painel interativo e banco de dados de acompanhamento de estudos, simulados e marcos administrativos para os concursos **ABDI**, **TJPB** e **TJRN** (Banca FGV).

## 🗄️ Arquitetura de Banco de Dados (3 Camadas)

1. **Banco NoSQL no Navegador (`IndexedDB` + `LocalStorage`)**: Grava instantaneamente cada clique, nota e quantidade de acertos mesmo quando acessado diretamente via GitHub Pages ou arquivo local.
2. **Banco Relacional Local (`SQLite3` — `data/estudos.db`)**: Quando iniciado pelo atalho `iniciar_painel.bat` (ou `python server.py`), todas as marcações são salvas em tabelas SQLite (`checklist_items` e `state_snapshots`) e espelhadas em `data/progress_db.json`.
3. **Sincronização em Nuvem (`GitHub REST API`)**: Permite sincronizar o banco (`data/progress_db.json`) diretamente com o repositório no GitHub clicando em **"☁️ Sincronizar Banco GitHub / API"**.

## 🚀 Como Usar Localmente com Banco SQLite
Basta dar duplo clique em [`iniciar_painel.bat`](iniciar_painel.bat) ou executar:
```bash
python server.py
```
E abrir `http://localhost:8080`.
