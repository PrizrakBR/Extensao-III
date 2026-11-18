# Sistema de Controle de Estoque e Agendamentos — TI Papanduva

**Sistema desktop local** desenvolvido para uso no estágio em Tecnologia da Informação da **Prefeitura Municipal de Papanduva - SC**, integrando o **Projeto de Extensão III (ADS)**.

> [!TIP]
> **Para instalar no Windows sem precisar do Python**, baixe o instalador (`Setup_TI_Papanduva_v1.5.1.exe` para Windows 7 SP1+ ou `Setup_TI_Papanduva_v1.5.exe` para Windows 10/11) na aba **Releases** deste repositório.

---

## 📋 Funcionalidades

| Módulo | Descrição |
|--------|-----------|
| **Painel** | Resumo por status, serviços atrasados (vermelho) e próximos 7 dias, e alertas de estoque (zerado em vermelho, abaixo do mínimo em laranja) |
| **Agendamentos** | Cadastro, edição, busca, filtros e conclusão de ordens de serviço com datas `DD/MM/AAAA` |
| **Estoque** | Cadastro de peças, entradas/saídas com histórico completo e alertas visuais de estoque zerado ou baixo |
| **Histórico** | Três abas: **Serviços Concluídos** (com opção de desmarcar conclusão), **Alterações em Serviços** e **Alterações no Estoque** |
| **Backup e Restauração** | Botões **Fazer Backup** e **Lançar Backup** (com validação do arquivo e cópia de segurança automática antes de restaurar) |

---

## 🚀 Como Executar pelo Código-Fonte

1. Instale as dependências (Windows):
   ```bat
   instalar.bat
   ```
   *(Ou instale `customtkinter` em Python 3.8+ via `pip install customtkinter`.)*
2. Execute o sistema:
   ```bat
   iniciar.bat
   ```

---

## 🗂 Estrutura de Arquivos

```text
estoque_ti/
├── main.py             ← Janela principal, menu lateral, tema e backup/restauração
├── database.py         ← Banco SQLite e operações de agendamentos, estoque e histórico
├── cores.py            ← Regras de destaque, tags das tabelas e controle seguro de modais
├── dashboard.py        ← Tela: Painel principal
├── agendamentos.py     ← Tela: Agendamentos de serviços
├── estoque.py          ← Tela: Controle de estoque de peças
├── historico.py        ← Tela: Histórico (concluídos, alterações em serviços e estoque)
├── icone.ico           ← Ícone da aplicação e do instalador
├── ti_papanduva*.spec  ← Especificações de empacotamento (PyInstaller)
├── instalador/         ← Scripts do instalador (Inno Setup 6)
├── instalar.bat        ← Script de instalação de dependências
├── iniciar.bat         ← Script de execução local
└── README.md           ← Este arquivo
```

---

## 🗄️ Banco de Dados

O sistema utiliza **SQLite** local (`estoque_ti.db`), sem necessidade de servidor externo:
- Quando executado pelo código-fonte: salvo na pasta do projeto.
- Quando instalado pelo `Setup`: salvo em `%LOCALAPPDATA%\TI_Papanduva\estoque_ti.db` (preservado entre atualizações e desinstalações).

### Tabelas
- `agendamentos` — ordens de serviço agendadas
- `historico_servicos` — serviços atualmente concluídos
- `historico_agendamentos` — histórico completo de alterações em serviços (cadastros, edições, conclusões, conclusões desmarcadas e exclusões)
- `estoque` — cadastro de peças
- `movimentacoes` — entradas e saídas de estoque
- `historico_estoque` — histórico completo de alterações no estoque (cadastros, edições, entradas, saídas e exclusões)

---

## 🛠 Tecnologias Utilizadas

- **Python 3** (3.8 para build compatível com Windows 7 SP1+; 3.11 para Windows 10/11)
- **CustomTkinter** — interface gráfica moderna com modo claro/escuro
- **Tkinter / `ttk`** — tabelas (`Treeview`) e diálogos nativos
- **SQLite** — banco de dados local embutido
- **PyInstaller** e **Inno Setup 6** — empacotamento e instalador Windows

---

*Projeto de Extensão III — ADS — Gustavo Zattar — Prefeitura de Papanduva - SC*
