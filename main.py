import ctypes, os, sys

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import threading, requests, time, json
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog, Toplevel

VERSION = "4.2.0"
CHUNK_SIZE = 65536
UPDATE_INTERVAL = 1000
CONFIG_FILE = "cdn_nodes.json"
ICON_FILE = "icon.ico"
THEME = "cosmo"

LANG = {
    "en": {
        "lang_name": "English",
        "app_title": "CDN SpeedTest v{VERSION}",
        "ip_address": "IP Address",
        "fetching": "Fetching...",
        "failed": "Failed",
        "current_node": "Current Node",
        "settings": "Settings",
        "stop": "Stop",
        "start_test": "Start Test",
        "speed_results": "Speed Results",
        "realtime_speed": "Real-time Speed",
        "max_speed": "Max Speed",
        "avg_speed": "Average Speed",
        "elapsed": "Elapsed",
        "remaining": "Remaining",
        "downloaded": "Downloaded",
        "ready": "Ready",
        "testing": "Testing...",
        "complete": "Complete",
        "stopped": "Stopped",
        "calculating": "Calculating...",
        "settings_title": "Node Manager",
        "node_list": "Node List",
        "node_name": "Node Name",
        "url_address": "URL Address",
        "def_col": "Default",
        "add": "+ Add",
        "edit": "Edit",
        "delete": "Delete",
        "set_default": "Set Default",
        "move_up": "Up",
        "move_down": "Down",
        "close": "Close",
        "auto_save_hint": "Auto-saved on change, effective on close",
        "please_select": "Please select a node first",
        "enter_name": "Enter node name:",
        "enter_url": "Enter test URL:",
        "confirm_delete": 'Delete node "{name}"?',
        "save_failed": "Save Failed",
        "save_failed_msg": "Unable to save config:\n{e}",
        "timeout": "Connection timeout",
        "connection_failed": "Connection failed",
        "error": "Error: {msg}",
        "language": "Language",
        "name_empty": "Name cannot be empty",
        "url_empty": "URL cannot be empty",
        "no_nodes": "No nodes available. Please add a node in Settings.",
        "cannot_delete_last": "Cannot delete the last node.",
    },
    "zh": {
        "lang_name": "简体中文",
        "app_title": "CDN 测速 v{VERSION}",
        "ip_address": "IP 地址",
        "fetching": "获取中...",
        "failed": "获取失败",
        "current_node": "当前节点",
        "settings": "设置",
        "stop": "停止",
        "start_test": "开始测速",
        "speed_results": "测速结果",
        "realtime_speed": "实时网速",
        "max_speed": "最高网速",
        "avg_speed": "平均网速",
        "elapsed": "已用时间",
        "remaining": "剩余时间",
        "downloaded": "已下载",
        "ready": "就绪",
        "testing": "测速中...",
        "complete": "测速完成",
        "stopped": "已停止",
        "calculating": "计算中...",
        "settings_title": "节点管理",
        "node_list": "节点列表",
        "node_name": "节点名称",
        "url_address": "URL 地址",
        "def_col": "默认",
        "add": "+ 新增",
        "edit": "编辑",
        "delete": "删除",
        "set_default": "设为默认",
        "move_up": "上移",
        "move_down": "下移",
        "close": "关闭",
        "auto_save_hint": "修改自动保存，关闭即生效",
        "please_select": "请先选择一个节点",
        "enter_name": "请输入节点名称:",
        "enter_url": "请输入测试 URL:",
        "confirm_delete": "确定删除节点「{name}」吗？",
        "save_failed": "保存失败",
        "save_failed_msg": "无法保存配置:\n{e}",
        "timeout": "连接超时",
        "connection_failed": "连接失败",
        "error": "错误: {msg}",
        "language": "语言",
        "name_empty": "名称不能为空",
        "url_empty": "URL 不能为空",
        "no_nodes": "没有可用节点，请在设置中添加节点。",
        "cannot_delete_last": "无法删除最后一个节点。",
    },
    "fr": {
        "lang_name": "Fran\u00E7ais",
        "app_title": "CDN SpeedTest v{VERSION}",
        "ip_address": "Adresse IP",
        "fetching": "R\u00E9cup\u00E9ration...",
        "failed": "\u00C9chec",
        "current_node": "N\u0153ud actuel",
        "settings": "Param\u00E8tres",
        "stop": "Arr\u00EAter",
        "start_test": "Lancer le test",
        "speed_results": "R\u00E9sultats de vitesse",
        "realtime_speed": "Temps r\u00E9el",
        "max_speed": "Vitesse max",
        "avg_speed": "Vitesse moyenne",
        "elapsed": "\u00C9coul\u00E9",
        "remaining": "Restant",
        "downloaded": "T\u00E9l\u00E9charg\u00E9",
        "ready": "Pr\u00EAt",
        "testing": "Test en cours...",
        "complete": "Termin\u00E9",
        "stopped": "Arr\u00EAt\u00E9",
        "calculating": "Calcul...",
        "settings_title": "Gestionnaire de n\u0153uds",
        "node_list": "Liste des n\u0153uds",
        "node_name": "Nom du n\u0153ud",
        "url_address": "Adresse URL",
        "def_col": "D\u00E9faut",
        "add": "+ Ajouter",
        "edit": "Modifier",
        "delete": "Supprimer",
        "set_default": "Par d\u00E9faut",
        "move_up": "Monter",
        "move_down": "Descendre",
        "close": "Fermer",
        "auto_save_hint": "Sauvegarde auto, effectif \u00E0 la fermeture",
        "please_select": "S\u00E9lectionnez d'abord un n\u0153ud",
        "enter_name": "Nom du n\u0153ud:",
        "enter_url": "URL de test:",
        "confirm_delete": 'Supprimer le n\u0153ud "{name}" ?',
        "save_failed": "\u00C9chec de sauvegarde",
        "save_failed_msg": "Impossible de sauvegarder :\n{e}",
        "timeout": "D\u00E9lai d\u00E9pass\u00E9",
        "connection_failed": "\u00C9chec de connexion",
        "error": "Erreur : {msg}",
        "language": "Langue",
        "name_empty": "Le nom ne peut pas être vide",
        "url_empty": "L'URL ne peut pas être vide",
        "no_nodes": "Aucun nœud disponible. Veuillez ajouter un nœud dans Paramètres.",
        "cannot_delete_last": "Impossible de supprimer le dernier nœud.",
    },
    "de": {
        "lang_name": "Deutsch",
        "app_title": "CDN SpeedTest v{VERSION}",
        "ip_address": "IP-Adresse",
        "fetching": "Abrufen...",
        "failed": "Fehlgeschlagen",
        "current_node": "Aktueller Knoten",
        "settings": "Einstellungen",
        "stop": "Stopp",
        "start_test": "Test starten",
        "speed_results": "Geschwindigkeit",
        "realtime_speed": "Echtzeit",
        "max_speed": "Maximum",
        "avg_speed": "Durchschnitt",
        "elapsed": "Verstrichen",
        "remaining": "Verbleibend",
        "downloaded": "Heruntergeladen",
        "ready": "Bereit",
        "testing": "Test l\u00E4uft...",
        "complete": "Abgeschlossen",
        "stopped": "Gestoppt",
        "calculating": "Berechne...",
        "settings_title": "Knotenverwaltung",
        "node_list": "Knotenliste",
        "node_name": "Knotenname",
        "url_address": "URL-Adresse",
        "def_col": "Standard",
        "add": "+ Hinzuf\u00FCgen",
        "edit": "Bearbeiten",
        "delete": "L\u00F6schen",
        "set_default": "Als Standard",
        "move_up": "Hoch",
        "move_down": "Runter",
        "close": "Schlie\u00DFen",
        "auto_save_hint": "Auto-Speicherung, wirksam beim Schlie\u00DFen",
        "please_select": "Bitte w\u00E4hlen Sie einen Knoten",
        "enter_name": "Knotenname eingeben:",
        "enter_url": "Test-URL eingeben:",
        "confirm_delete": 'Knoten "{name}" l\u00F6schen?',
        "save_failed": "Speichern fehlgeschlagen",
        "save_failed_msg": "Konfiguration kann nicht gespeichert werden:\n{e}",
        "timeout": "Zeit\u00FCberschreitung",
        "connection_failed": "Verbindung fehlgeschlagen",
        "error": "Fehler: {msg}",
        "language": "Sprache",
        "name_empty": "Name darf nicht leer sein",
        "url_empty": "URL darf nicht leer sein",
        "no_nodes": "Keine Knoten verfügbar. Bitte fügen Sie einen Knoten in den Einstellungen hinzu.",
        "cannot_delete_last": "Der letzte Knoten kann nicht gelöscht werden.",
    },
    "es": {
        "lang_name": "Espa\u00F1ol",
        "app_title": "CDN SpeedTest v{VERSION}",
        "ip_address": "Direcci\u00F3n IP",
        "fetching": "Obteniendo...",
        "failed": "Error",
        "current_node": "Nodo actual",
        "settings": "Ajustes",
        "stop": "Detener",
        "start_test": "Iniciar prueba",
        "speed_results": "Resultados de velocidad",
        "realtime_speed": "Tiempo real",
        "max_speed": "M\u00E1xima",
        "avg_speed": "Media",
        "elapsed": "Transcurrido",
        "remaining": "Restante",
        "downloaded": "Descargado",
        "ready": "Listo",
        "testing": "Probando...",
        "complete": "Completado",
        "stopped": "Detenido",
        "calculating": "Calculando...",
        "settings_title": "Administrador de nodos",
        "node_list": "Lista de nodos",
        "node_name": "Nombre del nodo",
        "url_address": "Direcci\u00F3n URL",
        "def_col": "Defecto",
        "add": "+ A\u00F1adir",
        "edit": "Editar",
        "delete": "Eliminar",
        "set_default": "Por defecto",
        "move_up": "Subir",
        "move_down": "Bajar",
        "close": "Cerrar",
        "auto_save_hint": "Auto-guardado, efectivo al cerrar",
        "please_select": "Seleccione un nodo primero",
        "enter_name": "Nombre del nodo:",
        "enter_url": "URL de prueba:",
        "confirm_delete": '\u00BFEliminar nodo "{name}"?',
        "save_failed": "Error al guardar",
        "save_failed_msg": "No se puede guardar la configuraci\u00F3n:\n{e}",
        "timeout": "Tiempo de espera agotado",
        "connection_failed": "Conexi\u00F3n fallida",
        "error": "Error: {msg}",
        "language": "Idioma",
        "name_empty": "El nombre no puede estar vacío",
        "url_empty": "La URL no puede estar vacía",
        "no_nodes": "No hay nodos disponibles. Agregue un nodo en Configuración.",
        "cannot_delete_last": "No se puede eliminar el último nodo.",
    },
    "pt": {
        "lang_name": "Portugu\u00EAs",
        "app_title": "CDN SpeedTest v{VERSION}",
        "ip_address": "Endere\u00E7o IP",
        "fetching": "Obtendo...",
        "failed": "Falhou",
        "current_node": "N\u00F3 atual",
        "settings": "Configura\u00E7\u00F5es",
        "stop": "Parar",
        "start_test": "Iniciar teste",
        "speed_results": "Resultados de velocidade",
        "realtime_speed": "Tempo real",
        "max_speed": "Velocidade m\u00E1x",
        "avg_speed": "Velocidade m\u00E9dia",
        "elapsed": "Decorrido",
        "remaining": "Restante",
        "downloaded": "Baixado",
        "ready": "Pronto",
        "testing": "Testando...",
        "complete": "Conclu\u00EDdo",
        "stopped": "Parado",
        "calculating": "Calculando...",
        "settings_title": "Gerenciador de n\u00F3s",
        "node_list": "Lista de n\u00F3s",
        "node_name": "Nome do n\u00F3",
        "url_address": "Endere\u00E7o URL",
        "def_col": "Padr\u00E3o",
        "add": "+ Adicionar",
        "edit": "Editar",
        "delete": "Excluir",
        "set_default": "Definir padr\u00E3o",
        "move_up": "Subir",
        "move_down": "Descer",
        "close": "Fechar",
        "auto_save_hint": "Salvo automaticamente, efetivo ao fechar",
        "please_select": "Selecione um n\u00F3 primeiro",
        "enter_name": "Nome do n\u00F3:",
        "enter_url": "URL de teste:",
        "confirm_delete": 'Excluir n\u00F3 "{name}"?',
        "save_failed": "Falha ao salvar",
        "save_failed_msg": "N\u00E3o foi poss\u00EDvel salvar:\n{e}",
        "timeout": "Tempo esgotado",
        "connection_failed": "Falha de conex\u00E3o",
        "error": "Erro: {msg}",
        "language": "Idioma",
        "name_empty": "O nome não pode estar vazio",
        "url_empty": "A URL não pode estar vazia",
        "no_nodes": "Nenhum nó disponível. Adicione um nó em Configurações.",
        "cannot_delete_last": "Não é possível excluir o último nó.",
    },
    "it": {
        "lang_name": "Italiano",
        "app_title": "CDN SpeedTest v{VERSION}",
        "ip_address": "Indirizzo IP",
        "fetching": "Recupero...",
        "failed": "Fallito",
        "current_node": "Nodo corrente",
        "settings": "Impostazioni",
        "stop": "Ferma",
        "start_test": "Avvia test",
        "speed_results": "Risultati velocit\u00E0",
        "realtime_speed": "Tempo reale",
        "max_speed": "Velocit\u00E0 max",
        "avg_speed": "Velocit\u00E0 media",
        "elapsed": "Trascorso",
        "remaining": "Rimanente",
        "downloaded": "Scaricato",
        "ready": "Pronto",
        "testing": "Test in corso...",
        "complete": "Completato",
        "stopped": "Fermato",
        "calculating": "Calcolo...",
        "settings_title": "Gestione nodi",
        "node_list": "Elenco nodi",
        "node_name": "Nome nodo",
        "url_address": "Indirizzo URL",
        "def_col": "Predefinito",
        "add": "+ Aggiungi",
        "edit": "Modifica",
        "delete": "Elimina",
        "set_default": "Come predefinito",
        "move_up": "Su",
        "move_down": "Gi\u00F9",
        "close": "Chiudi",
        "auto_save_hint": "Salvataggio auto, effettivo alla chiusura",
        "please_select": "Seleziona prima un nodo",
        "enter_name": "Nome del nodo:",
        "enter_url": "URL di test:",
        "confirm_delete": 'Eliminare il nodo "{name}"?',
        "save_failed": "Salvataggio fallito",
        "save_failed_msg": "Impossibile salvare la configurazione:\n{e}",
        "timeout": "Timeout di connessione",
        "connection_failed": "Connessione fallita",
        "error": "Errore: {msg}",
        "language": "Lingua",
        "name_empty": "Il nome non può essere vuoto",
        "url_empty": "L'URL non può essere vuota",
        "no_nodes": "Nessun nodo disponibile. Aggiungi un nodo in Impostazioni.",
        "cannot_delete_last": "Impossibile eliminare l'ultimo nodo.",
    },
    "ru": {
        "lang_name": "\u0420\u0443\u0441\u0441\u043A\u0438\u0439",
        "app_title": "CDN SpeedTest v{VERSION}",
        "ip_address": "IP-\u0430\u0434\u0440\u0435\u0441",
        "fetching": "\u0417\u0430\u0433\u0440\u0443\u0437\u043A\u0430...",
        "failed": "\u041E\u0448\u0438\u0431\u043A\u0430",
        "current_node": "\u0422\u0435\u043A\u0443\u0449\u0438\u0439 \u0443\u0437\u0435\u043B",
        "settings": "\u041D\u0430\u0441\u0442\u0440\u043E\u0439\u043A\u0438",
        "stop": "\u0421\u0442\u043E\u043F",
        "start_test": "\u041D\u0430\u0447\u0430\u0442\u044C \u0442\u0435\u0441\u0442",
        "speed_results": "\u0420\u0435\u0437\u0443\u043B\u044C\u0442\u0430\u0442\u044B",
        "realtime_speed": "\u0420\u0435\u0430\u043B\u044C\u043D\u0430\u044F",
        "max_speed": "\u041C\u0430\u043A\u0441\u0438\u043C\u0430\u043B\u044C\u043D\u0430\u044F",
        "avg_speed": "\u0421\u0440\u0435\u0434\u043D\u044F\u044F",
        "elapsed": "\u041F\u0440\u043E\u0448\u043B\u043E",
        "remaining": "\u041E\u0441\u0442\u0430\u043B\u043E\u0441\u044C",
        "downloaded": "\u0417\u0430\u0433\u0440\u0443\u0436\u0435\u043D\u043E",
        "ready": "\u0413\u043E\u0442\u043E\u0432",
        "testing": "\u0422\u0435\u0441\u0442\u0438\u0440\u043E\u0432\u0430\u043D\u0438\u0435...",
        "complete": "\u0417\u0430\u0432\u0435\u0440\u0448\u0435\u043D\u043E",
        "stopped": "\u041E\u0441\u0442\u0430\u043D\u043E\u0432\u043B\u0435\u043D\u043E",
        "calculating": "\u0420\u0430\u0441\u0447\u0451\u0442...",
        "settings_title": "\u0423\u043F\u0440\u0430\u0432\u043B\u0435\u043D\u0438\u0435 \u0443\u0437\u043B\u0430\u043C\u0438",
        "node_list": "\u0421\u043F\u0438\u0441\u043E\u043A \u0443\u0437\u043B\u043E\u0432",
        "node_name": "\u0418\u043C\u044F \u0443\u0437\u043B\u0430",
        "url_address": "URL-\u0430\u0434\u0440\u0435\u0441",
        "def_col": "\u041F\u043E \u0443\u043C\u043E\u043B\u0447.",
        "add": "+ \u0414\u043E\u0431\u0430\u0432\u0438\u0442\u044C",
        "edit": "\u0418\u0437\u043C\u0435\u043D\u0438\u0442\u044C",
        "delete": "\u0423\u0434\u0430\u043B\u0438\u0442\u044C",
        "set_default": "\u041F\u043E \u0443\u043C\u043E\u043B\u0447.",
        "move_up": "\u0412\u0432\u0435\u0440\u0445",
        "move_down": "\u0412\u043D\u0438\u0437",
        "close": "\u0417\u0430\u043A\u0440\u044B\u0442\u044C",
        "auto_save_hint": "\u0410\u0432\u0442\u043E\u0441\u043E\u0445\u0440\u0430\u043D\u0435\u043D\u0438\u0435, \u0434\u0435\u0439\u0441\u0442\u0432\u0443\u0435\u0442 \u043F\u0440\u0438 \u0437\u0430\u043A\u0440\u044B\u0442\u0438\u0438",
        "please_select": "\u0421\u043D\u0430\u0447\u0430\u043B\u0430 \u0432\u044B\u0431\u0435\u0440\u0438\u0442\u0435 \u0443\u0437\u0435\u043B",
        "enter_name": "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0438\u043C\u044F \u0443\u0437\u043B\u0430:",
        "enter_url": "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 URL \u0442\u0435\u0441\u0442\u0430:",
        "confirm_delete": '\u0423\u0434\u0430\u043B\u0438\u0442\u044C \u0443\u0437\u0435\u043B "{name}"?',
        "save_failed": "\u041E\u0448\u0438\u0431\u043A\u0430 \u0441\u043E\u0445\u0440\u0430\u043D\u0435\u043D\u0438\u044F",
        "save_failed_msg": "\u041D\u0435 \u0443\u0434\u0430\u043B\u043E\u0441\u044C \u0441\u043E\u0445\u0440\u0430\u043D\u0438\u0442\u044C:\n{e}",
        "timeout": "\u041F\u0440\u0435\u0432\u044B\u0448\u0435\u043D\u043E \u0432\u0440\u0435\u043C\u044F \u043E\u0436\u0438\u0434\u0430\u043D\u0438\u044F",
        "connection_failed": "\u041E\u0448\u0438\u0431\u043A\u0430 \u043F\u043E\u0434\u043A\u043B\u044E\u0447\u0435\u043D\u0438\u044F",
        "error": "\u041E\u0448\u0438\u0431\u043A\u0430: {msg}",
        "language": "\u042F\u0437\u044B\u043A",
        "name_empty": "\u0418\u043C\u044F \u043D\u0435 \u043C\u043E\u0436\u0435\u0442 \u0431\u044B\u0442\u044C \u043F\u0443\u0441\u0442\u044B\u043C",
        "url_empty": "URL \u043D\u0435 \u043C\u043E\u0436\u0435\u0442 \u0431\u044B\u0442\u044C \u043F\u0443\u0441\u0442\u043E\u0439",
        "no_nodes": "\u041D\u0435\u0442 \u0434\u043E\u0441\u0442\u0443\u043F\u043D\u044B\u0445 \u0443\u0437\u043B\u043E\u0432. \u0414\u043E\u0431\u0430\u0432\u044C\u0442\u0435 \u0443\u0437\u0435\u043B \u0432 \u043D\u0430\u0441\u0442\u0440\u043E\u0439\u043A\u0430\u0445.",
        "cannot_delete_last": "\u041D\u0435\u043B\u044C\u0437\u044F \u0443\u0434\u0430\u043B\u0438\u0442\u044C \u043F\u043E\u0441\u043B\u0435\u0434\u043D\u0438\u0439 \u0443\u0437\u0435\u043B.",
    },
    "pl": {
        "lang_name": "Polski",
        "app_title": "CDN SpeedTest v{VERSION}",
        "ip_address": "Adres IP",
        "fetching": "Pobieranie...",
        "failed": "Nieudane",
        "current_node": "Bie\u017C\u0105cy w\u0119ze\u0142",
        "settings": "Ustawienia",
        "stop": "Zatrzymaj",
        "start_test": "Rozpocznij test",
        "speed_results": "Wyniki pr\u0119dko\u015Bci",
        "realtime_speed": "Na \u017Cywo",
        "max_speed": "Maksymalna",
        "avg_speed": "\u015Arednia",
        "elapsed": "Up\u0142yn\u0119\u0142o",
        "remaining": "Pozosta\u0142o",
        "downloaded": "Pobrano",
        "ready": "Gotowy",
        "testing": "Testowanie...",
        "complete": "Zako\u0144czono",
        "stopped": "Zatrzymano",
        "calculating": "Obliczanie...",
        "settings_title": "Zarz\u0105dzanie w\u0119z\u0142ami",
        "node_list": "Lista w\u0119z\u0142\u00F3w",
        "node_name": "Nazwa w\u0119z\u0142a",
        "url_address": "Adres URL",
        "def_col": "Domy\u015Blny",
        "add": "+ Dodaj",
        "edit": "Edytuj",
        "delete": "Usu\u0144",
        "set_default": "Ustaw domy\u015Blny",
        "move_up": "W g\u00F3r\u0119",
        "move_down": "W d\u00F3\u0142",
        "close": "Zamknij",
        "auto_save_hint": "Auto-zapis, dzia\u0142a po zamkni\u0119ciu",
        "please_select": "Najpierw wybierz w\u0119ze\u0142",
        "enter_name": "Nazwa w\u0119z\u0142a:",
        "enter_url": "URL testu:",
        "confirm_delete": 'Usun\u0105\u0107 w\u0119ze\u0142 "{name}"?',
        "save_failed": "B\u0142\u0105d zapisu",
        "save_failed_msg": "Nie mo\u017Cna zapisa\u0107 konfiguracji:\n{e}",
        "timeout": "Przekroczono czas oczekiwania",
        "connection_failed": "Po\u0142\u0105czenie nieudane",
        "error": "B\u0142\u0105d: {msg}",
        "language": "J\u0119zyk",
        "name_empty": "Nazwa nie mo\u017Ce by\u0107 pusta",
        "url_empty": "URL nie mo\u017Ce by\u0107 pusty",
        "no_nodes": "Brak dost\u0119pnych w\u0119z\u0142\u00F3w. Dodaj w\u0119ze\u0142 w Ustawieniach.",
        "cannot_delete_last": "Nie mo\u017Cna usun\u0105\u0107 ostatniego w\u0119z\u0142a.",
    },
    "ar": {
        "lang_name": "\u0627\u0644\u0639\u0631\u0628\u064A\u0629",
        "app_title": "CDN SpeedTest v{VERSION}",
        "ip_address": "\u0639\u0646\u0648\u0627\u0646 IP",
        "fetching": "\u062C\u0627\u0631\u064D \u0627\u0644\u062C\u0644\u0628...",
        "failed": "\u0641\u0634\u0644",
        "current_node": "\u0627\u0644\u0639\u0642\u062F\u0629 \u0627\u0644\u062D\u0627\u0644\u064A\u0629",
        "settings": "\u0627\u0644\u0625\u0639\u062F\u0627\u062F\u0627\u062A",
        "stop": "\u0625\u064A\u0642\u0627\u0641",
        "start_test": "\u0628\u062F\u0621 \u0627\u0644\u0627\u062E\u062A\u0628\u0627\u0631",
        "speed_results": "\u0646\u062A\u0627\u0626\u062C \u0627\u0644\u0633\u0631\u0639\u0629",
        "realtime_speed": "\u0627\u0644\u0633\u0631\u0639\u0629 \u0627\u0644\u062D\u064A\u0629",
        "max_speed": "\u0627\u0644\u0633\u0631\u0639\u0629 \u0627\u0644\u0642\u0635\u0648\u0649",
        "avg_speed": "\u0645\u062A\u0648\u0633\u0637 \u0627\u0644\u0633\u0631\u0639\u0629",
        "elapsed": "\u0627\u0644\u0645\u0646\u0642\u0636\u064A",
        "remaining": "\u0627\u0644\u0645\u062A\u0628\u0642\u064A",
        "downloaded": "\u062A\u0645 \u0627\u0644\u062A\u0646\u0632\u064A\u0644",
        "ready": "\u062C\u0627\u0647\u0632",
        "testing": "\u0627\u0644\u0627\u062E\u062A\u0628\u0627\u0631...",
        "complete": "\u0627\u0643\u062A\u0645\u0644",
        "stopped": "\u062A\u0645 \u0627\u0644\u0625\u064A\u0642\u0627\u0641",
        "calculating": "\u062C\u0627\u0631\u064D \u0627\u0644\u062D\u0633\u0627\u0628...",
        "settings_title": "\u0625\u062F\u0627\u0631\u0629 \u0627\u0644\u0639\u0642\u062F",
        "node_list": "\u0642\u0627\u0626\u0645\u0629 \u0627\u0644\u0639\u0642\u062F",
        "node_name": "\u0627\u0633\u0645 \u0627\u0644\u0639\u0642\u062F\u0629",
        "url_address": "\u0639\u0646\u0648\u0627\u0646 URL",
        "def_col": "\u0627\u0641\u062A\u0631\u0627\u0636\u064A",
        "add": "+ \u0625\u0636\u0627\u0641\u0629",
        "edit": "\u062A\u062D\u0631\u064A\u0631",
        "delete": "\u062D\u0630\u0641",
        "set_default": "\u062A\u0639\u064A\u064A\u0646 \u0627\u0641\u062A\u0631\u0627\u0636\u064A",
        "move_up": "\u0644\u0644\u0623\u0639\u0644\u0649",
        "move_down": "\u0644\u0644\u0623\u0633\u0641\u0644",
        "close": "\u0625\u063A\u0644\u0627\u0642",
        "auto_save_hint": "\u062D\u0641\u0638 \u062A\u0644\u0642\u0627\u0626\u064A\u060C \u064A\u0633\u0631\u064A \u0639\u0646\u062F \u0627\u0644\u0625\u063A\u0644\u0627\u0642",
        "please_select": "\u0627\u0644\u0631\u062C\u0627\u0621 \u062A\u062D\u062F\u064A\u062F \u0639\u0642\u062F\u0629 \u0623\u0648\u0644\u0627\u064B",
        "enter_name": "\u0623\u062F\u062E\u0644 \u0627\u0633\u0645 \u0627\u0644\u0639\u0642\u062F\u0629:",
        "enter_url": "\u0623\u062F\u062E\u0644 URL \u0627\u0644\u0627\u062E\u062A\u0628\u0627\u0631:",
        "confirm_delete": '\u0647\u0644 \u062A\u0631\u064A\u062F \u062D\u0630\u0641 \u0627\u0644\u0639\u0642\u062F\u0629 "{name}"\u061F',
        "save_failed": "\u0641\u0634\u0644 \u0627\u0644\u062D\u0641\u0638",
        "save_failed_msg": "\u062A\u0639\u0630\u0631 \u062D\u0641\u0638 \u0627\u0644\u0625\u0639\u062F\u0627\u062F\u0627\u062A:\n{e}",
        "timeout": "\u0627\u0646\u0642\u0636\u0649 \u0627\u0644\u0648\u0642\u062A",
        "connection_failed": "\u0641\u0634\u0644 \u0627\u0644\u0627\u062A\u0635\u0627\u0644",
        "error": "\u062E\u0637\u0623: {msg}",
        "language": "\u0627\u0644\u0644\u063A\u0629",
        "name_empty": "\u064A\u062C\u0628 \u0623\u0646 \u0644\u0627 \u064A\u0643\u0648\u0646 \u0627\u0644\u0627\u0633\u0645 \u0641\u0627\u0631\u063A\u064B\u0627",
        "url_empty": "\u064A\u062C\u0628 \u0623\u0646 \u0644\u0627 \u064A\u0643\u0648\u0646 URL \u0641\u0627\u0631\u063A\u064B\u0627",
        "no_nodes": "\u0644\u0627 \u062A\u0648\u062C\u062F \u0639\u0642\u062F \u0645\u062A\u0627\u062D\u0629. \u064A\u0631\u062C\u0649 \u0625\u0636\u0627\u0641\u0629 \u0639\u0642\u062F\u0629 \u0641\u064A \u0627\u0644\u0625\u0639\u062F\u0627\u062F\u0627\u062A.",
        "cannot_delete_last": "\u0644\u0627 \u064A\u0645\u0643\u0646 \u062D\u0630\u0641 \u0622\u062E\u0631 \u0639\u0642\u062F\u0629.",
    },
}

