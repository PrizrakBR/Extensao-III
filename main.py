"""
Aplicação Principal - Sistema de Controle de Estoque e Agendamento de TI
Prefeitura de Papanduva - SC

Autor: Gustavo Zattar (Estagiário de TI)
Versão: 1.5
"""

import os
import sys
import traceback
from datetime import date, datetime

import customtkinter as ctk
from tkinter import messagebox, filedialog
import database as db

VERSAO = "1.5"

# Importa as telas
from dashboard    import DashboardFrame
from agendamentos import AgendamentosFrame
from estoque      import EstoqueFrame
from historico    import HistoricoFrame


# ══════════════════════════════════════════════════════════════════════════════
#  Configuração visual global
# ══════════════════════════════════════════════════════════════════════════════
ctk.set_appearance_mode("system")       # "light", "dark" ou "system"
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TI Papanduva — Estoque & Agendamentos")
        self.geometry("1150x720")
        self.minsize(900, 600)
        self._definir_icone()

        # Inicializa o banco
        db.inicializar_banco()
        self.report_callback_exception = self._tratar_excecao

        self._build_layout()
        self._navegar("dashboard")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _tratar_excecao(self, exc_type, exc_val, exc_tb):
        """Evita falhas silenciosas no .exe sem console, registrando em erros.log."""
        detalhe = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
        try:
            log_path = os.path.join(db.PASTA_DADOS, "erros.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}]\n{detalhe}\n")
        except Exception:
            pass
        try:
            messagebox.showerror(
                "Erro inesperado",
                f"Ocorreu um erro:\n{exc_val}\n\nDetalhes salvos em erros.log.",
                parent=self,
            )
        except Exception:
            pass

    def _build_layout(self):
        # ── Sidebar ────────────────────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo / cabeçalho da sidebar
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color=["#1a1a2e", "#0d0d1a"],
                                   corner_radius=0, height=80)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)
        ctk.CTkLabel(logo_frame, text="🏛️ TI Papanduva",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="white").pack(expand=True)

        # Separador
        ctk.CTkFrame(self.sidebar, height=1, fg_color="gray30").pack(fill="x")

        # Botões de navegação
        nav_items = [
            ("🏠  Painel",          "dashboard"),
            ("📅  Agendamentos",    "agendamentos"),
            ("📦  Estoque",         "estoque"),
            ("📋  Histórico",       "historico"),
        ]
        self.nav_buttons = {}
        for label, key in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, text=label, anchor="w",
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                text_color=["gray20", "gray80"],
                hover_color=["gray85", "gray25"],
                height=44,
                corner_radius=6,
                command=lambda k=key: self._navegar(k)
            )
            btn.pack(fill="x", padx=8, pady=3)
            self.nav_buttons[key] = btn

        # Rodapé da sidebar
        ctk.CTkFrame(self.sidebar, height=1, fg_color="gray30").pack(fill="x", side="bottom", pady=(0, 8))
        ctk.CTkLabel(self.sidebar, text=f"Versão {VERSAO}\nPapanduva - SC",
                     font=ctk.CTkFont(size=10),
                     text_color="gray50").pack(side="bottom", pady=4)

        # Botão de lançar (restaurar) backup — empacotado antes do "Fazer Backup"
        # para ficar logo ABAIXO dele (a barra empilha de baixo para cima).
        ctk.CTkButton(
            self.sidebar, text="📂  Lançar Backup", height=32,
            fg_color="#fd7e14", hover_color="#dd6b0c",
            command=self._lancar_backup
        ).pack(side="bottom", fill="x", padx=8, pady=4)

        # Botão de backup
        ctk.CTkButton(
            self.sidebar, text="💾  Fazer Backup", height=32,
            fg_color="#198754", hover_color="#146c43",
            command=self._fazer_backup
        ).pack(side="bottom", fill="x", padx=8, pady=4)

        # Botão de tema
        self.btn_tema = ctk.CTkButton(
            self.sidebar, text="🌙  Modo Escuro", height=32,
            fg_color="gray30", hover_color="gray40",
            command=self._toggle_tema
        )
        self.btn_tema.pack(side="bottom", fill="x", padx=8, pady=4)

        # ── Área de conteúdo ───────────────────────────────────────────────────
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=["#f0f4f8", "#1a1a2e"])
        self.content.pack(side="right", fill="both", expand=True)

        # Instancia as telas (lazy: só cria quando necessário)
        self._frames = {}
        self._aba_atual = None

    def _navegar(self, chave):
        if self._aba_atual == chave:
            return

        # Esconde frame atual
        if self._aba_atual and self._aba_atual in self._frames:
            self._frames[self._aba_atual].pack_forget()

        # Atualiza estilo dos botões (mantém azul no hover da aba ativa)
        for k, btn in self.nav_buttons.items():
            if k == chave:
                btn.configure(fg_color=["#1f6aa5", "#1f6aa5"],
                              hover_color=["#1f6aa5", "#1f6aa5"],
                              text_color="white")
            else:
                btn.configure(fg_color="transparent",
                              hover_color=["gray85", "gray25"],
                              text_color=["gray20", "gray80"])

        # Cria ou mostra o frame da aba
        if chave not in self._frames:
            self._frames[chave] = self._criar_frame(chave)

        self._frames[chave].pack(fill="both", expand=True)
        self._aba_atual = chave

        # Recarrega dados se o frame tiver método de atualização
        frame = self._frames[chave]
        if hasattr(frame, "atualizar"):
            frame.atualizar()
        elif hasattr(frame, "carregar_agendamentos"):
            frame.carregar_agendamentos()
        elif hasattr(frame, "carregar_estoque"):
            frame.carregar_estoque()

    def _criar_frame(self, chave):
        parent = self.content
        if chave == "dashboard":
            return DashboardFrame(parent, nav_callback=self._navegar,
                                   fg_color="transparent")
        elif chave == "agendamentos":
            return AgendamentosFrame(parent, fg_color="transparent")
        elif chave == "estoque":
            return EstoqueFrame(parent, fg_color="transparent")
        elif chave == "historico":
            return HistoricoFrame(parent, fg_color="transparent")

    def _toggle_tema(self):
        modo_atual = ctk.get_appearance_mode()
        if modo_atual == "Dark":
            ctk.set_appearance_mode("light")
            self.btn_tema.configure(text="🌙  Modo Escuro")
        else:
            ctk.set_appearance_mode("dark")
            self.btn_tema.configure(text="☀️  Modo Claro")

    def _fazer_backup(self):
        nome = f"backup_estoque_ti_{date.today().strftime('%d-%m-%Y')}.db"
        destino = filedialog.asksaveasfilename(
            parent=self, title="Salvar backup do banco de dados",
            initialfile=nome, defaultextension=".db",
            filetypes=[("Banco de dados (*.db)", "*.db")])
        if not destino:
            return
        try:
            db.fazer_backup(destino)
            messagebox.showinfo("Backup", f"Backup salvo com sucesso em:\n{destino}", parent=self)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível fazer o backup:\n{e}", parent=self)

    def _definir_icone(self):
        try:
            base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
            ico = os.path.join(base, "icone.ico")
            if os.path.isfile(ico):
                self.iconbitmap(ico)
                # o CustomTkinter redefine o ícone ~200 ms após abrir; reaplica depois disso
                self.after(300, lambda: self.iconbitmap(ico))
        except Exception:
            pass

    def _lancar_backup(self):
        """Abre o Explorer para escolher um backup e o lança no sistema."""
        caminho = filedialog.askopenfilename(
            parent=self, title="Selecione o arquivo de backup a lançar",
            filetypes=[("Backup do sistema (*.db)", "*.db"), ("Todos os arquivos", "*.*")])
        if not caminho:
            return
        try:
            ag, hist, pecas, mov = db.validar_backup(caminho)
        except ValueError as e:
            messagebox.showerror("Backup inválido", str(e), parent=self)
            return
        if not messagebox.askyesno(
                "Confirmar lançamento do backup",
                f"Arquivo: {os.path.basename(caminho)}\n\n"
                f"Conteúdo do backup:\n"
                f"  • {ag} agendamento(s)\n"
                f"  • {hist} serviço(s) no histórico\n"
                f"  • {pecas} peça(s) em estoque\n"
                f"  • {mov} movimentação(ões) de estoque\n\n"
                "⚠️ TODOS os dados atuais serão SUBSTITUÍDOS pelos do backup.\n"
                "Uma cópia de segurança dos dados atuais será salva automaticamente.\n\n"
                "Deseja continuar?", parent=self):
            return
        try:
            copia, _ = db.restaurar_backup(caminho)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível lançar o backup:\n{e}\n\n"
                                         "Os dados atuais não foram alterados.", parent=self)
            return
        self._recarregar_telas()
        messagebox.showinfo("Backup lançado",
                            "Backup lançado com sucesso!\n\n"
                            f"Cópia de segurança dos dados anteriores:\n{copia}", parent=self)

    def _recarregar_telas(self):
        """Descarta as telas já abertas e recria a atual, lendo o banco restaurado."""
        atual = self._aba_atual or "dashboard"
        for f in self._frames.values():
            f.destroy()
        self._frames.clear()
        self._aba_atual = None
        self._navegar(atual)

    def _on_close(self):
        if messagebox.askokcancel("Sair", "Deseja fechar o sistema?"):
            self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  Ponto de entrada
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = App()
    app.mainloop()
