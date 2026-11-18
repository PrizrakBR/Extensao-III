"""
Janela de Agendamentos — v1.1
Prefeitura de Papanduva - SC
"""

import customtkinter as ctk
from tkinter import messagebox, ttk
import database as db
import cores
from datetime import datetime, date


class AgendamentosFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self._build_ui()
        self.carregar_agendamentos()

    def _build_ui(self):
        # ── Cabeçalho ─────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(header, text="📅  Agendamentos de Serviços",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="＋  Novo Agendamento", width=180,
                      command=self._abrir_form_novo).pack(side="right")

        # ── Filtros ────────────────────────────────────────────────────────────
        filtros = ctk.CTkFrame(self, corner_radius=8)
        filtros.pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkLabel(filtros, text="Status:").pack(side="left", padx=(12, 4), pady=8)
        self.combo_status = ctk.CTkComboBox(
            filtros, values=["Todos", "Pendente", "Em andamento", "Concluído", "Cancelado"],
            width=160, command=lambda _: self.carregar_agendamentos())
        self.combo_status.set("Pendente")
        self.combo_status.pack(side="left", padx=4, pady=8)
        ctk.CTkLabel(filtros, text="Buscar:").pack(side="left", padx=(12, 4))
        self.entry_busca = ctk.CTkEntry(filtros, placeholder_text="Título / Responsável / Setor", width=220)
        self.entry_busca.pack(side="left", padx=4, pady=8)
        self.entry_busca.bind("<Return>", lambda _: self.carregar_agendamentos())
        ctk.CTkButton(filtros, text="🔍", width=36,
                      command=self.carregar_agendamentos).pack(side="left", padx=4)
        ctk.CTkButton(filtros, text="✕ Limpar", width=80, fg_color="gray40",
                      command=self._limpar_filtros).pack(side="left", padx=4)

        # ── Tabela ─────────────────────────────────────────────────────────────
        table_frame = ctk.CTkFrame(self, corner_radius=8)
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#1f6aa5")])
        cols = ("ID", "Título", "Responsável", "Setor", "Data", "Hora", "Prioridade", "Status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        widths = (40, 220, 130, 120, 90, 60, 90, 100)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_column(c))
            self.tree.column(col, width=w, anchor="w")
        cores.configurar_tags_agendamento(self.tree)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        self.tree.bind("<Double-1>", lambda _: self._abrir_detalhe())

        # ── Barra de ações ─────────────────────────────────────────────────────
        acoes = ctk.CTkFrame(self, fg_color="transparent")
        acoes.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(acoes, text="✏️  Editar", width=130,
                      command=self._editar_selecionado).pack(side="left", padx=(0, 6))
        ctk.CTkButton(acoes, text="✅  Concluir", width=130, fg_color="#198754",
                      command=self._concluir_selecionado).pack(side="left", padx=6)
        ctk.CTkButton(acoes, text="🗑  Excluir", width=130, fg_color="#dc3545",
                      command=self._excluir_selecionado).pack(side="left", padx=6)
        ctk.CTkButton(acoes, text="🔄  Atualizar", width=130, fg_color="gray40",
                      command=self.carregar_agendamentos).pack(side="right")
        cores.legenda(acoes, [(cores.VERMELHO[0], "Atrasado (data passou e não foi concluído)")]
                      ).pack(side="right", padx=12)

        self._sort_col = None
        self._sort_rev = False

    def _limpar_filtros(self):
        self.combo_status.set("Todos")
        self.entry_busca.delete(0, "end")
        self.carregar_agendamentos()

    def carregar_agendamentos(self, *_):
        status = self.combo_status.get()
        busca = self.entry_busca.get().strip().lower()
        rows = db.listar_agendamentos(status=status)
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            if busca and busca not in (r["titulo"] or "").lower() \
                     and busca not in (r["responsavel"] or "").lower() \
                     and busca not in (r["setor"] or "").lower():
                continue
            self.tree.insert("", "end", iid=str(r["id"]),
                             values=(r["id"], r["titulo"], r["responsavel"] or "",
                                     r["setor"] or "",
                                     db.to_display_date(r["data_agendada"]),   # DD/MM/AAAA
                                     r["hora_agendada"] or "", r["prioridade"] or "",
                                     r["status"] or ""),
                             tags=(cores.tag_agendamento(r["data_agendada"], r["status"]),))

    def _sort_column(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        self._sort_rev = not self._sort_rev if self._sort_col == col else False
        self._sort_col = col
        items.sort(reverse=self._sort_rev)
        for index, (_, k) in enumerate(items):
            self.tree.move(k, "", index)

    def _get_selecionado_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione um agendamento na lista.")
            return None
        return int(sel[0])

    def _abrir_form_novo(self):
        FormAgendamento(self, titulo="Novo Agendamento", callback=self.carregar_agendamentos)

    def _abrir_detalhe(self):
        id_ = self._get_selecionado_id()
        if id_:
            FormAgendamento(self, titulo="Detalhes do Agendamento",
                            id_agendamento=id_, callback=self.carregar_agendamentos)

    def _editar_selecionado(self):
        id_ = self._get_selecionado_id()
        if id_:
            FormAgendamento(self, titulo="Editar Agendamento",
                            id_agendamento=id_, callback=self.carregar_agendamentos)

    def _concluir_selecionado(self):
        id_ = self._get_selecionado_id()
        if id_:
            ag = db.obter_agendamento(id_)
            if ag and ag["status"] == "Concluído":
                messagebox.showinfo("Aviso", "Este agendamento já está concluído.")
                return
            FormConclusao(self, id_agendamento=id_, callback=self.carregar_agendamentos)

    def _excluir_selecionado(self):
        id_ = self._get_selecionado_id()
        if id_:
            ag = db.obter_agendamento(id_)
            titulo = ag["titulo"] if ag else f"ID {id_}"
            if messagebox.askyesno("Confirmar Exclusão",
                                   f"Excluir o agendamento:\n\"{titulo}\"?\n\nEsta ação não pode ser desfeita."):
                db.excluir_agendamento(id_)
                self.carregar_agendamentos()


# ══════════════════════════════════════════════════════════════════════════════
#  Formulário de Agendamento
#  CORREÇÃO: botões fora do CTkScrollableFrame (sempre visíveis)
# ══════════════════════════════════════════════════════════════════════════════

class FormAgendamento(ctk.CTkToplevel):
    def __init__(self, master, titulo="Agendamento", id_agendamento=None, callback=None):
        super().__init__(master)
        self.title(titulo)
        self.geometry("600x580")
        self.minsize(560, 500)
        self.id_agendamento = id_agendamento
        self.callback = callback
        self._salvando = False
        self._build_form()
        if id_agendamento:
            self._carregar_dados()
        cores.preparar_modal(self, master, focus_widget=self.e_titulo)

    def _build_form(self):
        # ── Barra de botões FIXADA na parte inferior (fora do scroll) ─────────
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(side="bottom", fill="x", padx=16, pady=(4, 12))
        self.btn_salvar = ctk.CTkButton(btns, text="💾  Salvar", command=self._salvar, width=130)
        self.btn_salvar.pack(side="right", padx=(6, 0))
        ctk.CTkButton(btns, text="Cancelar", fg_color="gray40",
                      command=lambda: cores.fechar_modal(self), width=100).pack(side="right")

        # Divisor
        ctk.CTkFrame(self, height=1, fg_color="gray30").pack(
            side="bottom", fill="x", padx=16)

        # ── Área rolável com os campos ─────────────────────────────────────────
        frame = ctk.CTkScrollableFrame(self)
        frame.pack(fill="both", expand=True, padx=16, pady=(16, 4))

        def row(label, widget_fn, **kw):
            ctk.CTkLabel(frame, text=label, anchor="w").pack(fill="x", pady=(8, 2))
            w = widget_fn(frame, **kw)
            w.pack(fill="x")
            return w

        self.e_titulo       = row("Título *",        ctk.CTkEntry,
                                  placeholder_text="Ex: Troca de HD no Setor de RH")
        self.e_responsavel  = row("Responsável",     ctk.CTkEntry,
                                  placeholder_text="Nome do técnico")
        self.e_setor        = row("Setor / Local",   ctk.CTkEntry,
                                  placeholder_text="Ex: Secretaria de Educação")

        # Data e hora na mesma linha
        ctk.CTkLabel(frame, text="Data Agendada *", anchor="w").pack(fill="x", pady=(8, 2))
        dh = ctk.CTkFrame(frame, fg_color="transparent")
        dh.pack(fill="x")
        self.e_data = ctk.CTkEntry(dh, placeholder_text="DD/MM/AAAA", width=130)
        self.e_data.pack(side="left", padx=(0, 8))
        self.e_data.insert(0, date.today().strftime("%d/%m/%Y"))   # formato BR
        ctk.CTkLabel(dh, text="Hora:").pack(side="left", padx=(0, 4))
        self.e_hora = ctk.CTkEntry(dh, placeholder_text="HH:MM", width=80)
        self.e_hora.pack(side="left")

        ctk.CTkLabel(frame, text="Prioridade", anchor="w").pack(fill="x", pady=(8, 2))
        self.combo_prio = ctk.CTkComboBox(frame,
                           values=["Baixa", "Normal", "Alta", "Urgente"])
        self.combo_prio.set("Normal")
        self.combo_prio.pack(fill="x")

        if self.id_agendamento:
            ctk.CTkLabel(frame, text="Status", anchor="w").pack(fill="x", pady=(8, 2))
            self.combo_status = ctk.CTkComboBox(frame,
                                 values=["Pendente", "Em andamento", "Concluído", "Cancelado"])
            self.combo_status.set("Pendente")
            self.combo_status.pack(fill="x")
        else:
            self.combo_status = None

        self.e_descricao = row("Descrição", ctk.CTkTextbox, height=80)
        self.e_obs       = row("Observações", ctk.CTkTextbox, height=60)

    def _carregar_dados(self):
        ag = db.obter_agendamento(self.id_agendamento)
        if not ag:
            return

        def _set(w, val):
            if isinstance(w, ctk.CTkTextbox):
                w.delete("0.0", "end")
                if val: w.insert("0.0", str(val))
            elif isinstance(w, ctk.CTkComboBox):
                if val: w.set(str(val))
            else:
                w.delete(0, "end")
                if val is not None: w.insert(0, str(val))

        _set(self.e_titulo,      ag["titulo"])
        _set(self.e_responsavel, ag["responsavel"])
        _set(self.e_setor,       ag["setor"])
        # Converte data do banco (AAAA-MM-DD) para exibição (DD/MM/AAAA)
        _set(self.e_data,        db.to_display_date(ag["data_agendada"]))
        _set(self.e_hora,        ag["hora_agendada"])
        _set(self.combo_prio,    ag["prioridade"])
        if self.combo_status:
            _set(self.combo_status, ag["status"])
        _set(self.e_descricao,   ag["descricao"])
        _set(self.e_obs,         ag["observacoes"])

    def _salvar(self):
        if self._salvando:
            return
        titulo = self.e_titulo.get().strip()
        if not titulo:
            cores.erro_modal(self, "Erro", "O campo Título é obrigatório.")
            return
        data_display = self.e_data.get().strip()
        if not data_display:
            cores.erro_modal(self, "Erro", "A Data Agendada é obrigatória.")
            return
        # Valida formato DD/MM/AAAA
        try:
            datetime.strptime(data_display, "%d/%m/%Y")
        except ValueError:
            cores.erro_modal(self, "Erro", "Data inválida. Use o formato DD/MM/AAAA.")
            return

        def _get_text(w):
            if isinstance(w, ctk.CTkTextbox):
                return w.get("0.0", "end").strip()
            return w.get().strip()

        # data_agendada é passada em DD/MM/AAAA — database.py converte para AAAA-MM-DD
        kwargs = dict(
            titulo=titulo,
            descricao=_get_text(self.e_descricao),
            responsavel=self.e_responsavel.get().strip(),
            setor=self.e_setor.get().strip(),
            data_agendada=data_display,
            hora_agendada=self.e_hora.get().strip(),
            prioridade=self.combo_prio.get(),
            observacoes=_get_text(self.e_obs),
        )

        self._salvando = True
        self.btn_salvar.configure(state="disabled")
        try:
            if self.id_agendamento:
                status = self.combo_status.get() if self.combo_status else "Pendente"
                db.atualizar_agendamento(self.id_agendamento, status=status, **kwargs)
                msg = "Agendamento atualizado com sucesso!"
            else:
                db.criar_agendamento(**kwargs)
                msg = "Agendamento criado com sucesso!"
        except Exception as e:
            self._salvando = False
            self.btn_salvar.configure(state="normal")
            cores.erro_modal(self, "Erro ao salvar", f"Não foi possível salvar o agendamento:\n{e}")
            return

        cores.concluir_modal(self, self.callback, "Sucesso", msg)


# ══════════════════════════════════════════════════════════════════════════════
#  Formulário de Conclusão
# ══════════════════════════════════════════════════════════════════════════════

class FormConclusao(ctk.CTkToplevel):
    def __init__(self, master, id_agendamento, callback=None):
        super().__init__(master)
        self.title("Concluir Serviço")
        self.geometry("520x420")
        self.minsize(480, 380)
        self.id_agendamento = id_agendamento
        self.callback = callback
        self._confirmando = False

        ag = db.obter_agendamento(id_agendamento)
        ctk.CTkLabel(self,
                     text=f"Concluindo: {ag['titulo'] if ag else ''}",
                     font=ctk.CTkFont(weight="bold"),
                     wraplength=480).pack(padx=16, pady=(16, 4))

        # ── Botões FIXADOS na parte inferior ───────────────────────────────────
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(side="bottom", fill="x", padx=16, pady=(4, 14))
        self.btn_confirmar = ctk.CTkButton(btns, text="✅  Confirmar Conclusão", fg_color="#198754",
                                           command=self._confirmar, width=200)
        self.btn_confirmar.pack(side="right", padx=(6, 0))
        ctk.CTkButton(btns, text="Cancelar", fg_color="gray40",
                      command=lambda: cores.fechar_modal(self), width=100).pack(side="right")

        ctk.CTkFrame(self, height=1, fg_color="gray30").pack(
            side="bottom", fill="x", padx=16)

        # ── Campos ────────────────────────────────────────────────────────────
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=16, pady=(8, 4))

        ctk.CTkLabel(frame, text="Solução / O que foi feito:", anchor="w").pack(fill="x")
        self.e_solucao = ctk.CTkTextbox(frame, height=110)
        self.e_solucao.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(frame, text="Tempo gasto (minutos):", anchor="w").pack(fill="x")
        self.e_tempo = ctk.CTkEntry(frame, placeholder_text="Ex: 45")
        self.e_tempo.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(frame, text="Observações:", anchor="w").pack(fill="x")
        self.e_obs = ctk.CTkTextbox(frame, height=70)
        self.e_obs.pack(fill="x", pady=(4, 4))

        cores.preparar_modal(self, master, focus_widget=self.e_solucao)

    def _confirmar(self):
        if self._confirmando:
            return
        solucao = self.e_solucao.get("0.0", "end").strip()
        obs     = self.e_obs.get("0.0", "end").strip()
        tempo_str = self.e_tempo.get().strip()
        if tempo_str and not tempo_str.isdigit():
            cores.erro_modal(self, "Erro", "Tempo gasto deve ser um número inteiro de minutos.")
            return
        tempo = int(tempo_str) if tempo_str else None
        self._confirmando = True
        self.btn_confirmar.configure(state="disabled")
        try:
            db.concluir_agendamento(self.id_agendamento, solucao, tempo, obs)
        except Exception as e:
            self._confirmando = False
            self.btn_confirmar.configure(state="normal")
            cores.erro_modal(self, "Erro ao concluir", f"Não foi possível concluir o serviço:\n{e}")
            return
        cores.concluir_modal(self, self.callback, "Sucesso",
                             "Serviço concluído e registrado no histórico!")
