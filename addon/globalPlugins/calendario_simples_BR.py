# -*- coding: utf-8 -*-
import datetime
import calendar
import wx
import json
import os
import shutil
import addonHandler
import globalPluginHandler
import globalVars
import gui
import ui
import tones
import api
from logHandler import log
from scriptHandler import script

addonHandler.initTranslation()

# --- CONSTANTES E DADOS ---
DIAS_SEMANA = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
DIAS_ABREV = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

FERIADOS_FIXOS = {
    (1, 1): "Confraternização Universal",
    (21, 4): "Tiradentes",
    (1, 5): "Dia do Trabalho",
    (7, 9): "Independência do Brasil",
    (12, 10): "Nossa Senhora Aparecida",
    (2, 11): "Finados",
    (15, 11): "Proclamação da República",
    (20, 11): "Dia da Consciência Negra",
    (25, 12): "Natal",
}

# --- DEFINIÇÃO DO ARQUIVO DE NOTAS (PERSISTENTE) ---
ARQUIVO_NOTAS = os.path.join(globalVars.appArgs.configPath, "calendario_simples_notas.json")
ARQUIVO_NOTAS_LEGADO = os.path.join(os.path.dirname(__file__), "notas_calendario.json")


# --- FUNÇÕES AUXILIARES ---
def get_feriados_moveis(ano):
    """Calcula feriados móveis baseados na data da Páscoa."""
    a = ano % 19
    b = ano // 100
    c = ano % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1

    pascoa = datetime.date(ano, mes, dia)

    return {
        pascoa - datetime.timedelta(days=47): "Carnaval",
        pascoa - datetime.timedelta(days=2): "Sexta-feira Santa",
        pascoa: "Páscoa",
        pascoa + datetime.timedelta(days=60): "Corpus Christi",
    }


def get_fase_lua_nome(data_dt):
    """Calcula a fase da lua simplificada (Nova, Crescente, Cheia, Minguante)."""
    # Referência: Lua Nova em 6 de Janeiro de 2000
    lua_nova_ref = datetime.date(2000, 1, 6)
    ciclo_lunar = 29.530588853

    dias_passados = (data_dt - lua_nova_ref).days
    lunacao = dias_passados % ciclo_lunar

    indice = int((lunacao / ciclo_lunar) * 4) % 4

    fases = [
        "Lua Nova",
        "Lua Crescente",
        "Lua Cheia",
        "Lua Minguante",
    ]
    return fases[indice]


def formato_data_pt(dt):
    dia_semana = DIAS_SEMANA[dt.weekday()]
    mes = MESES[dt.month - 1]
    return "{} {} de {} de {}".format(dia_semana, dt.day, mes, dt.year)


def formato_dia_mes(dt):
    """Formato curto apenas com dia e mês para o intervalo."""
    mes = MESES[dt.month - 1]
    return "{} de {}".format(dt.day, mes)


def _end_modal_or_destroy(dlg, return_code=wx.ID_CANCEL):
    try:
        if hasattr(dlg, "IsModal") and dlg.IsModal():
            dlg.EndModal(return_code)
        else:
            dlg.Destroy()
    except Exception:
        try:
            dlg.Destroy()
        except Exception:
            pass


