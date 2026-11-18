"""
Módulo de Histórico (Serviços Concluídos, Alterações em Serviços e Alterações no Estoque)
Prefeitura de Papanduva - SC
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
import database as db
import cores
from datetime import date, datetime


_TIPO_ESTOQUE_LABEL = {
    "Entrada":  "⬆ Entrada",
    "Saída":    "⬇ Saída",
    "Cadastro": "➕ Cadastro",
    "Edição":   "✏️ Edição",
    "Exclusão": "🗑 Exclusão",
}

_TIPO_SERVICO_LABEL = {
    "Conclusão":            "✅ Conclusão",
    "Conclusão Desmarcada": "↩️ Desmarcada",
    "Cadastro":             "➕ Cadastro",
    "Edição":               "✏️ Edição",
    "Exclusão":             "🗑 Exclusão",
}

_AZUL = ["#1f6aa5", "#1f6aa5"]
_CINZA = "gray40"
_CINZA_HOVER = "gray50"


class HistoricoFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self._aba_atual = "servicos"
        self._build_ui()
        self._ver_servicos()

    def _build_ui(self):
        # ── Cabeçalho ─────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(header, text="📋  Histórico",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")

        # ── Abas ──────────────────────────────────────────────────────────────
        abas = ctk.CTkFrame(self, fg_color="transparent")
        abas.pack(fill="x", padx=16, pady=(0, 8))
        self.btn_servicos = ctk.CTkButton(abas, text="🔧 Serviços Concluídos",
                                          width=190, command=self._ver_servicos)
        self.btn_servicos.pack(side="left", padx=(0, 6))
        self.btn_ag_hist = ctk.CTkButton(abas, text="📝 Alterações em Serviços",
                                         width=205, fg_color=_CINZA,
                                         command=self._ver_ag_hist)
        self.btn_ag_hist.pack(side="left", padx=(0, 6))
        self.btn_mov = ctk.CTkButton(abas, text="📦 Alterações no Estoque",
                                     width=205, fg_color=_CINZA,
                                     command=self._ver_movimentacoes)
        self.btn_mov.pack(side="left")

        # ── Filtros ────────────────────────────────────────────────────────────
        filtros = ctk.CTkFrame(self, corner_radius=8)
        filtros.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(filtros, text="De:").pack(side="left", padx=(12, 4), pady=8)
        self.e_data_ini = ctk.CTkEntry(filtros, placeholder_text="DD/MM/AAAA", width=110)
        self.e_data_ini.pack(side="left", padx=4)
        hoje = date.today()
        self.e_data_ini.insert(0, hoje.replace(day=1).strftime("%d/%m/%Y"))

        ctk.CTkLabel(filtros, text="Até:").pack(side="left", padx=(8, 4))
        self.e_data_fim = ctk.CTkEntry(filtros, placeholder_text="DD/MM/AAAA", width=110)
        self.e_data_fim.pack(side="left", padx=4)
        self.e_data_fim.insert(0, hoje.strftime("%d/%m/%Y"))

        ctk.CTkLabel(filtros, text="Buscar:").pack(side="left", padx=(12, 4))
        self.e_busca = ctk.CTkEntry(filtros, placeholder_text="Título / Peça / Responsável...", width=200)
        self.e_busca.pack(side="left", padx=4)
        self.e_busca.bind("<Return>", lambda _: self._aplicar_filtros())

        self.lbl_tipo = ctk.CTkLabel(filtros, text="Tipo:")
        self.combo_tipo = ctk.CTkComboBox(
            filtros,
            values=["Todos"],
            width=155,
            command=lambda _: self._aplicar_filtros(),
        )
        self.combo_tipo.set("Todos")

        ctk.CTkButton(filtros, text="🔍", width=36,
                      command=self._aplicar_filtros).pack(side="left", padx=4)
        ctk.CTkButton(filtros, text="✕", width=36, fg_color="gray40",
                      command=self._limpar_filtros).pack(side="left", padx=4)

        # ── Container da tabela ────────────────────────────────────────────────
        self.table_frame = ctk.CTkFrame(self, corner_radius=8)
        self.table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#1f6aa5")])

        self._build_tabela_servicos()
        self._build_tabela_ag_hist()
        self._build_tabela_movimentacoes()

        # ── Rodapé (ações e legendas por aba) ──────────────────────────────────
        self.rodape = ctk.CTkFrame(self, fg_color="transparent")
        self.rodape.pack(fill="x", padx=16, pady=(0, 12))

        self.btn_desmarcar = ctk.CTkButton(
            self.rodape,
            text="↩️  Desmarcar Conclusão",
            width=190,
            fg_color="#fd7e14",
            hover_color="#dd6b0c",
            command=self._desmarcar_conclusao,
        )
        self.lbl_dica = ctk.CTkLabel(
            self.rodape,
            text="Duplo clique em um registro para ver os detalhes completos",
            font=ctk.CTkFont(size=11),
            text_color="gray50",
        )
        self.legenda_servicos = cores.legenda(
            self.rodape,
            [
                ("#d1e7dd", "Conclusão"),
                ("#fff3cd", "Desmarcada"),
                ("#cfe2ff", "Cadastro"),
                ("#e2d9f3", "Edição"),
                ("#f8d7da", "Exclusão"),
            ],
        )
        self.legenda_estoque = cores.legenda(
            self.rodape,
            [
                ("#d1e7dd", "Entrada"),
                ("#fff3cd", "Saída"),
                ("#cfe2ff", "Cadastro"),
                ("#e2d9f3", "Edição"),
                ("#f8d7da", "Exclusão"),
            ],
        )

    def _build_tabela_servicos(self):
        self.frame_serv = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        cols = ("ID", "Título", "Responsável", "Setor", "Data Conclusão",
                "Tempo (min)", "Solução")
        self.tree_serv = ttk.Treeview(self.frame_serv, columns=cols,
                                       show="headings", selectmode="browse")
        widths = (40, 220, 130, 120, 110, 80, 250)
        for col, w in zip(cols, widths):
            self.tree_serv.heading(col, text=col)
            self.tree_serv.column(col, width=w, anchor="w")

        vsb = ttk.Scrollbar(self.frame_serv, orient="vertical",
                            command=self.tree_serv.yview)
        hsb = ttk.Scrollbar(self.frame_serv, orient="horizontal",
                            command=self.tree_serv.xview)
        self.tree_serv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree_serv.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.frame_serv.grid_rowconfigure(0, weight=1)
        self.frame_serv.grid_columnconfigure(0, weight=1)
        self.tree_serv.bind("<Double-1>", self._ver_detalhe_servico)

    def _build_tabela_ag_hist(self):
        self.frame_ag_hist = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        cols = ("ID", "Serviço", "Alteração", "Antes", "Depois",
                "Resumo / Motivo", "Responsável", "Data")
        self.tree_ag_hist = ttk.Treeview(self.frame_ag_hist, columns=cols,
                                         show="headings", selectmode="browse")
        widths = (40, 180, 115, 90, 90, 240, 115, 125)
        for col, w in zip(cols, widths):
            self.tree_ag_hist.heading(col, text=col)
            self.tree_ag_hist.column(col, width=w, anchor="w")

        cores.configurar_tags_historico_agendamentos(self.tree_ag_hist)

        vsb = ttk.Scrollbar(self.frame_ag_hist, orient="vertical",
                            command=self.tree_ag_hist.yview)
        hsb = ttk.Scrollbar(self.frame_ag_hist, orient="horizontal",
                            command=self.tree_ag_hist.xview)
        self.tree_ag_hist.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree_ag_hist.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.frame_ag_hist.grid_rowconfigure(0, weight=1)
        self.frame_ag_hist.grid_columnconfigure(0, weight=1)
        self.tree_ag_hist.bind("<Double-1>", self._ver_detalhe_alteracao_servico)

    def _build_tabela_movimentacoes(self):
        self.frame_mov = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        cols = ("ID", "Peça", "Alteração", "Anterior", "Novo",
                "Motivo / Resumo", "Responsável", "Data")
        self.tree_mov = ttk.Treeview(self.frame_mov, columns=cols,
                                     show="headings", selectmode="browse")
        widths = (40, 190, 95, 60, 60, 260, 120, 125)
        for col, w in zip(cols, widths):
            self.tree_mov.heading(col, text=col)
            self.tree_mov.column(col, width=w, anchor="w")

        cores.configurar_tags_historico_estoque(self.tree_mov)

        vsb = ttk.Scrollbar(self.frame_mov, orient="vertical",
                            command=self.tree_mov.yview)
        hsb = ttk.Scrollbar(self.frame_mov, orient="horizontal",
                            command=self.tree_mov.xview)
        self.tree_mov.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree_mov.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.frame_mov.grid_rowconfigure(0, weight=1)
        self.frame_mov.grid_columnconfigure(0, weight=1)
        self.tree_mov.bind("<Double-1>", self._ver_detalhe_alteracao)

    def atualizar(self):
        """Chamado automaticamente ao navegar para a aba Histórico."""
        self._aplicar_filtros()

    def _estilizar_abas(self, ativa):
        mapa = {
            "servicos":      self.btn_servicos,
            "ag_hist":       self.btn_ag_hist,
            "movimentacoes": self.btn_mov,
        }
        for chave, btn in mapa.items():
            if chave == ativa:
                btn.configure(fg_color=_AZUL, hover_color=_AZUL)
            else:
                btn.configure(fg_color=_CINZA, hover_color=_CINZA_HOVER)

    def _ocultar_paineis(self):
        for w in (self.frame_serv, self.frame_ag_hist, self.frame_mov,
                  self.lbl_tipo, self.combo_tipo,
                  self.btn_desmarcar, self.lbl_dica,
                  self.legenda_servicos, self.legenda_estoque):
            w.pack_forget()

    def _ver_servicos(self):
        self._aba_atual = "servicos"
        self._estilizar_abas("servicos")
        self._ocultar_paineis()
        self.frame_serv.pack(fill="both", expand=True)
        self.btn_desmarcar.pack(side="left", padx=(0, 12))
        self.lbl_dica.pack(side="left")
        self.carregar_servicos()

    def _ver_ag_hist(self):
        self._aba_atual = "ag_hist"
        self._estilizar_abas("ag_hist")
        self._ocultar_paineis()
        self.combo_tipo.configure(
            values=["Todos", "Cadastro", "Edição", "Conclusão", "Conclusão Desmarcada", "Exclusão"]
        )
        if self.combo_tipo.get() not in ("Todos", "Cadastro", "Edição", "Conclusão", "Conclusão Desmarcada", "Exclusão"):
            self.combo_tipo.set("Todos")
        self.lbl_tipo.pack(side="left", padx=(10, 4))
        self.combo_tipo.pack(side="left", padx=4)
        self.frame_ag_hist.pack(fill="both", expand=True)
        self.lbl_dica.pack(side="left")
        self.legenda_servicos.pack(side="right")
        self.carregar_ag_hist()

    def _ver_movimentacoes(self):
        self._aba_atual = "movimentacoes"
        self._estilizar_abas("movimentacoes")
        self._ocultar_paineis()
        self.combo_tipo.configure(
            values=["Todos", "Entrada", "Saída", "Cadastro", "Edição", "Exclusão"]
        )
        if self.combo_tipo.get() not in ("Todos", "Entrada", "Saída", "Cadastro", "Edição", "Exclusão"):
            self.combo_tipo.set("Todos")
        self.lbl_tipo.pack(side="left", padx=(10, 4))
        self.combo_tipo.pack(side="left", padx=4)
        self.frame_mov.pack(fill="both", expand=True)
        self.lbl_dica.pack(side="left")
        self.legenda_estoque.pack(side="right")
        self.carregar_movimentacoes()

    def _datas_validas(self):
        for campo in (self.e_data_ini, self.e_data_fim):
            v = campo.get().strip()
            if v:
                try:
                    datetime.strptime(v, "%d/%m/%Y")
                except ValueError:
                    messagebox.showerror("Erro", "Data inválida. Use o formato DD/MM/AAAA.")
                    return False
        return True

    def _aplicar_filtros(self):
        if not self._datas_validas():
            return
        if self._aba_atual == "servicos":
            self.carregar_servicos()
        elif self._aba_atual == "ag_hist":
            self.carregar_ag_hist()
        else:
            self.carregar_movimentacoes()

    def _limpar_filtros(self):
        self.e_busca.delete(0, "end")
        self.combo_tipo.set("Todos")
        hoje = date.today()
        self.e_data_ini.delete(0, "end")
        self.e_data_ini.insert(0, hoje.replace(day=1).strftime("%d/%m/%Y"))
        self.e_data_fim.delete(0, "end")
        self.e_data_fim.insert(0, hoje.strftime("%d/%m/%Y"))
        self._aplicar_filtros()

    def carregar_servicos(self):
        di = self.e_data_ini.get().strip() or None
        df = self.e_data_fim.get().strip() or None
        busca = self.e_busca.get().strip() or None
        rows = db.listar_historico_servicos(data_inicio=di, data_fim=df, busca=busca)
        self.tree_serv.delete(*self.tree_serv.get_children())
        for r in rows:
            solucao = (r["solucao"] or "")[:60]
            self.tree_serv.insert("", "end", iid=str(r["id"]),
                                  values=(r["id"], r["titulo"], r["responsavel"] or "",
                                          r["setor"] or "", db.to_display_date(r["data_conclusao"]),
                                          r["tempo_gasto_min"] or "", solucao))

    def carregar_ag_hist(self):
        di = self.e_data_ini.get().strip() or None
        df = self.e_data_fim.get().strip() or None
        busca = self.e_busca.get().strip() or None
        tipo = self.combo_tipo.get()
        rows = db.listar_historico_agendamentos(tipo=tipo, data_inicio=di, data_fim=df, busca=busca)
        self.tree_ag_hist.delete(*self.tree_ag_hist.get_children())
        for r in rows:
            tipo_raw = r["tipo"]
            tipo_txt = _TIPO_SERVICO_LABEL.get(tipo_raw, tipo_raw)
            resumo = r["detalhes"] or r["motivo"] or ""
            self.tree_ag_hist.insert(
                "", "end", iid=str(r["id"]),
                values=(r["id"], r["titulo"], tipo_txt,
                        r["status_anterior"] or "—", r["status_novo"] or "—",
                        resumo[:75], r["responsavel"] or "",
                        db.to_display_date(r["data_alter"])),
                tags=(tipo_raw,),
            )

    def carregar_movimentacoes(self):
        di = self.e_data_ini.get().strip() or None
        df = self.e_data_fim.get().strip() or None
        busca = self.e_busca.get().strip() or None
        tipo = self.combo_tipo.get()
        rows = db.listar_historico_estoque(tipo=tipo, data_inicio=di, data_fim=df, busca=busca)
        self.tree_mov.delete(*self.tree_mov.get_children())
        for r in rows:
            tipo_raw = r["tipo"]
            tipo_txt = _TIPO_ESTOQUE_LABEL.get(tipo_raw, tipo_raw)
            resumo = r["detalhes"] or r["motivo"] or ""
            if r["motivo"] and r["detalhes"] and tipo_raw in ("Entrada", "Saída"):
                resumo = f"{r['motivo']} ({r['detalhes']})"
            self.tree_mov.insert("", "end", iid=str(r["id"]),
                                 values=(r["id"], r["peca_nome"],
                                         tipo_txt,
                                         "" if r["qtd_anterior"] is None else r["qtd_anterior"],
                                         "" if r["qtd_nova"] is None else r["qtd_nova"],
                                         resumo[:75], r["responsavel"] or "",
                                         db.to_display_date(r["data_alter"])),
                                 tags=(tipo_raw,))

    def _desmarcar_conclusao(self):
        sel = self.tree_serv.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um serviço concluído na lista.")
            return
        FormDesmarcarConclusao(self, historico_id=int(sel[0]),
                               callback=self.carregar_servicos)

    def _ver_detalhe_servico(self, event=None):
        sel = self.tree_serv.selection()
        if not sel:
            return
        reg = db.obter_historico_servico(int(sel[0]))
        if reg:
            DetalheServico(self, reg)

    def _ver_detalhe_alteracao_servico(self, event=None):
        sel = self.tree_ag_hist.selection()
        if not sel:
            return
        reg = db.obter_alteracao_agendamento(int(sel[0]))
        if reg:
            DetalheAlteracaoServico(self, reg)

    def _ver_detalhe_alteracao(self, event=None):
        sel = self.tree_mov.selection()
        if not sel:
            return
        reg = db.obter_alteracao_estoque(int(sel[0]))
        if reg:
            DetalheAlteracaoEstoque(self, reg)


class FormDesmarcarConclusao(ctk.CTkToplevel):
    def __init__(self, master, historico_id, callback=None):
        super().__init__(master)
        self.title("Desmarcar Conclusão")
        self.geometry("500x380")
        self.minsize(460, 340)
        self.historico_id = historico_id
        self.callback = callback
        self._processando = False

        reg = db.obter_historico_servico(historico_id)
        titulo = reg["titulo"] if reg else f"ID {historico_id}"

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(side="bottom", fill="x", padx=16, pady=(4, 14))
        self.btn_confirmar = ctk.CTkButton(
            btns, text="↩️  Confirmar", fg_color="#fd7e14",
            hover_color="#dd6b0c", command=self._confirmar, width=160
        )
        self.btn_confirmar.pack(side="right", padx=(6, 0))
        ctk.CTkButton(
            btns, text="Cancelar", fg_color="gray40",
            command=lambda: cores.fechar_modal(self), width=100
        ).pack(side="right")

        ctk.CTkFrame(self, height=1, fg_color="gray30").pack(
            side="bottom", fill="x", padx=16)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=16, pady=(16, 4))

        ctk.CTkLabel(
            frame,
            text=f"Desmarcar conclusão de: {titulo}",
            font=ctk.CTkFont(size=14, weight="bold"),
            wraplength=460, justify="left"
        ).pack(anchor="w", pady=(0, 6))
        ctk.CTkLabel(
            frame,
            text="O serviço voltará para a tela de Agendamentos e esta alteração será registrada no histórico.",
            text_color="gray50", wraplength=460, justify="left"
        ).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(frame, text="Retornar com o status:", anchor="w").pack(fill="x")
        self.combo_status = ctk.CTkComboBox(frame, values=["Pendente", "Em andamento"])
        self.combo_status.set("Pendente")
        self.combo_status.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(frame, text="Motivo / Observação (opcional):", anchor="w").pack(fill="x")
        self.e_motivo = ctk.CTkEntry(frame, placeholder_text="Ex: Marcado como concluído por engano")
        self.e_motivo.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(frame, text="Responsável pela alteração (opcional):", anchor="w").pack(fill="x")
        self.e_resp = ctk.CTkEntry(frame, placeholder_text="Nome do técnico")
        self.e_resp.pack(fill="x", pady=(4, 4))

        cores.preparar_modal(self, master, focus_widget=self.e_motivo)

    def _confirmar(self):
        if self._processando:
            return
        self._processando = True
        self.btn_confirmar.configure(state="disabled")
        novo_status = self.combo_status.get()
        motivo = self.e_motivo.get().strip()
        resp = self.e_resp.get().strip()
        try:
            db.desmarcar_conclusao_servico(
                self.historico_id,
                novo_status=novo_status,
                motivo=motivo,
                responsavel=resp,
            )
        except Exception as e:
            self._processando = False
            self.btn_confirmar.configure(state="normal")
            cores.erro_modal(self, "Erro", f"Não foi possível desmarcar a conclusão:\n{e}")
            return

        cores.concluir_modal(
            self, self.callback, "Sucesso",
            f"Conclusão desmarcada.\nO serviço retornou aos Agendamentos como \"{novo_status}\"."
        )


class DetalheServico(ctk.CTkToplevel):
    def __init__(self, master, registro):
        super().__init__(master)
        self.title("Detalhe do Serviço")
        self.geometry("520x420")

        frame = ctk.CTkScrollableFrame(self)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        def campo(label, valor):
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(weight="bold"),
                         anchor="w").pack(fill="x", pady=(8, 2))
            ctk.CTkLabel(frame, text=str(valor or "—"), anchor="w",
                         wraplength=460, justify="left").pack(fill="x")

        campo("Título", registro["titulo"])
        campo("Responsável", registro["responsavel"])
        campo("Setor", registro["setor"])
        campo("Data de Conclusão", db.to_display_date(registro["data_conclusao"]))
        campo("Tempo gasto", f"{registro['tempo_gasto_min']} min" if registro["tempo_gasto_min"] else "—")
        campo("Descrição original", registro["descricao"])
        campo("Solução aplicada", registro["solucao"])
        campo("Observações", registro["observacoes"])

        ctk.CTkButton(frame, text="Fechar",
                      command=lambda: cores.fechar_modal(self)).pack(pady=12)
        cores.preparar_modal(self, master)


class DetalheAlteracaoServico(ctk.CTkToplevel):
    def __init__(self, master, registro):
        super().__init__(master)
        self.title("Detalhe da Alteração no Serviço")
        self.geometry("520x440")

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(side="bottom", fill="x", padx=16, pady=(4, 12))
        ctk.CTkButton(btns, text="Fechar",
                      command=lambda: cores.fechar_modal(self), width=110).pack(side="right")

        frame = ctk.CTkScrollableFrame(self)
        frame.pack(fill="both", expand=True, padx=16, pady=(16, 4))

        def campo(label, valor):
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(weight="bold"),
                         anchor="w").pack(fill="x", pady=(8, 2))
            ctk.CTkLabel(frame, text=str(valor if valor not in (None, "") else "—"),
                         anchor="w", wraplength=460, justify="left").pack(fill="x")

        campo("Tipo de alteração", _TIPO_SERVICO_LABEL.get(registro["tipo"], registro["tipo"]))
        campo("Serviço", registro["titulo"])
        campo("Status (antes → depois)",
              f"{registro['status_anterior'] or '—'} → {registro['status_novo'] or '—'}")
        campo("Motivo", registro["motivo"])
        campo("Responsável", registro["responsavel"])
        campo("Data / Hora", db.to_display_date(registro["data_alter"]))
        campo("Detalhes", registro["detalhes"])
        cores.preparar_modal(self, master)


class DetalheAlteracaoEstoque(ctk.CTkToplevel):
    def __init__(self, master, registro):
        super().__init__(master)
        self.title("Detalhe da Alteração no Estoque")
        self.geometry("520x440")

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(side="bottom", fill="x", padx=16, pady=(4, 12))
        ctk.CTkButton(btns, text="Fechar",
                      command=lambda: cores.fechar_modal(self), width=110).pack(side="right")

        frame = ctk.CTkScrollableFrame(self)
        frame.pack(fill="both", expand=True, padx=16, pady=(16, 4))

        def campo(label, valor):
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(weight="bold"),
                         anchor="w").pack(fill="x", pady=(8, 2))
            ctk.CTkLabel(frame, text=str(valor if valor not in (None, "") else "—"),
                         anchor="w", wraplength=460, justify="left").pack(fill="x")

        campo("Tipo de alteração", _TIPO_ESTOQUE_LABEL.get(registro["tipo"], registro["tipo"]))
        campo("Peça", registro["peca_nome"])
        campo("Quantidade (antes → depois)",
              f"{registro['qtd_anterior']} → {registro['qtd_nova']}")
        campo("Motivo", registro["motivo"])
        campo("Responsável", registro["responsavel"])
        campo("Data / Hora", db.to_display_date(registro["data_alter"]))
        campo("Detalhes", registro["detalhes"])
        cores.preparar_modal(self, master)
