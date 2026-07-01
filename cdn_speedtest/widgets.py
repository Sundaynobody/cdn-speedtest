import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, simpledialog, Toplevel
from .i18n import t, set_language, _supported_langs, LANG
from .utils import get_dpi_factor, set_window_icon, resource_path, _UI_FONT, _MONO_FONT, save_config


class SettingsDialog:
    BTN_KEYS = ["add", "edit", "delete", "set_default", "move_up", "move_down"]
    BTN_MAP = {"add": "_add_node", "edit": "_edit_node", "delete": "_delete_node"}

    def __init__(self, parent, config, callback):
        self.parent = parent
        self.dialog = Toplevel(parent)
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        set_window_icon(self.dialog)
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
                 font=(_UI_FONT, 8),
                 foreground="#999").pack(side="left")
        lang_names = [LANG[code]["lang_name"] for code in _supported_langs]
        self.lang_combo = tb.Combobox(lf, values=lang_names, state="readonly", width=22)
        self.lang_combo.pack(side="left", padx=(8, 0))
        ci = _supported_langs.index(self.config.get("language", "en"))
        self.lang_combo.current(ci)
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_lang_change)

        tb.Label(frame, text=t("node_list"),
                 font=(_UI_FONT, 11, "bold")).pack(anchor="w")

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
                              font=(_UI_FONT, 8),
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
                                    font=(_UI_FONT, 8),
                                    foreground="#999")
        self.title_label.pack(anchor="w", padx=8, pady=(8, 0))
        self.value_label = tb.Label(self, text=value,
                                    font=(_MONO_FONT, 13, "bold"))
        self.value_label.pack(anchor="w", fill="x", padx=8, pady=(0, 8))

    def set_title(self, text):
        self.title_label.configure(text=text)

    def set_value(self, text):
        self.value_label.configure(text=text)