# --- CLASSES DE INTERFACE ---
class AjudaDialog(wx.Dialog):
    """Diálogo de ajuda acessível com navegação por setas."""

    def __init__(self, parent, content):
        super(AjudaDialog, self).__init__(parent, title="Ajuda do Calendário", size=(600, 450))

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.text_ctrl = wx.TextCtrl(
            panel,
            value=content,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_BESTWRAP | wx.TE_RICH,
        )
        vbox.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 10)

        btn_close = wx.Button(panel, wx.ID_OK, label="Fechar")
        vbox.Add(btn_close, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        panel.SetSizer(vbox)

        self.text_ctrl.SetFocus()
        self.text_ctrl.SetInsertionPoint(0)

        self.Bind(wx.EVT_CHAR_HOOK, self.onKey)

    def onKey(self, evt):
        if evt.GetKeyCode() == wx.WXK_ESCAPE:
            _end_modal_or_destroy(self, wx.ID_CANCEL)
        else:
            evt.Skip()


class ListaFeriadosDialog(wx.Dialog):
    def __init__(self, parent, ano, feriados_lista):
        super(ListaFeriadosDialog, self).__init__(parent, title="Feriados de {}".format(ano), size=(500, 400))
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        lista_txt = wx.ListBox(panel, choices=feriados_lista, style=wx.LB_SINGLE)
        sizer.Add(lista_txt, 1, wx.EXPAND | wx.ALL, 10)

        btn_fechar = wx.Button(panel, wx.ID_OK, label="Fechar")
        sizer.Add(btn_fechar, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        panel.SetSizer(sizer)
        lista_txt.SetFocus()

        self.Bind(wx.EVT_CHAR_HOOK, self.onKey)

    def onKey(self, evt):
        if evt.GetKeyCode() == wx.WXK_ESCAPE:
            _end_modal_or_destroy(self, wx.ID_CANCEL)
        else:
            evt.Skip()


class CalendarioFrame(wx.Frame):
    def __init__(self, parent=None):
        style = wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP
        super(CalendarioFrame, self).__init__(parent, title="Calendário Simples BR", size=(900, 700), style=style)

        self.today = datetime.date.today()
        self.currentDate = self.today
        self.dia_labels = []

        self.notas = self.carregar_notas()

        self.panel = wx.Panel(self, style=wx.WANTS_CHARS)
        self.panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        self.panel.SetForegroundColour(wx.Colour(255, 255, 255))

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.label_mes = wx.StaticText(self.panel, label="", style=wx.ALIGN_CENTER_HORIZONTAL)
        font_mes = self.label_mes.GetFont()
        font_mes.PointSize += 22
        font_mes.SetWeight(wx.FONTWEIGHT_BOLD)
        self.label_mes.SetFont(font_mes)
        self.main_sizer.Add(self.label_mes, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 20)

        self.grid_sizer = wx.FlexGridSizer(rows=7, cols=7, vgap=10, hgap=20)
        self._setup_grid()
        self.main_sizer.Add(self.grid_sizer, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.TOP, 10)

        self.label_data = wx.StaticText(self.panel, label="", style=wx.ALIGN_CENTER_HORIZONTAL)
        font_data = self.label_data.GetFont()
        font_data.PointSize += 16
        self.label_data.SetFont(font_data)
        self.label_data.SetForegroundColour(wx.Colour(0, 255, 0))
        self.main_sizer.Add(self.label_data, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 20)

        self.panel.SetSizer(self.main_sizer)
        self.panel.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)

        self.Bind(wx.EVT_ACTIVATE, self.onActivate)
        self.Bind(wx.EVT_CLOSE, self.onClose)

        self.update_ui()
        self.Center()
        self.Show()
        self.Raise()
        self.panel.SetFocus()

        self.focus_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._force_focus, self.focus_timer)
        self.focus_timer.StartOnce(250)

        wx.CallLater(600, self.initial_announcement)

    def _garantir_pasta_notas(self):
        try:
            pasta = os.path.dirname(ARQUIVO_NOTAS)
            if pasta and not os.path.isdir(pasta):
                os.makedirs(pasta, exist_ok=True)
        except Exception as e:
            log.error("CALENDARIO: Falha ao garantir pasta de notas: {}".format(e))

    def carregar_notas(self):
        self._garantir_pasta_notas()

        if os.path.exists(ARQUIVO_NOTAS_LEGADO) and not os.path.exists(ARQUIVO_NOTAS):
            try:
                shutil.move(ARQUIVO_NOTAS_LEGADO, ARQUIVO_NOTAS)
                log.info("CALENDARIO: Notas migradas para local seguro.")
            except Exception as e:
                log.error("CALENDARIO: Falha ao migrar notas: {}".format(e))

        try:
            if os.path.exists(ARQUIVO_NOTAS):
                with open(ARQUIVO_NOTAS, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    return dados if isinstance(dados, dict) else {}
        except Exception as e:
            log.error("CALENDARIO: Erro ao carregar notas: {}".format(e))
        return {}

    def salvar_notas(self):
        self._garantir_pasta_notas()
        pasta = os.path.dirname(ARQUIVO_NOTAS)
        tmp_path = os.path.join(pasta, "calendario_simples_BR_notas.tmp")

        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.notas, f, ensure_ascii=False)
            os.replace(tmp_path, ARQUIVO_NOTAS)
        except Exception as e:
            log.error("CALENDARIO: Erro ao salvar notas: {}".format(e))
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            ui.message("Erro ao salvar nota.")

    def _setup_grid(self):
        for abrev in DIAS_ABREV:
            lbl = wx.StaticText(self.panel, label=abrev)
            lbl.SetForegroundColour(wx.Colour(150, 150, 150))
            self.grid_sizer.Add(lbl, 0, wx.ALIGN_CENTER)

        for _ in range(42):
            lbl = wx.StaticText(self.panel, label="")
            font = lbl.GetFont()
            font.PointSize += 14
            lbl.SetFont(font)
            self.dia_labels.append(lbl)
            self.grid_sizer.Add(lbl, 0, wx.ALIGN_CENTER | wx.ALL, 5)

    def _force_focus(self, event=None):
        try:
            if self and self.IsShown() and not self.IsBeingDeleted():
                self.Raise()
                self.panel.SetFocus()
        except Exception:
            pass

    def onClose(self, evt):
        try:
            if hasattr(self, "focus_timer") and self.focus_timer and self.focus_timer.IsRunning():
                self.focus_timer.Stop()
        except Exception:
            pass
        evt.Skip()

    def onActivate(self, evt):
        if evt.GetActive():
            self.panel.SetFocus()
        evt.Skip()

    def update_ui(self):
        self.label_mes.SetLabel("{} {}".format(MESES[self.currentDate.month - 1].upper(), self.currentDate.year))
        self.label_data.SetLabel(formato_data_pt(self.currentDate))

        primeiro_dia = self.currentDate.replace(day=1)
        offset = primeiro_dia.weekday()
        num_dias = calendar.monthrange(self.currentDate.year, self.currentDate.month)[1]

        moveis = get_feriados_moveis(self.currentDate.year)

        for i, lbl in enumerate(self.dia_labels):
            dia_num = i - offset + 1
            if 1 <= dia_num <= num_dias:
                lbl.SetLabel(str(dia_num))
                data_alvo = datetime.date(self.currentDate.year, self.currentDate.month, dia_num)

                if dia_num == self.currentDate.day:
                    lbl.SetBackgroundColour(wx.Colour(255, 255, 0))
                    lbl.SetForegroundColour(wx.Colour(0, 0, 0))
                elif data_alvo == self.today:
                    lbl.SetBackgroundColour(wx.Colour(0, 0, 0))
                    lbl.SetForegroundColour(wx.Colour(255, 100, 100))
                elif (dia_num, self.currentDate.month) in FERIADOS_FIXOS or data_alvo in moveis:
                    lbl.SetBackgroundColour(wx.Colour(0, 0, 0))
                    lbl.SetForegroundColour(wx.Colour(255, 0, 0))
                else:
                    lbl.SetBackgroundColour(wx.Colour(0, 0, 0))
                    lbl.SetForegroundColour(wx.Colour(255, 255, 255))
            else:
                lbl.SetLabel("")
                lbl.SetBackgroundColour(wx.Colour(0, 0, 0))
                lbl.SetForegroundColour(wx.Colour(255, 255, 255))

        self.panel.Layout()

    def mostrar_lista_feriados(self):
        ano = self.currentDate.year
        moveis = get_feriados_moveis(ano)
        todos = []

        for (dia, mes), nome in FERIADOS_FIXOS.items():
            dt = datetime.date(ano, mes, dia)
            todos.append((dt, nome))

        for dt, nome in moveis.items():
            todos.append((dt, nome))

        todos.sort(key=lambda x: x[0])

        lista_formatada = ["{:02d}/{:02d} ({}): {}".format(d.day, d.month, DIAS_ABREV[d.weekday()], n) for d, n in todos]

        ui.message("Listando feriados de {}".format(ano))
        dlg = ListaFeriadosDialog(self, ano, lista_formatada)
        dlg.ShowModal()
        dlg.Destroy()
        self.panel.SetFocus()

    def dialogo_ir_para_data(self):
        dlg = wx.TextEntryDialog(self, "Digite a data (DD/MM/AAAA):", "Ir Para Data")
        if dlg.ShowModal() == wx.ID_OK:
            texto = dlg.GetValue()
            try:
                partes = texto.split("/")
                if len(partes) == 3:
                    dia, mes, ano = map(int, partes)
                    nova_data = datetime.date(ano, mes, dia)
                    self.currentDate = nova_data
                    self.announce(mudou_contexto=True)
                else:
                    ui.message("Formato inválido. Use dia barra mês barra ano.")
            except ValueError:
                ui.message("Data inválida.")
        dlg.Destroy()
        self.panel.SetFocus()

    def copiar_data_clipboard(self):
        texto = formato_data_pt(self.currentDate)
        if api.copyToClip(texto):
            ui.message("Copiado: {}".format(texto))
        else:
            ui.message("Erro ao copiar.")

    def anunciar_dia_ano(self):
        timetuple = self.currentDate.timetuple()
        dia_do_ano = timetuple.tm_yday
        ano = self.currentDate.year
        eh_bissexto = calendar.isleap(ano)
        total_dias = 366 if eh_bissexto else 365
        faltam = total_dias - dia_do_ano

        msg = "Dia {} de {}. Faltam {} dias para o fim do ano.".format(dia_do_ano, total_dias, faltam)
        ui.message(msg)

    def anunciar_fase_lua_detalhada(self):
        """Anuncia a fase simplificada e calcula o intervalo de dias dessa fase."""
        fase_atual = get_fase_lua_nome(self.currentDate)

        data_inicio = self.currentDate
        while True:
            dia_anterior = data_inicio - datetime.timedelta(days=1)
            if get_fase_lua_nome(dia_anterior) != fase_atual:
                break
            data_inicio = dia_anterior

        data_fim = self.currentDate
        while True:
            dia_proximo = data_fim + datetime.timedelta(days=1)
            if get_fase_lua_nome(dia_proximo) != fase_atual:
                break
            data_fim = dia_proximo

        msg = "{}. De {} a {}.".format(
            fase_atual,
            formato_dia_mes(data_inicio),
            formato_dia_mes(data_fim),
        )
        ui.message(msg)

    def gerenciar_nota(self):
        chave = self.currentDate.strftime("%Y-%m-%d")
        nota_atual = self.notas.get(chave, "")

        titulo = "Nota do Dia: {}".format(formato_data_pt(self.currentDate))
        dlg = wx.TextEntryDialog(self, "Edite a nota:", titulo, value=nota_atual, style=wx.TE_MULTILINE | wx.OK | wx.CANCEL)

        if dlg.ShowModal() == wx.ID_OK:
            nova_nota = dlg.GetValue().strip()
            if nova_nota:
                self.notas[chave] = nova_nota
                ui.message("Nota salva.")
            else:
                if chave in self.notas:
                    del self.notas[chave]
                    ui.message("Nota removida.")
            self.salvar_notas()
            self.announce()

        dlg.Destroy()
        self.panel.SetFocus()

    def mostrar_ajuda(self):
        texto_ajuda = (
            "--- Atalhos do Calendário ---\n\n"
            "Navegação:\n"
            "- Setas (Esquerda/Direita): Dia anterior / próximo\n"
            "- Setas (Cima/Baixo): Semana anterior / próxima\n"
            "- PageUp / PageDown: Mês anterior / próximo\n"
            "- Home: Primeiro dia do mês\n"
            "- End: Último dia do mês\n"
            "- Ctrl + Home: Ano anterior\n"
            "- Ctrl + End: Próximo ano\n\n"
            "Ações:\n"
            "- Enter: Abrir/Editar nota do dia selecionado\n"
            "- F: Anunciar fase da lua e seu período (início e fim)\n"
            "- G: Ir para uma data específica\n"
            "- H: Ir para a data atual (Hoje)\n"
            "- C: Copiar data para área de transferência\n"
            "- D: Anunciar dias restantes para o fim do ano\n"
            "- L: Listar todos os feriados do ano\n\n"
            "Geral:\n"
            "- F1: Exibir esta ajuda (use setas para ler)\n"
            "- Esc: Fechar calendário ou ajuda"
        )

        ui.message("Exibindo ajuda.")
        dlg = AjudaDialog(self, texto_ajuda)
        dlg.ShowModal()
        dlg.Destroy()
        self.panel.SetFocus()

    def initial_announcement(self):
        if self.IsActive():
            ui.message("Calendário. {}".format(formato_data_pt(self.today)))

    def announce(self, mudou_contexto=False):
        self.update_ui()
        if mudou_contexto:
            ui.message("{} de {}".format(MESES[self.currentDate.month - 1], self.currentDate.year))

        if self.currentDate == self.today:
            tones.beep(880, 50)

        chave_fixa = (self.currentDate.day, self.currentDate.month)
        moveis = get_feriados_moveis(self.currentDate.year)

        extra_info = []

        if chave_fixa in FERIADOS_FIXOS:
            extra_info.append("Feriado: {}".format(FERIADOS_FIXOS[chave_fixa]))
        elif self.currentDate in moveis:
            extra_info.append("Feriado: {}".format(moveis[self.currentDate]))

        chave_nota = self.currentDate.strftime("%Y-%m-%d")
        if chave_nota in self.notas:
            extra_info.append("Tem nota")

        texto_final = formato_data_pt(self.currentDate)
        if extra_info:
            texto_final += ". " + ". ".join(extra_info)

        ui.message(texto_final)

    def move_safe(self, dias):
        nova_data = self.currentDate + datetime.timedelta(days=dias)
        if nova_data.month == self.currentDate.month and nova_data.year == self.currentDate.year:
            self.currentDate = nova_data
            self.announce()
        else:
            tones.beep(200, 100)

    def onKeyDown(self, evt):
        code = evt.GetKeyCode()

        if code == wx.WXK_ESCAPE:
            self.Close()
        elif code == wx.WXK_F1:
            self.mostrar_ajuda()
        elif code == wx.WXK_RETURN or code == wx.WXK_NUMPAD_ENTER:
            self.gerenciar_nota()
        elif code in (ord("G"), ord("g")) and not evt.ControlDown() and not evt.AltDown():
            self.dialogo_ir_para_data()
        elif code in (ord("H"), ord("h")) and not evt.ControlDown() and not evt.AltDown():
            self.currentDate = self.today
            self.announce(mudou_contexto=False)
        elif code in (ord("C"), ord("c")) and not evt.ControlDown() and not evt.AltDown():
            self.copiar_data_clipboard()
        elif code in (ord("D"), ord("d")) and not evt.ControlDown() and not evt.AltDown():
            self.anunciar_dia_ano()
        elif code in (ord("F"), ord("f")) and not evt.ControlDown() and not evt.AltDown():
            self.anunciar_fase_lua_detalhada()
        elif code in (ord("L"), ord("l")) and not evt.ControlDown() and not evt.AltDown():
            self.mostrar_lista_feriados()
        elif code == wx.WXK_LEFT:
            self.move_safe(-1)
        elif code == wx.WXK_RIGHT:
            self.move_safe(1)
        elif code == wx.WXK_UP:
            self.move_safe(-7)
        elif code == wx.WXK_DOWN:
            self.move_safe(7)
        elif code == wx.WXK_PAGEUP:
            self.add_months(-1)
            self.announce(mudou_contexto=True)
        elif code == wx.WXK_PAGEDOWN:
            self.add_months(1)
            self.announce(mudou_contexto=True)
        elif code == wx.WXK_HOME:
            if evt.ControlDown():
                self.add_years(-1)
                self.announce(mudou_contexto=True)
            else:
                self.currentDate = self.currentDate.replace(day=1)
                self.announce()
        elif code == wx.WXK_END:
            if evt.ControlDown():
                self.add_years(1)
                self.announce(mudou_contexto=True)
            else:
                ultimo_dia = calendar.monthrange(self.currentDate.year, self.currentDate.month)[1]
                self.currentDate = self.currentDate.replace(day=ultimo_dia)
                self.announce()
        else:
            evt.Skip()

    def add_months(self, delta):
        tones.beep(550, 70)
        m = self.currentDate.month - 1 + delta
        y = self.currentDate.year + m // 12
        m = m % 12 + 1
        d = 1
        self.currentDate = datetime.date(y, m, d)

    def add_years(self, delta):
        tones.beep(440, 150)
        y = self.currentDate.year + delta
        m = self.currentDate.month
        d = min(self.currentDate.day, calendar.monthrange(y, m)[1])
        self.currentDate = datetime.date(y, m, d)


