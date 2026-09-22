from pathlib import Path
import pandas as pd
import joblib
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QLineEdit, QFrame, QSizePolicy
from PyQt6.QtGui import QFont, QColor, QPainter, QPen
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QEvent, QRectF, QSettings, pyqtProperty, QEasingCurve, QPropertyAnimation

REQUIRED_COLUMNS = ['diagonal','height_left','height_right','margin_low','margin_up','length']
lighten = lambda hex_color, f=140: QColor(hex_color).lighter(f)

# Switch animé
class Switch(QWidget):
    toggled = pyqtSignal(bool)
    def __init__(self, checked=False, parent=None):
        super().__init__(parent); self._checked=checked; self._offset=1.0 if checked else 0.0
        self.setFixedSize(54,28); self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.anim = QPropertyAnimation(self, b"offset", duration=160, easingCurve=QEasingCurve.Type.InOutCubic)
    def mousePressEvent(self, _): self.setChecked(not self._checked); self.toggled.emit(self._checked)
    def isChecked(self): return self._checked
    def setChecked(self, v:bool): self._checked=v; self.anim.stop(); self.anim.setStartValue(self._offset); self.anim.setEndValue(1.0 if v else 0.0); self.anim.start()
    def getOffset(self): return self._offset
    def setOffset(self, x): self._offset=float(x); self.update()
    offset = pyqtProperty(float, fget=getOffset, fset=setOffset)
    def paintEvent(self, _):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        track_on, track_off = QColor("#e5e7eb"), QColor("#4b5563")
        border_on, border_off = QColor("#cbd5e1"), QColor("#1f2937")
        bg = track_on if self._checked else track_off; bd = border_on if self._checked else border_off
        r = QRectF(self.rect()).adjusted(0.75,0.75,-0.75,-0.75)
        p.setBrush(bg); p.setPen(QPen(bd,1.5)); p.drawRoundedRect(r,14,14)
        m=3; d=self.height()-2*m; x=m + self._offset*(self.width()-2*m-d)
        p.setBrush(QColor("#ffffff")); p.setPen(Qt.PenStyle.NoPen); p.drawEllipse(QRectF(x,m,d,d))

# Barre de statut sensible au thème
class StatusBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(44); self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.label = QLabel("PRÊT", self); self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f=QFont("Segoe UI",12); f.setWeight(QFont.Weight.Bold); self.label.setFont(f)
        self.theme="dark"; self.accent="idle"
        self.fill=QColor("#2f3b4a"); self.border=lighten("#2f3b4a")
        self.label.setStyleSheet("color:#fff;background:transparent;")
    def setTheme(self, theme:str): self.theme=theme; self.setAccent(self.accent)
    def setAccent(self, key:str):
        self.accent=key
        palettes = {
            "dark":   {"idle":"#2f3b4a","info":"#0b76b0","success":"#1a9c4a","warn":"#b07c10","error":"#b93a3a"},
            "light":  {"idle":"#cbd5e1","info":"#38bdf8","success":"#34d399","warn":"#facc15","error":"#f87171"},
        }
        base = palettes.get(self.theme, palettes["dark"]).get(key, "#0b76b0")
        self.fill=QColor(base); self.border=lighten(base); self.update()
    def setText(self, text:str): self.label.setText(text.upper()); self.update()
    def resizeEvent(self,e): self.label.setGeometry(self.rect()); super().resizeEvent(e)
    def paintEvent(self,_):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r=QRectF(self.rect()).adjusted(0.75,0.75,-0.75,-0.75)
        p.setBrush(self.fill); p.setPen(QPen(self.border,1.5)); p.drawRoundedRect(r,12,12)