_supported_langs = sorted(LANG.keys(), key=lambda l: 0 if l == "en" else 1)
_current_lang = "en"


def set_language(lang):
    global _current_lang
    if lang in LANG:
        _current_lang = lang


def t(key, **kwargs):
    text = LANG[_current_lang].get(key, LANG["en"].get(key, key))
    if kwargs:
        text = text.format(**kwargs)
    return text


def get_config_dir():
    if hasattr(sys, "_MEIPASS"):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(filename):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


def get_dpi_factor(window):
    try:
        dpi = ctypes.windll.user32.GetDpiForWindow(ctypes.wintypes.HWND(window.winfo_id()))
        if dpi > 0:
            return dpi / 96.0
    except Exception:
        pass
    return 1.0


DEFAULT_CONFIG = {
    "defaultIndex": 0,
    "language": "en",
    "nodes": [
        {"name": "Default Node", "url": "http://ota.justin-wg.com/Download/test.dat"},
        {"name": "Speedtest Tokyo", "url": "http://speedtest1.jp/hosted/50mb.dat"},
        {"name": "Speedtest Hong Kong", "url": "http://speedtest.hk/hosted/50mb.dat"},
        {"name": "Speedtest Singapore", "url": "http://speedtest.singapore.com/hosted/50mb.dat"},
    ],
}


