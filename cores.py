"""
Regras e cores de destaque compartilhadas por Agendamentos, Estoque e Painel.

  Agendamento ATRASADO  -> linha vermelha  (data já passou e não foi concluído)
  Estoque ZERADO        -> linha vermelha  (quantidade = 0)
  Estoque em ALERTA     -> linha laranja   (0 < quantidade <= mínimo)
"""

from datetime import date

# (fundo, texto)
VERMELHO = ("#dc3545", "#ffffff")
LARANJA = ("#ffa94d", "#000000")

# Status em que um agendamento ainda está "em aberto" (pode ficar atrasado).
# Concluído e Cancelado nunca ficam atrasados.
STATUS_EM_ABERTO = ("Pendente", "Em andamento")


def agendamento_atrasado(data_iso, status):
    """True se a data agendada (AAAA-MM-DD) já passou e o serviço segue em aberto."""
    if not data_iso or status not in STATUS_EM_ABERTO:
        return False
    return str(data_iso)[:10] < date.today().isoformat()


def tag_agendamento(data_iso, status):
    """Tag da linha: 'atrasado' ou o próprio status."""
    return "atrasado" if agendamento_atrasado(data_iso, status) else (status or "Pendente")


def tag_estoque(quantidade, minimo):
    """'zerado' (vermelho), 'alerta' (laranja) ou 'ok'."""
    q = quantidade or 0
    if q <= 0:
        return "zerado"
    if q <= (minimo or 0):
        return "alerta"
    return "ok"


def legenda(parent, itens):
    """Legenda com quadradinhos coloridos reais (emoji de cor não renderiza no Tk/Windows).
    itens: lista de (cor_de_fundo, texto). Retorna um frame (o chamador faz o pack)."""
    import customtkinter as ctk
    f = ctk.CTkFrame(parent, fg_color="transparent")
    for cor, texto in itens:
        ctk.CTkFrame(f, width=14, height=14, corner_radius=3, fg_color=cor).pack(side="left", padx=(10, 4))
        ctk.CTkLabel(f, text=texto, font=ctk.CTkFont(size=11), text_color="gray40").pack(side="left")
    return f


def configurar_tags_agendamento(tree):
    tree.tag_configure("Pendente",     background="#fff3cd", foreground="#000000")
    tree.tag_configure("Em andamento", background="#cfe2ff", foreground="#000000")
    tree.tag_configure("Concluído",    background="#d1e7dd", foreground="#000000")
    tree.tag_configure("Cancelado",    background="#e2e3e5", foreground="#000000")
    tree.tag_configure("atrasado",     background=VERMELHO[0], foreground=VERMELHO[1])


def configurar_tags_estoque(tree):
    tree.tag_configure("ok",     background="#d1e7dd", foreground="#000000")
    tree.tag_configure("alerta", background=LARANJA[0], foreground=LARANJA[1])
    tree.tag_configure("zerado", background=VERMELHO[0], foreground=VERMELHO[1])


def configurar_tags_historico_estoque(tree):
    tree.tag_configure("Entrada",  background="#d1e7dd", foreground="#000000")
    tree.tag_configure("Saída",    background="#fff3cd", foreground="#000000")
    tree.tag_configure("Cadastro", background="#cfe2ff", foreground="#000000")
    tree.tag_configure("Edição",   background="#e2d9f3", foreground="#000000")
    tree.tag_configure("Exclusão", background="#f8d7da", foreground="#000000")


def configurar_tags_historico_agendamentos(tree):
    tree.tag_configure("Conclusão",            background="#d1e7dd", foreground="#000000")
    tree.tag_configure("Conclusão Desmarcada", background="#fff3cd", foreground="#000000")
    tree.tag_configure("Cadastro",             background="#cfe2ff", foreground="#000000")
    tree.tag_configure("Edição",               background="#e2d9f3", foreground="#000000")
    tree.tag_configure("Exclusão",             background="#f8d7da", foreground="#000000")


def preparar_modal(win, master, focus_widget=None):
    """Configura janela modal de forma segura no Windows + CustomTkinter.
    Evita chamar grab_set() enquanto a janela ainda está em withdraw()."""
    import os
    import sys

    topo = master.winfo_toplevel()
    win._modal_topo = topo
    try:
        win.transient(topo)
    except Exception:
        pass
    win.protocol("WM_DELETE_WINDOW", lambda: fechar_modal(win))

    def _ativar(tentativas=0):
        try:
            if not win.winfo_exists():
                return
            if win.state() == "withdrawn" and tentativas < 20:
                win.after(20, lambda: _ativar(tentativas + 1))
                return
            win.lift()
            win.grab_set()
            if focus_widget is not None and focus_widget.winfo_exists():
                focus_widget.focus_set()
            else:
                win.focus_force()
        except Exception:
            pass

    def _icone():
        try:
            if not win.winfo_exists():
                return
            base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
            ico = os.path.join(base, "icone.ico")
            if os.path.isfile(ico):
                win.iconbitmap(ico)
        except Exception:
            pass

    win.after(40, _ativar)
    win.after(230, _icone)


def fechar_modal(win):
    """Libera o grab antes de destruir a janela modal e devolve o foco."""
    topo = getattr(win, "_modal_topo", None)
    try:
        win.grab_release()
    except Exception:
        pass
    try:
        win.destroy()
    except Exception:
        pass
    if topo is not None:
        try:
            if topo.winfo_exists():
                topo.lift()
                topo.focus_force()
        except Exception:
            pass


def erro_modal(win, titulo, mensagem):
    """Exibe erro sem risco de o diálogo ficar preso atrás ou com grab bloqueado."""
    from tkinter import messagebox
    try:
        win.grab_release()
    except Exception:
        pass
    messagebox.showerror(titulo, mensagem, parent=win)
    try:
        if win.winfo_exists():
            win.lift()
            win.focus_force()
            win.grab_set()
    except Exception:
        pass


def concluir_modal(win, callback, titulo, mensagem):
    """Atualiza a tela pai, fecha o modal e exibe o aviso na janela principal."""
    from tkinter import messagebox
    topo = getattr(win, "_modal_topo", None) or win.master.winfo_toplevel()
    if callback:
        callback()
    fechar_modal(win)
    messagebox.showinfo(titulo, mensagem, parent=topo)
