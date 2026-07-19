"""
Lightweight i18n for the SteamLEDs app: 7 languages incl. Chinese and Japanese,
with per-language UI fonts (CJK coverage) and persisted preference.
"""
from __future__ import annotations

import json
import os

# code -> display name
LANGUAGES = {
    "en": "English",
    "pl": "Polski",
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
    "zh": "中文",
    "ja": "日本語",
}

# per-language UI font family (Windows fonts with proper glyph coverage)
FONTS = {
    "zh": "Microsoft YaHei UI",
    "ja": "Yu Gothic UI",
}
DEFAULT_FONT = "Segoe UI"

# string id -> {lang: text}. English is the fallback.
STRINGS: dict[str, dict[str, str]] = {
    "app.ready":       {"en": "Ready", "pl": "Gotowe", "de": "Bereit", "fr": "Prêt", "es": "Listo", "zh": "就绪", "ja": "準備完了"},
    "app.preview":     {"en": "PREVIEW — no hardware", "pl": "PODGLĄD — brak sprzętu", "de": "VORSCHAU — keine Hardware", "fr": "APERÇU — pas de matériel", "es": "VISTA PREVIA — sin hardware", "zh": "预览 — 无硬件", "ja": "プレビュー — ハードウェアなし"},
    "app.tray":        {"en": "Running in tray", "pl": "Działa w zasobniku", "de": "Läuft im Infobereich", "fr": "Actif dans la barre", "es": "En la bandeja", "zh": "在托盘中运行", "ja": "トレイで実行中"},
    "app.applied":     {"en": "Applied", "pl": "Zastosowano", "de": "Übernommen", "fr": "Appliqué", "es": "Aplicado", "zh": "已应用", "ja": "適用しました"},
    "tab.colors":      {"en": "Colors", "pl": "Kolory", "de": "Farben", "fr": "Couleurs", "es": "Colores", "zh": "颜色", "ja": "カラー"},
    "tab.effects":     {"en": "Effects", "pl": "Efekty", "de": "Effekte", "fr": "Effets", "es": "Efectos", "zh": "效果", "ja": "エフェクト"},
    "tab.flags":       {"en": "Flags", "pl": "Flagi", "de": "Flaggen", "fr": "Drapeaux", "es": "Banderas", "zh": "旗帜", "ja": "旗"},
    "tab.animations":  {"en": "Animations", "pl": "Animacje", "de": "Animationen", "fr": "Animations", "es": "Animaciones", "zh": "动画", "ja": "アニメーション"},
    "tab.settings":    {"en": "Settings", "pl": "Ustawienia", "de": "Einstellungen", "fr": "Réglages", "es": "Ajustes", "zh": "设置", "ja": "設定"},
    "tab.system":      {"en": "System", "pl": "System", "de": "System", "fr": "Système", "es": "Sistema", "zh": "系统", "ja": "システム"},
    "sys.fan":         {"en": "Fan", "pl": "Wiatrak", "de": "Lüfter", "fr": "Ventilateur", "es": "Ventilador", "zh": "风扇", "ja": "ファン"},
    "sys.temps":       {"en": "Temperatures", "pl": "Temperatury", "de": "Temperaturen", "fr": "Températures", "es": "Temperaturas", "zh": "温度", "ja": "温度"},
    "sys.hottest":     {"en": "Hottest", "pl": "Najgoręcej", "de": "Wärmste", "fr": "Le plus chaud", "es": "Más caliente", "zh": "最高温", "ja": "最高温"},
    "sys.nohw":        {"en": "No EC detected — run on the Steam Machine (Windows) as admin.", "pl": "Brak EC — uruchom na Steam Machine (Windows) jako administrator.", "de": "Kein EC — auf der Steam Machine (Windows) als Admin starten.", "fr": "Aucun EC — lancez sur la Steam Machine (Windows) en admin.", "es": "Sin EC — ejecuta en la Steam Machine (Windows) como admin.", "zh": "未检测到 EC — 请在 Steam Machine（Windows）上以管理员运行。", "ja": "ECが見つかりません — Steam Machine（Windows）で管理者として実行してください。"},
    "sys.fanctl":      {"en": "Fan boost — up only", "pl": "Boost wiatraka — tylko w górę", "de": "Lüfter-Boost — nur hoch", "fr": "Boost ventilateur — seulement plus", "es": "Refuerzo ventilador — solo subir", "zh": "风扇加速 — 仅提升", "ja": "ファンブースト — 上げるのみ"},
    "sys.fanen":       {"en": "Enable fan control (experimental)", "pl": "Włącz sterowanie (eksperymentalne)", "de": "Steuerung aktivieren (experimentell)", "fr": "Activer le contrôle (expérimental)", "es": "Activar control (experimental)", "zh": "启用风扇控制（实验性）", "ja": "ファン制御を有効化（実験的）"},
    "sys.fanmin":      {"en": "Minimum RPM", "pl": "Minimalne RPM", "de": "Minimale U/min", "fr": "RPM minimum", "es": "RPM mínimas", "zh": "最低转速", "ja": "最低回転数"},
    "sys.apply":       {"en": "Apply", "pl": "Zastosuj", "de": "Anwenden", "fr": "Appliquer", "es": "Aplicar", "zh": "应用", "ja": "適用"},
    "sys.auto":        {"en": "Auto (EC)", "pl": "Auto (EC)", "de": "Auto (EC)", "fr": "Auto (EC)", "es": "Auto (EC)", "zh": "自动 (EC)", "ja": "自動 (EC)"},
    "sys.fanwarn":     {"en": "Only raises the fan, never lowers it. Hands back to Auto anytime.", "pl": "Tylko podnosi obroty, nigdy nie obniża. Auto oddaje sterowanie EC.", "de": "Erhöht nur, senkt nie. „Auto“ gibt an den EC zurück.", "fr": "Augmente seulement, ne baisse jamais. « Auto » rend au EC.", "es": "Solo sube, nunca baja. «Auto» devuelve al EC.", "zh": "只提升，绝不降低。“自动”交还给 EC。", "ja": "上げるだけで下げません。「自動」でECに戻します。"},
    "colors.perled":   {"en": "Per-LED colors", "pl": "Kolory per dioda", "de": "Farbe je LED", "fr": "Couleur par LED", "es": "Color por LED", "zh": "每颗 LED 颜色", "ja": "LEDごとの色"},
    "btn.default":     {"en": "Default", "pl": "Domyślny", "de": "Standard", "fr": "Défaut", "es": "Predet.", "zh": "默认", "ja": "既定"},
    "btn.rainbow":     {"en": "Rainbow", "pl": "Tęcza", "de": "Regenbogen", "fr": "Arc-en-ciel", "es": "Arcoíris", "zh": "彩虹", "ja": "レインボー"},
    "btn.flow":        {"en": "🌈 Flow", "pl": "🌈 Płyń", "de": "🌈 Fluss", "fr": "🌈 Flux", "es": "🌈 Fluir", "zh": "🌈 流动", "ja": "🌈 フロー"},
    "set.reverse":     {"en": "Reverse LED order (match your panel)", "pl": "Odwróć kolejność diod (dopasuj do panelu)", "de": "LED-Reihenfolge umkehren (an Panel anpassen)", "fr": "Inverser l'ordre des LED (selon le panneau)", "es": "Invertir orden de LED (según tu panel)", "zh": "反转 LED 顺序（匹配面板）", "ja": "LEDの順序を反転（パネルに合わせる）"},
    "set.hotkeys":     {"en": "Global hotkeys: Ctrl+Alt+O toggle blue/off · Ctrl+Alt+R rainbow flow", "pl": "Skróty globalne: Ctrl+Alt+O niebieski/wyłącz · Ctrl+Alt+R płynąca tęcza", "de": "Globale Tasten: Strg+Alt+O Blau/Aus · Strg+Alt+R Regenbogen", "fr": "Raccourcis: Ctrl+Alt+O bleu/arrêt · Ctrl+Alt+R arc-en-ciel", "es": "Atajos: Ctrl+Alt+O azul/apagar · Ctrl+Alt+R arcoíris", "zh": "全局快捷键：Ctrl+Alt+O 蓝色/关闭 · Ctrl+Alt+R 彩虹流动", "ja": "グローバルキー: Ctrl+Alt+O 青/オフ · Ctrl+Alt+R レインボー"},
    "btn.solid":       {"en": "Solid…", "pl": "Jednolity…", "de": "Einfarbig…", "fr": "Uni…", "es": "Sólido…", "zh": "纯色…", "ja": "単色…"},
    "btn.off":         {"en": "Off", "pl": "Wyłącz", "de": "Aus", "fr": "Éteint", "es": "Apagar", "zh": "关闭", "ja": "オフ"},
    "btn.boot":        {"en": "Boot color…", "pl": "Kolor startowy…", "de": "Startfarbe…", "fr": "Couleur de démarrage…", "es": "Color de inicio…", "zh": "开机颜色…", "ja": "起動時の色…"},
    "lbl.brightness":  {"en": "Brightness", "pl": "Jasność", "de": "Helligkeit", "fr": "Luminosité", "es": "Brillo", "zh": "亮度", "ja": "明るさ"},
    "fx.title":        {"en": "Firmware effect (runs on the panel)", "pl": "Efekt sprzętowy (na panelu)", "de": "Firmware-Effekt (im Panel)", "fr": "Effet firmware (sur le panneau)", "es": "Efecto de firmware (en el panel)", "zh": "固件效果（在面板上运行）", "ja": "ファームウェア効果（パネル側）"},
    "fx.speed":        {"en": "Delay (speed)", "pl": "Opóźnienie (prędkość)", "de": "Verzögerung (Tempo)", "fr": "Délai (vitesse)", "es": "Retardo (velocidad)", "zh": "延迟（速度）", "ja": "遅延（速度）"},
    "fx.breath":       {"en": "Breath", "pl": "Oddech", "de": "Atem", "fr": "Respiration", "es": "Respiración", "zh": "呼吸", "ja": "ブレス"},
    "fx.shift":        {"en": "Color shift", "pl": "Przesunięcie barw", "de": "Farbverschiebung", "fr": "Décalage couleur", "es": "Cambio de color", "zh": "色彩偏移", "ja": "カラーシフト"},
    "fx.patrol":       {"en": "Patrol #", "pl": "Patrol #", "de": "Patrouille #", "fr": "Patrouille #", "es": "Patrulla #", "zh": "巡逻数", "ja": "パトロール数"},
    "flags.title":     {"en": "Flag wave (stadium)", "pl": "Fala flagi (stadion)", "de": "Flaggenwelle (Stadion)", "fr": "Vague de drapeau (stade)", "es": "Ola de bandera (estadio)", "zh": "旗帜波浪（体育场）", "ja": "旗のウェーブ（スタジアム）"},
    "flags.mirror":    {"en": "Mirror (module)", "pl": "Odbicie (moduł)", "de": "Spiegeln (Modul)", "fr": "Miroir (module)", "es": "Espejo (módulo)", "zh": "镜像（模块）", "ja": "ミラー（モジュール）"},
    "common.speed":    {"en": "Speed", "pl": "Prędkość", "de": "Tempo", "fr": "Vitesse", "es": "Velocidad", "zh": "速度", "ja": "速度"},
    "common.start":    {"en": "Start", "pl": "Start", "de": "Start", "fr": "Démarrer", "es": "Iniciar", "zh": "开始", "ja": "開始"},
    "common.stop":     {"en": "Stop", "pl": "Stop", "de": "Stopp", "fr": "Arrêter", "es": "Detener", "zh": "停止", "ja": "停止"},
    "common.play":     {"en": "Play", "pl": "Odtwórz", "de": "Abspielen", "fr": "Lire", "es": "Reproducir", "zh": "播放", "ja": "再生"},
    "anim.presets":    {"en": "Presets", "pl": "Ustawienia gotowe", "de": "Vorlagen", "fr": "Préréglages", "es": "Ajustes preestablecidos", "zh": "预设", "ja": "プリセット"},
    "anim.build":      {"en": "Build your own", "pl": "Stwórz własną", "de": "Eigene erstellen", "fr": "Créez la vôtre", "es": "Crea la tuya", "zh": "自定义", "ja": "自作する"},
    "anim.pattern":    {"en": "Pattern", "pl": "Wzór", "de": "Muster", "fr": "Motif", "es": "Patrón", "zh": "图案", "ja": "パターン"},
    "anim.motion":     {"en": "Motion", "pl": "Ruch", "de": "Bewegung", "fr": "Mouvement", "es": "Movimiento", "zh": "运动", "ja": "モーション"},
    "anim.colors":     {"en": "Colors:", "pl": "Kolory:", "de": "Farben:", "fr": "Couleurs :", "es": "Colores:", "zh": "颜色：", "ja": "色："},
    "anim.name":       {"en": "animation name", "pl": "nazwa animacji", "de": "Animationsname", "fr": "nom de l'animation", "es": "nombre de animación", "zh": "动画名称", "ja": "アニメーション名"},
    "anim.save":       {"en": "Save preset", "pl": "Zapisz preset", "de": "Vorlage speichern", "fr": "Enregistrer", "es": "Guardar", "zh": "保存预设", "ja": "プリセット保存"},
    "set.startup":     {"en": "Startup & tray", "pl": "Autostart i zasobnik", "de": "Autostart & Infobereich", "fr": "Démarrage & barre", "es": "Inicio y bandeja", "zh": "启动与托盘", "ja": "起動とトレイ"},
    "set.autostart":   {"en": "Start with Windows (run in tray)", "pl": "Uruchamiaj z Windows (w zasobniku)", "de": "Mit Windows starten (im Infobereich)", "fr": "Démarrer avec Windows (barre)", "es": "Iniciar con Windows (bandeja)", "zh": "随 Windows 启动（在托盘）", "ja": "Windowsと同時に起動（トレイ）"},
    "set.trayinfo":    {"en": "Closing the window hides SteamLEDs to the tray and keeps it\nrunning. Right-click the tray icon to Quit.", "pl": "Zamknięcie okna chowa SteamLEDs do zasobnika i nie zamyka go.\nKliknij prawym ikonę w zasobniku, aby zamknąć.", "de": "Das Schließen des Fensters versteckt SteamLEDs im Infobereich.\nRechtsklick auf das Symbol zum Beenden.", "fr": "Fermer la fenêtre réduit SteamLEDs dans la barre.\nClic droit sur l'icône pour quitter.", "es": "Cerrar la ventana oculta SteamLEDs en la bandeja.\nClic derecho en el icono para salir.", "zh": "关闭窗口会将 SteamLEDs 隐藏到托盘并保持运行。\n右键点击托盘图标可退出。", "ja": "ウィンドウを閉じるとトレイに格納され動作を継続します。\nトレイアイコンを右クリックで終了。"},
    "set.about":       {"en": "About", "pl": "O programie", "de": "Über", "fr": "À propos", "es": "Acerca de", "zh": "关于", "ja": "情報"},
    "set.hwok":        {"en": "Hardware connected ✓", "pl": "Sprzęt podłączony ✓", "de": "Hardware verbunden ✓", "fr": "Matériel connecté ✓", "es": "Hardware conectado ✓", "zh": "硬件已连接 ✓", "ja": "ハードウェア接続済み ✓"},
    "set.previewinfo": {"en": "PREVIEW mode (no hardware detected)", "pl": "Tryb PODGLĄDU (brak sprzętu)", "de": "VORSCHAU-Modus (keine Hardware)", "fr": "Mode APERÇU (pas de matériel)", "es": "Modo VISTA PREVIA (sin hardware)", "zh": "预览模式（未检测到硬件）", "ja": "プレビューモード（ハードウェア未検出）"},
    "set.quit":        {"en": "Quit SteamLEDs", "pl": "Zamknij SteamLEDs", "de": "SteamLEDs beenden", "fr": "Quitter SteamLEDs", "es": "Salir de SteamLEDs", "zh": "退出 SteamLEDs", "ja": "SteamLEDsを終了"},
    "set.language":    {"en": "Language", "pl": "Język", "de": "Sprache", "fr": "Langue", "es": "Idioma", "zh": "语言", "ja": "言語"},
    "set.appearance":  {"en": "Appearance", "pl": "Wygląd", "de": "Darstellung", "fr": "Apparence", "es": "Apariencia", "zh": "外观", "ja": "外観"},
    "set.opacity":     {"en": "Window opacity", "pl": "Przezroczystość okna", "de": "Fenster-Deckkraft", "fr": "Opacité de la fenêtre", "es": "Opacidad de ventana", "zh": "窗口不透明度", "ja": "ウィンドウの不透明度"},
    "set.glass":       {"en": "Glass effect (Windows 11)", "pl": "Efekt szkła (Windows 11)", "de": "Glaseffekt (Windows 11)", "fr": "Effet verre (Windows 11)", "es": "Efecto cristal (Windows 11)", "zh": "玻璃效果（Windows 11）", "ja": "ガラス効果（Windows 11）"},
    "set.support":     {"en": "Support", "pl": "Wsparcie", "de": "Unterstützung", "fr": "Soutien", "es": "Apoyo", "zh": "支持", "ja": "サポート"},
    "set.kofi":        {"en": "☕  Support me on Ko-fi", "pl": "☕  Wesprzyj mnie na Ko-fi", "de": "☕  Unterstütze mich auf Ko-fi", "fr": "☕  Soutenez-moi sur Ko-fi", "es": "☕  Apóyame en Ko-fi", "zh": "☕  在 Ko-fi 上支持我", "ja": "☕  Ko-fiで応援する"},
}

_state = {"lang": "en"}


def available() -> dict[str, str]:
    return LANGUAGES


def get_language() -> str:
    return _state["lang"]


def set_language(code: str) -> None:
    if code in LANGUAGES:
        _state["lang"] = code


def code_for_name(name: str) -> str:
    for code, disp in LANGUAGES.items():
        if disp == name:
            return code
    return "en"


def t(key: str) -> str:
    entry = STRINGS.get(key)
    if not entry:
        return key
    return entry.get(_state["lang"]) or entry.get("en") or key


def font_family(lang: str | None = None) -> str:
    return FONTS.get(lang or _state["lang"], DEFAULT_FONT)


# --- preference persistence ------------------------------------------------
def _settings_path() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "steamleds")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "settings.json")


def load_settings() -> dict:
    try:
        with open(_settings_path(), encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_settings(data: dict) -> None:
    try:
        with open(_settings_path(), "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    except Exception:
        pass