class DropArea(QFrame):
    fileSelected = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent); self.setObjectName("DropArea"); self.setAcceptDrops(True)
        self.setMinimumHeight(170); self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.label = QLabel("Déposez votre CSV ici ou cliquez pour parcourir", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f=QFont("Segoe UI",12); f.setWeight(QFont.Weight.DemiBold); self.label.setFont(f)
        lay=QVBoxLayout(self); lay.setContentsMargins(22,22,22,22); lay.addWidget(self.label)
        self.setTheme("dark")
    def setTheme(self, theme):
        if theme=="light":
            self._base="QFrame#DropArea{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffffff,stop:1 #f3f4f6);border:1px solid #d1d5db;border-radius:14px;color:#111827;}"
            self._active="QFrame#DropArea{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #f8fafc,stop:1 #eef2f7);border:1px solid #0ea5e9;border-radius:14px;color:#111827;}"
            self.label.setStyleSheet("color:#111827;")
        else:
            self._base="QFrame#DropArea{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #11151b,stop:1 #0c1117);border:1px solid #1f2937;border-radius:14px;color:#e6edf3;}"
            self._active="QFrame#DropArea{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #101821,stop:1 #0b1720);border:1px solid #0ea5e9;border-radius:14px;color:#e6edf3;}"
            self.label.setStyleSheet("color:#e6edf3;")
        self.setStyleSheet(self._base)
    def setActive(self,a): self.setStyleSheet(self._active if a else self._base)
    def dragEnterEvent(self,e):
        urls=e.mimeData().urls()
        if urls and urls[0].toLocalFile().lower().endswith(".csv"): self.setActive(True); e.acceptProposedAction()
    def dragLeaveEvent(self,_): self.setActive(False)
    def dropEvent(self,e):
        self.setActive(False); urls=e.mimeData().urls()
        if urls: self.fileSelected.emit(urls[0].toLocalFile())
    def mousePressEvent(self,_):
        top=self.parentWidget()
        if top and hasattr(top,"sep_edit"): top.sep_edit.clearFocus()
        start_dir = top.get_last_dir() if top and hasattr(top, "get_last_dir") else ""
        path,_=QFileDialog.getOpenFileName(self,"Ouvrir un fichier CSV",start_dir,"CSV (*.csv)")
        if path:
            if top and hasattr(top, "set_last_dir"):
                top.set_last_dir(path)
            self.fileSelected.emit(path)

class PredictorApp(QWidget):
    def __init__(self):
        super().__init__(); self.setWindowTitle("CSV → Prédiction")
        self.resize(780, 340); self.setMinimumSize(470, 320)
        self.settings = QSettings("SchmidtGroupe","CSVPrediction")
        self.theme = self.settings.value("theme","dark")
        root=QVBoxLayout(self); root.setContentsMargins(16,16,16,16); root.setSpacing(12)
        self.status_bar = StatusBar(self); root.addWidget(self.status_bar)
        row=QHBoxLayout(); row.setSpacing(12)
        row.addWidget(QLabel("Séparateur"))
        self.sep_edit = QLineEdit(self.settings.value("sep", ",")); self.sep_edit.setFixedWidth(64); self.sep_edit.setMaxLength(3)
        self.sep_edit.editingFinished.connect(lambda: self.settings.setValue("sep", self.sep_edit.text() or ","))
        row.addWidget(self.sep_edit); row.addStretch(1)
        row.addWidget(QLabel("Mode clair"))
        self.switch = Switch(checked=(self.theme=="light"))
        self.switch.toggled.connect(lambda on: self.set_theme("light" if on else "dark"))
        row.addWidget(self.switch); root.addLayout(row)
        self.drop = DropArea(self); self.drop.fileSelected.connect(self.handle_file_selected); root.addWidget(self.drop,1)
        script_dir = Path(__file__).parent
        pipeline_path = script_dir / "modele_billets.joblib"
        try: self.pipeline = joblib.load(pipeline_path); self._set_status("PRÊT","idle")
        except Exception: self.pipeline=None; self._set_status("PIPELINE INTROUVABLE","error")
        self.set_theme(self.theme); self.installEventFilter(self)
    def set_theme(self, theme):
        self.theme=theme; self.settings.setValue("theme", theme)
        if theme=="light":
            QApplication.instance().setStyleSheet(
                "QWidget{background:#f6f8fb;color:#111827;font-family:'Segoe UI',Arial,sans-serif;font-size:11pt;}"
                "QLabel{color:#111827;} QLineEdit{background:#ffffff;color:#111827;border:1px solid #cbd5e1;border-radius:8px;padding:6px 8px;selection-background-color:#0ea5e9;selection-color:#0b0f14;} QLineEdit:focus{border-color:#0ea5e9;}"
            )
        else:
            QApplication.instance().setStyleSheet(
                "QWidget{background:#0b0f14;color:#e6edf3;font-family:'Segoe UI',Arial,sans-serif;font-size:11pt;}"
                "QLabel{color:#e6edf3;} QLineEdit{background:#121824;color:#e6edf3;border:1px solid #26313d;border-radius:8px;padding:6px 8px;selection-background-color:#0ea5e9;selection-color:#0b0f14;} QLineEdit:focus{border-color:#0ea5e9;}"
            )
        self.drop.setTheme(theme)
        self.status_bar.setTheme(theme)  # adapte la palette de la barre au thème
    def keyPressEvent(self,e):
        if e.key()==Qt.Key.Key_F11: self.showFullScreen() if not self.isFullScreen() else self.showNormal()
        elif e.key()==Qt.Key.Key_Escape and self.isFullScreen(): self.showNormal()
        else: super().keyPressEvent(e)
    def eventFilter(self,obj,e):
        if e.type()==QEvent.Type.MouseButtonPress and self.sep_edit.hasFocus(): self.sep_edit.clearFocus()
        return super().eventFilter(obj, e)
    def handle_file_selected(self, path:str): self.process_csv(path, self.sep_edit.text().strip() or ",")
    def process_csv(self, path:str, sep:str=","):
        if self.pipeline is None: self._set_status("PIPELINE NON CHARGÉ","error"); return
        self._set_status(f"LECTURE: {Path(path).name}","info")
        try:
            df=pd.read_csv(path, sep=sep)
            miss=[c for c in REQUIRED_COLUMNS if c not in df.columns]
            if miss: self._set_status(f"MANQUANT: {', '.join(miss)}","error"); return
            feats=df[REQUIRED_COLUMNS].apply(pd.to_numeric, errors="coerce"); mask=feats.notna().all(axis=1); Xp=feats[mask]
            if Xp.empty: self._set_status("AUCUNE LIGNE VALIDE","warn"); return
            df["prediction"]=pd.NA; df.loc[Xp.index,"prediction"]=self.pipeline.predict(Xp)
            suggested=Path(path).with_name(f"{Path(path).stem}_pred.csv").as_posix()
            save,_=QFileDialog.getSaveFileName(self,"Enregistrer le CSV",suggested,"CSV (*.csv)")
            if save: df.to_csv(save, sep=sep, index=False); self._set_status(f"ENREGISTRÉ: {Path(save).name}","success"); self.drop.setActive(True); QTimer.singleShot(600, lambda: self.drop.setActive(False))
            else: self._set_status("ANNULÉ","warn")
        except Exception as ex: self._set_status(f"ERREUR: {ex}","error")
    def _set_status(self, text, accent): self.status_bar.setText(text); self.status_bar.setAccent(accent)
    def get_last_dir(self): default=str(Path.home()/"Desktop"); return self.settings.value("last_dir",default)
    def set_last_dir(self,filepath): self.settings.setValue("last_dir", str(Path(filepath).parent))

if __name__ == "__main__":
    app = QApplication.instance() or QApplication([])
    w = PredictorApp(); w.show()
    app.exec()
