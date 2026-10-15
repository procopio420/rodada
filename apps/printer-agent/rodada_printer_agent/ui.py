"""Optional diagnostic UI; reads only the public status, never the protected state."""

import json
import tkinter as tk

from .windows_store import ROOT


def main() -> None:
    window = tk.Tk()
    window.title("Rodada Impressoras")
    window.geometry("520x300")
    text = tk.StringVar(value="Aguardando serviço…")
    tk.Label(window, text="Rodada Impressoras", font=("Segoe UI", 20, "bold")).pack(pady=16)
    tk.Label(window, textvariable=text, font=("Segoe UI", 13), wraplength=480).pack(
        padx=20, pady=16
    )

    def refresh() -> None:
        try:
            data = json.loads((ROOT / "diagnostics/status.json").read_text())
            code = data.get("code", "")
            message = {
                "ONLINE": "Computador conectado. Pode fechar esta janela.",
                "AUTHORIZATION_LOST": "Acesso encerrado. Solicite novo pareamento ao responsável.",
                "PENDING_PAIRING": "Abra a Gerência do estabelecimento → Impressoras.\nCódigo: "
                + code,
            }.get(data.get("state"), "Serviço aguardando conexão com Rodada.")
            if code:
                message += "\nValidade: " + data.get("expires_at", "")
            text.set(message)
        except (OSError, ValueError):
            text.set("Serviço ainda sem diagnóstico. Confira a instalação.")
        window.after(2000, refresh)

    refresh()
    tk.Button(window, text="Fechar", command=window.destroy).pack(pady=12)
    window.mainloop()


if __name__ == "__main__":
    main()
