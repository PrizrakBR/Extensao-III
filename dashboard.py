"""
Dashboard / Tela Inicial
Prefeitura de Papanduva - SC
"""

import customtkinter as ctk
from tkinter import ttk
import database as db
import cores
from datetime import date, timedelta


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, nav_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self.nav_callback = nav_callback  # função para navegar para outra aba
        self._build_ui()
        self.atualizar()

    def _build_ui(self):
        # ── Título ─────────────────────────────────────────────────────────────
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=20, pady=(20, 4))
        ctk.CTkLabel(topo, text="🏛️  TI Papanduva — Painel Principal",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        self.lbl_data = ctk.CTkLabel(topo, text="", font=ctk.CTkFont(size=13))
        self.lbl_data.pack(side="right")
        _dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
                 "Sexta-feira", "Sábado", "Domingo"]
        _hoje = date.today()
        self.lbl_data.configure(text=f"{_dias[_hoje.weekday()]}, {_hoje.strftime('%d/%m/%Y')}")

        # ── Cards de resumo ────────────────────────────────────────────────────
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20, pady=(12, 4))

        self.card_pendentes   = self._make_card(cards_frame, "Serviços\nPendentes",   "0", "#fd7e14")
        self.card_andamento   = self._make_card(cards_frame, "Em\nAndamento",         "0", "#0d6efd")
        self.card_concluidos  = self._make_card(cards_frame, "Concluídos\nHoje",      "0", "#198754")
        self.card_estoque     = self._make_card(cards_frame, "Itens em\nEstoque",     "0", "#6f42c1")
        self.card_alerta      = self._make_card(cards_frame, "Alertas de\nEstoque",   "0", "#dc3545")

        # ── Próximos agendamentos ──────────────────────────────────────────────
        ctk.CTkLabel(self, text="📅  Atrasados (vermelho) e próximos 7 dias",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=20, pady=(16, 4))

        prox_frame = ctk.CTkFrame(self, corner_radius=8)
        prox_frame.pack(fill="x", padx=20, pady=(0, 12))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dash.Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Dash.Treeview.Heading", font=("Segoe UI", 10, "bold"))

        cols = ("Data", "Hora", "Título", "Responsável", "Setor", "Prioridade", "Status")
        self.tree_prox = ttk.Treeview(prox_frame, columns=cols, show="headings",
                                       height=6, style="Dash.Treeview")
        widths = (90, 60, 230, 130, 120, 90, 100)
        for col, w in zip(cols, widths):
            self.tree_prox.heading(col, text=col)
            self.tree_prox.column(col, width=w, anchor="w")

        self.tree_prox.tag_configure("Urgente",    background="#f8d7da", foreground="#000000")
        self.tree_prox.tag_configure("Alta",       background="#fff3cd", foreground="#000000")
        self.tree_prox.tag_configure("Normal",     background="", foreground="#000000")
        self.tree_prox.tag_configure("Baixa",      background="#d1e7dd", foreground="#000000")
        self.tree_prox.tag_configure("atrasado",   background=cores.VERMELHO[0], foreground=cores.VERMELHO[1])

        vsb = ttk.Scrollbar(prox_frame, orient="vertical", command=self.tree_prox.yview)
        hsb = ttk.Scrollbar(prox_frame, orient="horizontal", command=self.tree_prox.xview)
        self.tree_prox.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree_prox.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        prox_frame.grid_rowconfigure(0, weight=1)
        prox_frame.grid_columnconfigure(0, weight=1)

        # ── Alertas de estoque ─────────────────────────────────────────────────
        ctk.CTkLabel(self, text="⚠️  Estoque: zerado (vermelho) e abaixo do mínimo (laranja)",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=20, pady=(4, 4))

        alerta_frame = ctk.CTkFrame(self, corner_radius=8)
        alerta_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        cols2 = ("Peça", "Categoria", "Qtd. Atual", "Qtd. Mínima", "Localização")
        self.tree_alerta = ttk.Treeview(alerta_frame, columns=cols2, show="headings",
                                         height=5, style="Dash.Treeview")
        widths2 = (240, 130, 90, 90, 170)
        for col, w in zip(cols2, widths2):
            self.tree_alerta.heading(col, text=col)
            self.tree_alerta.column(col, width=w, anchor="w")
        self.tree_alerta.tag_configure("critico",   background=cores.VERMELHO[0], foreground=cores.VERMELHO[1])
        self.tree_alerta.tag_configure("zerado",    background=cores.VERMELHO[0], foreground=cores.VERMELHO[1])
        self.tree_alerta.tag_configure("alerta",    background=cores.LARANJA[0], foreground=cores.LARANJA[1])
        self.tree_alerta.tag_configure("ok",        background="", foreground="#000000")

        vsb2 = ttk.Scrollbar(alerta_frame, orient="vertical", command=self.tree_alerta.yview)
        self.tree_alerta.configure(yscrollcommand=vsb2.set)
        self.tree_alerta.grid(row=0, column=0, sticky="nsew")
        vsb2.grid(row=0, column=1, sticky="ns")
        alerta_frame.grid_rowconfigure(0, weight=1)
        alerta_frame.grid_columnconfigure(0, weight=1)

        # ── Botão atualizar ────────────────────────────────────────────────────
        ctk.CTkButton(self, text="🔄  Atualizar Painel", width=180,
                      command=self.atualizar).pack(pady=(0, 16))

    def _make_card(self, parent, label, valor, cor):
        f = ctk.CTkFrame(parent, corner_radius=10, fg_color=cor, width=150, height=90)
        f.pack(side="left", padx=6, pady=4, expand=True, fill="x")
        f.pack_propagate(False)
        lbl_val = ctk.CTkLabel(f, text=valor,
                                font=ctk.CTkFont(size=30, weight="bold"),
                                text_color="white")
        lbl_val.pack(pady=(12, 2))
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=11),
                     text_color="white", justify="center").pack()
        return lbl_val

    def atualizar(self):
        # Cards de agendamentos
        contagem = db.contar_agendamentos_por_status()
        self.card_pendentes.configure(text=str(contagem.get("Pendente", 0)))
        self.card_andamento.configure(text=str(contagem.get("Em andamento", 0)))

        hoje_str = date.today().strftime("%Y-%m-%d")
        hist_hoje = db.listar_historico_servicos(data_inicio=hoje_str, data_fim=hoje_str)
        self.card_concluidos.configure(text=str(len(hist_hoje)))

        # Cards de estoque
        self.card_estoque.configure(text=str(db.contar_total_pecas()))
        self.card_alerta.configure(text=str(db.contar_itens_abaixo_minimo()))

        # Atrasados (vermelho) + próximos 7 dias
        hoje = date.today()
        fim = hoje + timedelta(days=7)
        atrasados = list(db.listar_agendamentos_atrasados())
        proximos = []
        for st in cores.STATUS_EM_ABERTO:
            proximos += list(db.listar_agendamentos(
                status=st,
                data_inicio=hoje_str,
                data_fim=fim.strftime("%Y-%m-%d")
            ))
        proximos.sort(key=lambda r: (r["data_agendada"], r["hora_agendada"] or ""))
        self.tree_prox.delete(*self.tree_prox.get_children())
        for r in atrasados + proximos:
            prio = r["prioridade"] or "Normal"
            tag = "atrasado" if cores.agendamento_atrasado(r["data_agendada"], r["status"]) else prio
            self.tree_prox.insert("", "end",
                                  values=(db.to_display_date(r["data_agendada"]), r["hora_agendada"] or "",
                                          r["titulo"], r["responsavel"] or "",
                                          r["setor"] or "", prio, r["status"] or ""),
                                  tags=(tag,))

        # Alertas estoque (zerado = vermelho, abaixo do mínimo = laranja)
        pecas_baixas = db.listar_estoque(apenas_abaixo_minimo=True)
        self.tree_alerta.delete(*self.tree_alerta.get_children())
        for p in pecas_baixas:
            tag = cores.tag_estoque(p["quantidade"], p["quantidade_min"])
            self.tree_alerta.insert("", "end",
                                    values=(p["nome"],
                                            p["categoria"] or "", p["quantidade"],
                                            p["quantidade_min"], p["localizacao"] or ""),
                                    tags=(tag,))