def load_config():
    path = os.path.join(get_config_dir(), CONFIG_FILE)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                nodes = data.get("nodes", [])
                if isinstance(nodes, list) and len(nodes) > 0:
                    return {
                        "defaultIndex": data.get("defaultIndex", 0),
                        "language": data.get("language", "en"),
                        "nodes": nodes,
                    }
        except Exception:
            pass
    return {
        "defaultIndex": DEFAULT_CONFIG["defaultIndex"],
        "language": DEFAULT_CONFIG["language"],
        "nodes": [dict(n) for n in DEFAULT_CONFIG["nodes"]],
    }


def save_config(config):
    path = os.path.join(get_config_dir(), CONFIG_FILE)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        messagebox.showerror(t("save_failed"), t("save_failed_msg", e=str(e)))


class SettingsDialog:
    BTN_KEYS = ["add", "edit", "delete", "set_default", "move_up", "move_down"]
    BTN_MAP = {"add": "_add_node", "edit": "_edit_node", "delete": "_delete_node"}

    def __init__(self, parent, config, callback):
        self.parent = parent
        self.dialog = Toplevel(parent)
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        icon_path = resource_path(ICON_FILE)
        if os.path.exists(icon_path):
            try:
                self.dialog.iconbitmap(icon_path)
            except Exception:
                pass
        self.config = config
        self.callback = callback
        self.sf = get_dpi_factor(self.dialog)
        self._btns = {}
        self._build()

    def _build(self):
        sf = self.sf
        for child in list(self.dialog.winfo_children()):
            child.destroy()
        self.dialog.title(t("settings_title"))
        self.dialog.geometry(f"{int(580*sf)}x{int(520*sf)}")

        frame = tb.Frame(self.dialog)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        lf = tb.Frame(frame)
        lf.pack(fill="x", pady=(0, 10))
        tb.Label(lf, text=t("language"),
                 font=("Microsoft YaHei UI", 8),
                 foreground="#999").pack(side="left")
        lang_names = [LANG[code]["lang_name"] for code in _supported_langs]
        self.lang_combo = tb.Combobox(lf, values=lang_names, state="readonly", width=22)
        self.lang_combo.pack(side="left", padx=(8, 0))
        ci = _supported_langs.index(self.config.get("language", "en"))
        self.lang_combo.current(ci)
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_lang_change)

        tb.Label(frame, text=t("node_list"),
                 font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w")

        lf2 = tb.Frame(frame)
        lf2.pack(fill="both", expand=True, pady=(8, 0))

        self.tree = tb.Treeview(lf2, columns=("name","url","default"), show="headings", height=8)
        for c, w in [("name",150),("url",300),("default",50)]:
            self.tree.column(c, width=w, minwidth=max(w//3,40),
                             anchor="center" if c=="default" else "w")
        self._tree_headings()
        sb = tb.Scrollbar(lf2, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._refresh_list()

        br = tb.Frame(frame)
        br.pack(fill="x", pady=(8, 0))
        self._btns.clear()
        for k in self.BTN_KEYS:
            cmd_name = self.BTN_MAP.get(k, f"_{k}")
            b = tb.Button(br, text=t(k), command=getattr(self, cmd_name))
            b.pack(side="left", padx=2, ipadx=4)
            self._btns[k] = b

        btm = tb.Frame(frame)
        btm.pack(fill="x", pady=(8, 0))
        self._hint = tb.Label(btm, text=t("auto_save_hint"),
                              font=("Microsoft YaHei UI", 8),
                              foreground="#999")
        self._hint.pack(side="left")
        self._close = tb.Button(btm, text=t("close"),
                                command=self.dialog.destroy)
        self._close.pack(side="right")

    def _tree_headings(self):
        self.tree.heading("name", text=t("node_name"))
        self.tree.heading("url", text=t("url_address"))
        self.tree.heading("default", text=t("def_col"))

    def _refresh_lang(self):
        self.dialog.title(t("settings_title"))
        for k, b in self._btns.items():
            b.configure(text=t(k))
        self._hint.configure(text=t("auto_save_hint"))
        self._close.configure(text=t("close"))
        self._tree_headings()

    def _on_lang_change(self, event=None):
        idx = self.lang_combo.current()
        code = _supported_langs[idx]
        self.config["language"] = code
        set_language(code)
        save_config(self.config)
        self.callback(self.config)
        self._refresh_lang()

    def _refresh_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for i, node in enumerate(self.config["nodes"]):
            m = "\u25CF" if i == self.config["defaultIndex"] else ""
            self.tree.insert("", "end", iid=str(i), values=(node["name"], node["url"], m))
        if self.tree.get_children():
            self.tree.selection_set(str(self.config["defaultIndex"]))

    def _get_selected_idx(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("", t("please_select"), parent=self.dialog)
            return None
        return int(sel[0])

    def _add_node(self):
        name = simpledialog.askstring("", t("enter_name"), parent=self.dialog)
        if name is None:
            return
        name = name.strip()
        if not name:
            messagebox.showwarning("", t("name_empty"), parent=self.dialog)
            return
        url = simpledialog.askstring("", t("enter_url"), parent=self.dialog)
        if url is None:
            return
        url = url.strip()
        if not url:
            messagebox.showwarning("", t("url_empty"), parent=self.dialog)
            return
        self.config["nodes"].append({"name": name, "url": url})
        self._refresh_list(); save_config(self.config); self.callback(self.config)

    def _edit_node(self):
        idx = self._get_selected_idx()
        if idx is None:
            return
        n = self.config["nodes"][idx]
        name = simpledialog.askstring("", t("enter_name"), initialvalue=n["name"], parent=self.dialog)
        if name is None:
            return
        name = name.strip()
        if not name:
            messagebox.showwarning("", t("name_empty"), parent=self.dialog)
            return
        url = simpledialog.askstring("", t("enter_url"), initialvalue=n["url"], parent=self.dialog)
        if url is None:
            return
        url = url.strip()
        if not url:
            messagebox.showwarning("", t("url_empty"), parent=self.dialog)
            return
        self.config["nodes"][idx] = {"name": name, "url": url}
        self._refresh_list(); save_config(self.config); self.callback(self.config)

    def _delete_node(self):
        idx = self._get_selected_idx()
        if idx is None:
            return
        if len(self.config["nodes"]) <= 1:
            messagebox.showwarning("", t("cannot_delete_last"), parent=self.dialog)
            return
        nm = self.config["nodes"][idx]["name"]
        if messagebox.askyesno("", t("confirm_delete", name=nm), parent=self.dialog):
            self.config["nodes"].pop(idx)
            if self.config["defaultIndex"] >= len(self.config["nodes"]):
                self.config["defaultIndex"] = max(0, len(self.config["nodes"]) - 1)
            elif self.config["defaultIndex"] > idx:
                self.config["defaultIndex"] -= 1
            self._refresh_list(); save_config(self.config); self.callback(self.config)

    def _set_default(self):
        idx = self._get_selected_idx()
        if idx is None:
            return
        self.config["defaultIndex"] = idx
        self._refresh_list(); save_config(self.config); self.callback(self.config)

    def _move_up(self):
        idx = self._get_selected_idx()
        if idx is None or idx == 0:
            return
        ns = self.config["nodes"]
        ns[idx], ns[idx-1] = ns[idx-1], ns[idx]
        if self.config["defaultIndex"] == idx:
            self.config["defaultIndex"] = idx - 1
        elif self.config["defaultIndex"] == idx - 1:
            self.config["defaultIndex"] = idx
        self._refresh_list(); self.tree.selection_set(str(idx - 1))
        save_config(self.config); self.callback(self.config)

    def _move_down(self):
        idx = self._get_selected_idx()
        if idx is None or idx >= len(self.config["nodes"]) - 1:
            return
        ns = self.config["nodes"]
        ns[idx], ns[idx+1] = ns[idx+1], ns[idx]
        if self.config["defaultIndex"] == idx:
            self.config["defaultIndex"] = idx + 1
        elif self.config["defaultIndex"] == idx + 1:
            self.config["defaultIndex"] = idx
        self._refresh_list(); self.tree.selection_set(str(idx + 1))
        save_config(self.config); self.callback(self.config)


class MetricCard(tb.LabelFrame):
    def __init__(self, master, value="--"):
        super().__init__(master, text="")
        self.title_label = tb.Label(self, text="",
                                    font=("Microsoft YaHei UI", 8),
                                    foreground="#999")
        self.title_label.pack(anchor="w", padx=8, pady=(8, 0))
        self.value_label = tb.Label(self, text=value,
                                    font=("Consolas", 13, "bold"))
        self.value_label.pack(anchor="w", fill="x", padx=8, pady=(0, 8))

    def set_title(self, text):
        self.title_label.configure(text=text)

    def set_value(self, text):
        self.value_label.configure(text=text)


class SpeedTester:
    def __init__(self, root, dpi=96):
        self.root = root
        self.dpi = dpi
        self.config = load_config()
        set_language(self.config.get("language", "en"))
        sf = dpi / 96.0
        self.root.geometry(f"{int(620*sf)}x{int(480*sf)}")
        self.root.resizable(False, False)
        icon_path = resource_path(ICON_FILE)
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass
        self.current_node_idx = self._clamp(self.config["defaultIndex"])
        self.downloading = False
        self._stop_event = False
        self._test_error = False
        self._test_gen = 0
        self.start_time = 0
        self.total_bytes = 0
        self.last_bytes = 0
        self.last_time = 0
        self.max_speed = 0.0
        self.avg_speed = 0.0
        self.realtime_speed = 0.0
        self.content_length = 0
        self.display_timer = None
        self.metric_cards = {}
        self._speed_frame = None
        self._setup_ui()

    def _clamp(self, idx):
        ns = self.config["nodes"]
        return 0 if idx < 0 or idx >= len(ns) else idx

    def _setup_ui(self):
        self.root.title(t("app_title", VERSION=VERSION))
        main = tb.Frame(self.root)
        main.pack(fill="both", expand=True, padx=16, pady=16)

        ic = tb.LabelFrame(main, text="")
        ic.pack(fill="x", pady=(0, 10))
        ir = tb.Frame(ic); ir.pack(fill="x", padx=12, pady=(8, 4))
        tb.Label(ir, text=t("ip_address"),
                 font=("Microsoft YaHei UI", 8),
                 foreground="#999").pack(side="left")
        bf = tb.Frame(ir); bf.pack(side="right")
        self.settings_btn = tb.Button(bf, text=t("settings"),
                                       command=self._open_settings,
                                       bootstyle="secondary,outline")
        self.settings_btn.pack(side="left", padx=2)
        self.stop_btn = tb.Button(bf, text=t("stop"),
                                   command=self.stop_test,
                                   bootstyle="danger,outline", state=DISABLED)
        self.stop_btn.pack(side="left", padx=2)
        self.start_btn = tb.Button(bf, text=t("start_test"),
                                    command=self.start_test,
                                    bootstyle="success")
        self.start_btn.pack(side="left", padx=2)
        iv = tb.Frame(ic); iv.pack(fill="x", padx=12, pady=(2, 8))
        self.ip_label = tb.Label(iv, text=t("fetching"),
                                 font=("Consolas", 16, "bold"))
        self.ip_label.pack(side="left")
        self.location_label = tb.Label(iv, text="",
                                       font=("Microsoft YaHei UI", 9),
                                       foreground="#999")
        self.location_label.pack(side="left", padx=(12,0), pady=(4,0))

        self._speed_frame = tb.LabelFrame(main, text=f"  {t('speed_results')}  ")
        self._speed_frame.pack(fill="both", expand=True, pady=(0, 10),
                               ipadx=12, ipady=12)
        gd = tb.Frame(self._speed_frame)
        gd.pack(fill="both", expand=True, padx=4, pady=4)

        self.card_keys = [("realtime_speed","realtime"),("max_speed","max"),
                          ("avg_speed","avg"),("elapsed","elapsed"),
                          ("remaining","remain"),("downloaded","downloaded")]
        for i, (lk, key) in enumerate(self.card_keys):
            r, c = i // 3, i % 3
            card = MetricCard(gd, "--")
            card.set_title(t(lk))
            card.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
            gd.columnconfigure(c, weight=1)
            self.metric_cards[key] = card
        gd.rowconfigure(0, weight=1); gd.rowconfigure(1, weight=1)

        self.pf = tb.Frame(main)
        self.progress = tb.Progressbar(self.pf, mode="determinate", bootstyle=INFO)
        self.progress.pack(side="left", fill="x", expand=True)
        self.pct_label = tb.Label(self.pf, text="", font=("Microsoft YaHei UI", 9))
        self.pct_label.pack(side="right", padx=(4, 0))
        sf2 = tb.Frame(main); sf2.pack(fill="x")
        self.status_label = tb.Label(sf2, text=t("ready"),
                                     font=("Microsoft YaHei UI", 8),
                                     foreground="#999")
        self.status_label.pack(side="left")
        self._fetch_ip_info()

    def _apply_language(self):
        self.root.title(t("app_title", VERSION=VERSION))
        self.settings_btn.configure(text=t("settings"))
        self.stop_btn.configure(text=t("stop"))
        self.start_btn.configure(text=t("start_test"))
        self._speed_frame.configure(text=f"  {t('speed_results')}  ")
        for lk, key in self.card_keys:
            self.metric_cards[key].set_title(t(lk))

    def _open_settings(self):
        SettingsDialog(self.root, self.config, self._on_config_updated)

    def _on_config_updated(self, config):
        self.config = config
        set_language(config.get("language", "en"))
        self.current_node_idx = self._clamp(config["defaultIndex"])
        self._apply_language()

    def _fetch_ip_info(self):
        def _task():
            try:
                r = requests.get("http://ip-api.com/json", timeout=10)
                d = r.json(); ip = d.get("query", "")
                parts = [p for p in [d.get("country"), d.get("regionName"), d.get("city")] if p]
                loc = " \u2014 ".join(parts) if parts else ""
                self.root.after(0, lambda i=ip, l=loc: (
                    self.ip_label.configure(text=i),
                    self.location_label.configure(text=l)))
            except Exception:
                try:
                    r = requests.get("https://api.ipify.org?format=json", timeout=8)
                    ip = r.json().get("ip", "")
                    self.root.after(0, lambda i=ip: (
                        self.ip_label.configure(text=i),
                        self.location_label.configure(text="")))
                except Exception:
                    self.root.after(0, lambda: self.ip_label.configure(text=t("failed")))
        threading.Thread(target=_task, daemon=True).start()

    def _format_speed(self, bps):
        if bps >= 1024*1024: return f"{bps/(1024*1024):.2f} MB/s"
        if bps >= 1024: return f"{bps/1024:.2f} KB/s"
        return f"{bps:.1f} B/s"

    def _format_bytes(self, b):
        if b >= 1024*1024*1024: return f"{b/(1024*1024*1024):.2f} GB"
        if b >= 1024*1024: return f"{b/(1024*1024):.2f} MB"
        if b >= 1024: return f"{b/1024:.2f} KB"
        return f"{b} B"

    @staticmethod
    def _fmt_time(sec):
        if sec is None or sec < 0: return "--"
        m, s = divmod(int(sec), 60)
        h, m = divmod(m, 60)
        return f"{h}h{m:02d}m{s:02d}s" if h else f"{m:02d}m{s:02d}s"

    def start_test(self):
        if self.downloading: return
        if not self.config["nodes"]:
            messagebox.showwarning("", t("no_nodes"))
            return
        self.downloading = True; self._stop_event = False
        self.start_time = self.last_time = time.time()
        self.total_bytes = self.last_bytes = 0
        self.max_speed = self.avg_speed = self.realtime_speed = 0.0
        self.content_length = 0
        self._test_error = False
        self._test_gen += 1
        gen = self._test_gen
        self.start_btn.configure(state=DISABLED)
        self.stop_btn.configure(state=NORMAL)
        self.settings_btn.configure(state=DISABLED)
        self.pf.pack(fill="x", pady=(0, 6))
        self.progress.configure(value=0)
        self.pct_label.configure(text="0%")
        self.status_label.configure(text=t("testing"), foreground="#2b8a3e")
        self.metric_cards["elapsed"].set_value(self._fmt_time(0))
        self.metric_cards["remain"].set_value(t("calculating"))
        threading.Thread(target=self._download_task, daemon=True, args=(gen,)).start()
        self._update_display()

    def stop_test(self):
        self._stop_event = True; self.downloading = False
        self._cleanup_stop()

    def _cleanup_stop(self):
        if self.display_timer:
            self.root.after_cancel(self.display_timer); self.display_timer = None
        self.start_btn.configure(state=NORMAL)
        self.stop_btn.configure(state=DISABLED)
        self.settings_btn.configure(state=NORMAL)
        self.pf.pack_forget()
        if not self._test_error:
            self.status_label.configure(
                text=t("complete") if not self._stop_event else t("stopped"),
                foreground="#2b8a3e" if not self._stop_event else "#c92a2a")

    def _download_task(self, gen):
        url = self.config["nodes"][self.current_node_idx]["url"]
        try:
            with requests.Session() as s:
                a = requests.adapters.HTTPAdapter(pool_connections=1, pool_maxsize=1, max_retries=0, pool_block=True)
                s.mount("http://", a); s.mount("https://", a)
                with s.get(url, stream=True, timeout=(10, 30)) as r:
                    r.raise_for_status()
                    try:
                        self.content_length = int(r.headers.get("Content-Length", 0))
                        if self.content_length <= 0: self.content_length = 0
                    except Exception: self.content_length = 0
                    for ch in r.iter_content(chunk_size=CHUNK_SIZE):
                        if self._stop_event: break
                        if ch:
                            now = time.time(); self.total_bytes += len(ch)
                            el = now - self.last_time
                            if el >= 0.8:
                                sp = (self.total_bytes - self.last_bytes) / el
                                self.realtime_speed = sp
                                if sp > self.max_speed: self.max_speed = sp
                                self.last_bytes = self.total_bytes; self.last_time = now
                                te = now - self.start_time
                                if te > 0: self.avg_speed = self.total_bytes / te
                    te = time.time() - self.start_time
                    if te > 0: self.avg_speed = self.total_bytes / te
        except requests.exceptions.Timeout:
            self._test_error = True
            self.root.after(0, lambda: self.status_label.configure(text=t("timeout"), foreground="#c92a2a"))
        except requests.exceptions.ConnectionError:
            self._test_error = True
            self.root.after(0, lambda: self.status_label.configure(text=t("connection_failed"), foreground="#c92a2a"))
        except Exception as e:
            self._test_error = True
            m = str(e)[:50]
            self.root.after(0, lambda msg=m: self.status_label.configure(text=t("error", msg=msg), foreground="#c92a2a"))
        finally:
            self.root.after(0, lambda g=gen: self._finish_test(g))

    def _finish_test(self, gen):
        if gen != self._test_gen or self._stop_event: return
        self.downloading = False
        self._cleanup_stop()

    def _update_display(self):
        if not self.downloading: return
        now = time.time(); el = now - self.start_time
        self.metric_cards["realtime"].set_value(self._format_speed(self.realtime_speed))
        self.metric_cards["max"].set_value(self._format_speed(self.max_speed))
        self.metric_cards["avg"].set_value(self._format_speed(self.avg_speed))
        self.metric_cards["elapsed"].set_value(self._fmt_time(el))
        self.metric_cards["downloaded"].set_value(self._format_bytes(self.total_bytes))
        if self.content_length > 0:
            pct = min(100, int(self.total_bytes * 100 / self.content_length))
            self.progress.configure(value=pct)
            self.pct_label.configure(text=f"{pct}%")
        else:
            self.pct_label.configure(text="")
        if self.realtime_speed > 0:
            if self.content_length > 0:
                rm = max(0, self.content_length - self.total_bytes) / self.realtime_speed
            elif self.total_bytes > 0:
                rm = max(0, self.total_bytes / self.realtime_speed - el)
            else: rm = None
            self.metric_cards["remain"].set_value(self._fmt_time(rm))
        else:
            self.metric_cards["remain"].set_value(t("calculating"))
        self.display_timer = self.root.after(UPDATE_INTERVAL, self._update_display)


def _get_monitor_dpi():
    try:
        hwnd = ctypes.windll.user32.GetDesktopWindow()
        monitor = ctypes.windll.user32.MonitorFromWindow(hwnd, 2)
        dx = ctypes.c_uint(); dy = ctypes.c_uint()
        ctypes.windll.shcore.GetDpiForMonitor(monitor, 0, ctypes.byref(dx), ctypes.byref(dy))
        return dx.value
    except Exception:
        return 96

def main():
    dpi = _get_monitor_dpi()
    root = tk.Tk()
    root.tk.call("tk", "scaling", dpi / 72.0)
    tb.Style(theme=THEME)
    SpeedTester(root, dpi)
    root.mainloop()


if __name__ == "__main__":
    main()