# --- PLUGIN GLOBAL ---
class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    def __init__(self):
        super(GlobalPlugin, self).__init__()
        self._menuItem = None
        wx.CallAfter(self._addToToolsMenu)

    def _addToToolsMenu(self):
        try:
            if gui.mainFrame and hasattr(gui.mainFrame, "sysTrayIcon"):
                toolsMenu = gui.mainFrame.sysTrayIcon.toolsMenu
                self._menuItem = toolsMenu.Append(wx.ID_ANY, "Calendário Simples BR")
                gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onMenu, self._menuItem)
                log.info("CALENDARIO: Menu adicionado.")
            else:
                log.error("CALENDARIO: sysTrayIcon não encontrado.")
        except Exception as e:
            log.error("CALENDARIO: Erro ao adicionar menu: {}".format(e))

    def onMenu(self, event):
        self.openCalendar()

    def terminate(self):
        try:
            if self._menuItem:
                if gui.mainFrame and hasattr(gui.mainFrame, "sysTrayIcon"):
                    gui.mainFrame.sysTrayIcon.toolsMenu.Remove(self._menuItem)
        except Exception:
            pass
        super(GlobalPlugin, self).terminate()

    @script(
        description="Abrir Calendário Simples BR",
        category="Calendário Simples BR",
        gesture="kb:NVDA+shift+c",
    )
    def script_openCalendar(self, gesture):
        self.openCalendar()

    def openCalendar(self):
        for child in gui.mainFrame.GetChildren():
            if isinstance(child, CalendarioFrame):
                child.Raise()
                child.panel.SetFocus()
                return
        CalendarioFrame(gui.mainFrame)
