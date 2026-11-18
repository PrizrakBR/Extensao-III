"""
Módulo de Estoque de Peças — v1.1
Prefeitura de Papanduva - SC
CORREÇÃO: botões fora do CTkScrollableFrame (sempre visíveis)
"""

import customtkinter as ctk
from tkinter import messagebox, ttk
import database as db
import cores

class EstoqueFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self._build_ui()
        self.carregar_estoque()

    def _build_ui(self):
        # ── Cabeçalho ─────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(header, text="📦  Estoque de Peças",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="＋  Nova Peça", width=160,
                      command=self._abrir_form_novo).pack(side="right")

        # ── Filtros ────────────────────────────────────────────────────────────
        filtros = ctk.CTkFrame(self, corner_radius=8)
        filtros.pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkLabel(filtros, text="Buscar:").pack(side="left", padx=(12, 4), pady=8)
        self.entry_busca = ctk.CTkEntry(filtros,
                            placeholder_text="Nome / Fabricante / Modelo", width=260)
        self.entry_busca.pack(side="left", padx=4, pady=8)
        self.entry_busca.bind("<Return>", lambda _: self.carregar_estoque())
        ctk.CTkLabel(filtros, text="Categoria:").pack(side="left", padx=(12, 4))
        self.combo_cat = ctk.CTkComboBox(filtros, values=["Todas"], width=160,
                                          command=lambda _: self.carregar_estoque())
        self.combo_cat.set("Todas")
        self.combo_cat.pack(side="left", padx=4)
        self.var_min = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(filtros, text="Abaixo do mínimo", variable=self.var_min,
                        command=self.carregar_estoque).pack(side="left", padx=12)
        ctk.CTkButton(filtros, text="🔍", width=36,
                      command=self.carregar_estoque).pack(side="left", padx=4)
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
        cols = ("ID", "Nome", "Categoria", "Fabricante", "Modelo",
                "Qtd.", "Mín.", "Localização", "Unid.")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        widths = (40, 220, 120, 120, 120, 50, 50, 130, 50)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_column(c))
            self.tree.column(col, width=w, anchor="w")
        cores.configurar_tags_estoque(self.tree)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        self.tree.bind("<Double-1>", lambda _: self._editar_selecionado())

        # ── Barra de ações ─────────────────────────────────────────────────────
        acoes = ctk.CTkFrame(self, fg_color="transparent")
        acoes.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(acoes, text="✏️  Editar", width=130,
                      command=self._editar_selecionado).pack(side="left", padx=(0, 6))
        ctk.CTkButton(acoes, text="📥  Entrada", width=130, fg_color="#198754",
                      command=self._movimentar_entrada).pack(side="left", padx=6)
        ctk.CTkButton(acoes, text="📤  Saída", width=130, fg_color="#fd7e14",
                      command=self._movimentar_saida).pack(side="left", padx=6)
        ctk.CTkButton(acoes, text="🗑  Excluir", width=130, fg_color="#dc3545",
                      command=self._excluir_selecionado).pack(side="left", padx=6)
        ctk.CTkButton(acoes, text="🔄  Atualizar", width=130, fg_color="gray40",
                      command=self.carregar_estoque).pack(side="right")
        cores.legenda(acoes, [(cores.VERMELHO[0], "Zerado"),
                              (cores.LARANJA[0], "Abaixo do mínimo")]
                      ).pack(side="right", padx=12)

        self._sort_col = None
        self._sort_rev = False

    def _limpar_filtros(self):
        self.entry_busca.delete(0, "end")
        self.combo_cat.set("Todas")
        self.var_min.set(False)
        self.carregar_estoque()

    def _atualizar_categorias(self):
        cats = ["Todas"] + db.listar_categorias()
        self.combo_cat.configure(values=cats)

    def carregar_estoque(self, *_):
        self._atualizar_categorias()
        busca = self.entry_busca.get().strip() or None
        cat   = self.combo_cat.get()
        rows  = db.listar_estoque(busca=busca, categoria=cat,
                                   apenas_abaixo_minimo=self.var_min.get())
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            tag = cores.tag_estoque(r["quantidade"], r["quantidade_min"])
            self.tree.insert("", "end", iid=str(r["id"]),
                             values=(r["id"], r["nome"],
                                     r["categoria"] or "", r["fabricante"] or "",
                                     r["modelo"] or "", r["quantidade"],
                                     r["quantidade_min"], r["localizacao"] or "",
                                     r["unidade"] or "un"),
                             tags=(tag,))

    def _sort_column(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        self._sort_rev = not self._sort_rev if self._sort_col == col else False
        self._sort_col = col
        try:
            items.sort(key=lambda x: float(x[0]) if x[0].replace('.','').isdigit() else x[0],
                       reverse=self._sort_rev)
        except Exception:
            items.sort(reverse=self._sort_rev)
        for index, (_, k) in enumerate(items):
            self.tree.move(k, "", index)

    def _get_selecionado_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma peça na lista.")
            return None
        return int(sel[0])

    def _abrir_form_novo(self):
        FormPeca(self, titulo="Nova Peça", callback=self.carregar_estoque)

    def _editar_selecionado(self):
        id_ = self._get_selecionado_id()
        if id_:
            FormPeca(self, titulo="Editar Peça", id_peca=id_, callback=self.carregar_estoque)

    def _movimentar_entrada(self):
        id_ = self._get_selecionado_id()
        if id_:
            FormMovimentacao(self, id_peca=id_, tipo="entrada", callback=self.carregar_estoque)

    def _movimentar_saida(self):
        id_ = self._get_selecionado_id()
        if id_:
            FormMovimentacao(self, id_peca=id_, tipo="saida", callback=self.carregar_estoque)

    def _excluir_selecionado(self):
        id_ = self._get_selecionado_id()
        if id_:
            peca = db.obter_peca(id_)
            nome = peca["nome"] if peca else f"ID {id_}"
            if messagebox.askyesno("Confirmar Exclusão",
                                   f"Excluir a peça \"{nome}\" e todo seu histórico?\n\nEsta ação não pode ser desfeita."):
                db.excluir_peca(id_)
                self.carregar_estoque()


# ══════════════════════════════════════════════════════════════════════════════
#  Formulário de Peça
#  CORREÇÃO: botões fora do CTkScrollableFrame (sempre visíveis)
# ══════════════════════════════════════════════════════════════════════════════

class FormPeca(ctk.CTkToplevel):
    def __init__(self, master, titulo="Peça", id_peca=None, callback=None):
        super().__init__(master)
        self.title(titulo)
        self.geometry("560x640")
        self.minsize(520, 520)
        self.id_peca = id_peca
        self.callback = callback
        self._salvando = False
        self._codigo_atual = ""
        self._build_form()
        if id_peca:
            self._carregar_dados()
        cores.preparar_modal(self, master, focus_widget=self.e_nome)

    def _build_form(self):
        # ── Botões FIXADOS na parte inferior (fora do scroll) ──────────────────
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(side="bottom", fill="x", padx=16, pady=(4, 12))
        self.btn_salvar = ctk.CTkButton(btns, text="💾  Salvar", command=self._salvar, width=130)
        self.btn_salvar.pack(side="right", padx=(6, 0))
        ctk.CTkButton(btns, text="Cancelar", fg_color="gray40",
                      command=lambda: cores.fechar_modal(self), width=100).pack(side="right")

        ctk.CTkFrame(self, height=1, fg_color="gray30").pack(
            side="bottom", fill="x", padx=16)

        # ── Área rolável com os campos ─────────────────────────────────────────
        frame = ctk.CTkScrollableFrame(self)
        frame.pack(fill="both", expand=True, padx=16, pady=(16, 4))

        def lbl(text):
            ctk.CTkLabel(frame, text=text, anchor="w").pack(fill="x", pady=(8, 2))
        def entry(**kw):
            e = ctk.CTkEntry(frame, **kw)
            e.pack(fill="x")
            return e

        lbl("Nome *")
        self.e_nome = entry(placeholder_text="Ex: HD SATA 500GB")
        lbl("Categoria")
        self.e_categoria = entry(placeholder_text="Ex: Armazenamento, Memória, Cabos...")
        lbl("Fabricante")
        self.e_fabricante = entry(placeholder_text="Ex: Seagate")
        lbl("Modelo")
        self.e_modelo = entry(placeholder_text="Ex: Barracuda ST500DM002")

        lbl("Quantidade inicial")
        qf = ctk.CTkFrame(frame, fg_color="transparent")
        qf.pack(fill="x")
        self.e_qtd = ctk.CTkEntry(qf, placeholder_text="0", width=80)
        self.e_qtd.pack(side="left", padx=(0, 8))
        ctk.CTkLabel(qf, text="Unidade:").pack(side="left", padx=(0, 4))
        self.e_unidade = ctk.CTkEntry(qf, placeholder_text="un", width=80)
        self.e_unidade.pack(side="left")

        lbl("Quantidade mínima (alerta)")
        self.e_qtd_min = ctk.CTkEntry(frame, placeholder_text="1", width=80)
        self.e_qtd_min.pack(anchor="w")

        lbl("Localização no estoque")
        self.e_local = entry(placeholder_text="Ex: Prateleira A, Gaveta 3")
        lbl("Responsável pelo cadastro/alteração (opcional)")
        self.e_resp = entry(placeholder_text="Nome do técnico")
        lbl("Descrição / Observações")
        self.e_obs = ctk.CTkTextbox(frame, height=80)
        self.e_obs.pack(fill="x")

    def _carregar_dados(self):
        p = db.obter_peca(self.id_peca)
        if not p: return

        def _s(w, v):
            if isinstance(w, ctk.CTkTextbox):
                w.delete("0.0", "end")
                if v: w.insert("0.0", str(v))
            else:
                w.delete(0, "end")
                if v is not None: w.insert(0, str(v))

        self._codigo_atual = p["codigo"] or ""
        _s(self.e_nome,      p["nome"])
        _s(self.e_categoria, p["categoria"])
        _s(self.e_fabricante,p["fabricante"])
        _s(self.e_modelo,    p["modelo"])
        _s(self.e_qtd,       p["quantidade"])
        _s(self.e_qtd_min,   p["quantidade_min"])
        _s(self.e_local,     p["localizacao"])
        _s(self.e_unidade,   p["unidade"])
        _s(self.e_obs,       p["observacoes"])

        # Desabilita qtd se editando (use movimentações para alterar)
        if self.id_peca:
            self.e_qtd.configure(state="disabled")

    def _salvar(self):
        if self._salvando:
            return
        nome = self.e_nome.get().strip()
        if not nome:
            cores.erro_modal(self, "Erro", "O campo Nome é obrigatório.")
            return

        qtd_str = self.e_qtd.get().strip()
        if not self.id_peca:
            if not qtd_str:
                qtd = 0
            elif qtd_str.isdigit():
                qtd = int(qtd_str)
            else:
                cores.erro_modal(self, "Erro", "Quantidade inicial deve ser um número inteiro (0 ou maior).")
                return
        else:
            qtd = 0

        qtd_min_str = self.e_qtd_min.get().strip()
        if not qtd_min_str:
            qtd_min = 1
        elif qtd_min_str.isdigit():
            qtd_min = int(qtd_min_str)
        else:
            cores.erro_modal(self, "Erro", "Quantidade mínima deve ser um número inteiro (0 ou maior).")
            return

        obs = self.e_obs.get("0.0", "end").strip()

        self._salvando = True
        self.btn_salvar.configure(state="disabled")
        try:
            if self.id_peca:
                db.atualizar_peca(
                    self.id_peca,
                    codigo=self._codigo_atual,
                    nome=nome,
                    categoria=self.e_categoria.get().strip(),
                    descricao=obs,
                    fabricante=self.e_fabricante.get().strip(),
                    modelo=self.e_modelo.get().strip(),
                    quantidade_min=qtd_min,
                    localizacao=self.e_local.get().strip(),
                    unidade=self.e_unidade.get().strip() or "un",
                    observacoes=obs,
                    responsavel=self.e_resp.get().strip(),
                )
                msg = "Peça atualizada com sucesso!"
            else:
                db.criar_peca(
                    codigo="",
                    nome=nome,
                    categoria=self.e_categoria.get().strip(),
                    descricao=obs,
                    fabricante=self.e_fabricante.get().strip(),
                    modelo=self.e_modelo.get().strip(),
                    quantidade=qtd,
                    quantidade_min=qtd_min,
                    localizacao=self.e_local.get().strip(),
                    unidade=self.e_unidade.get().strip() or "un",
                    observacoes=obs,
                    responsavel=self.e_resp.get().strip(),
                )
                msg = "Peça cadastrada com sucesso!"
        except Exception as e:
            self._salvando = False
            self.btn_salvar.configure(state="normal")
            cores.erro_modal(self, "Erro ao salvar", f"Não foi possível salvar a peça:\n{e}")
            return

        cores.concluir_modal(self, self.callback, "Sucesso", msg)


# ══════════════════════════════════════════════════════════════════════════════
#  Formulário de Movimentação (Entrada / Saída)
# ══════════════════════════════════════════════════════════════════════════════

class FormMovimentacao(ctk.CTkToplevel):
    def __init__(self, master, id_peca, tipo="saida", callback=None):
        super().__init__(master)
        self.id_peca  = id_peca
        self.tipo     = tipo
        self.callback = callback
        self._confirmando = False
        peca = db.obter_peca(id_peca)
        self.peca = peca

        tipo_label = "Entrada de Estoque" if tipo == "entrada" else "Saída de Estoque"
        self.title(tipo_label)
        self.geometry("480x440")
        self.minsize(440, 400)
        self._build_form(peca, tipo_label)
        cores.preparar_modal(self, master, focus_widget=self.e_qtd)

    def _build_form(self, peca, tipo_label):
        cor = "#198754" if self.tipo == "entrada" else "#fd7e14"

        # ── Botões FIXADOS na parte inferior ──────────────────────────────────
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(side="bottom", fill="x", padx=20, pady=(4, 14))
        self.btn_confirmar = ctk.CTkButton(btns, text="✔  Confirmar", fg_color=cor,
                                           command=self._confirmar, width=150)
        self.btn_confirmar.pack(side="right", padx=(6, 0))
        ctk.CTkButton(btns, text="Cancelar", fg_color="gray40",
                      command=lambda: cores.fechar_modal(self), width=100).pack(side="right")

        ctk.CTkFrame(self, height=1, fg_color="gray30").pack(
            side="bottom", fill="x", padx=16)

        # ── Campos (frame simples para evitar bloqueios de scroll em modal) ───
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(frame, text=tipo_label,
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=cor).pack(anchor="w", pady=(0, 8))

        if peca:
            info = f"Peça: {peca['nome']}"
            info += f"\nEstoque atual: {peca['quantidade']} {peca['unidade'] or 'un'}"
            ctk.CTkLabel(frame, text=info, justify="left").pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(frame, text="Quantidade *", anchor="w").pack(fill="x")
        self.e_qtd = ctk.CTkEntry(frame, placeholder_text="Ex: 2")
        self.e_qtd.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(frame, text="Motivo / Destino", anchor="w").pack(fill="x")
        self.e_motivo = ctk.CTkEntry(frame, placeholder_text="Ex: Troca no Setor de Administração")
        self.e_motivo.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(frame, text="Responsável", anchor="w").pack(fill="x")
        self.e_resp = ctk.CTkEntry(frame, placeholder_text="Nome do técnico")
        self.e_resp.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(frame, text="Observações", anchor="w").pack(fill="x")
        self.e_obs = ctk.CTkTextbox(frame, height=65)
        self.e_obs.pack(fill="x", pady=(4, 4))

    def _confirmar(self):
        if self._confirmando:
            return
        qtd_str = self.e_qtd.get().strip()
        if not qtd_str.isdigit() or int(qtd_str) <= 0:
            cores.erro_modal(self, "Erro",
                             "Informe uma quantidade válida (número inteiro positivo).")
            return
        qtd = int(qtd_str)
        self._confirmando = True
        self.btn_confirmar.configure(state="disabled")
        try:
            novo_saldo = db.movimentar_estoque(
                peca_id=self.id_peca,
                tipo=self.tipo,
                quantidade=qtd,
                motivo=self.e_motivo.get().strip(),
                responsavel=self.e_resp.get().strip(),
                observacoes=self.e_obs.get("0.0", "end").strip(),
            )
        except ValueError as e:
            self._confirmando = False
            self.btn_confirmar.configure(state="normal")
            cores.erro_modal(self, "Erro", str(e))
            return
        except Exception as e:
            self._confirmando = False
            self.btn_confirmar.configure(state="normal")
            cores.erro_modal(self, "Erro ao registrar",
                             f"Não foi possível registrar a movimentação:\n{e}")
            return

        tipo_msg = "entrada" if self.tipo == "entrada" else "saída"
        cores.concluir_modal(
            self, self.callback, "Sucesso",
            f"Registrada {tipo_msg} de {qtd} unidade(s).\nSaldo atual: {novo_saldo}"
        )
