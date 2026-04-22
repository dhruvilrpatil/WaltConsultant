"""Documents management screen for WaltConsultant."""

from __future__ import annotations

import io
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk

from PIL import Image, ImageTk

from components.button import WaltButton
from components.card import WaltCard
from components.input import WaltInput
from components.modal import WaltConfirmDialog, WaltModal
from components.toast import WaltToast
from database.connection import get_db_manager
from models.document import DOCUMENT_MODEL
from utils.constants import ROLE_PERMISSIONS
from utils.theme import PALETTE


DOCUMENT_TYPES = ["ID Proof", "Address Proof", "Income Proof", "Bank Statement", "Agreement", "Other"]
REFERENCE_TYPES = ["customer", "loan"]


class DocumentsScreen(tk.Frame):
    def __init__(self, parent, current_user_id: int | None, role: str):
        super().__init__(parent, bg=PALETTE.window_bg)
        self.current_user_id = current_user_id
        self.role = role
        self.db = get_db_manager()
        self.documents_cache: list[dict] = []

        self._build()
        self.refresh()

    def _can(self, action: str) -> bool:
        return action in ROLE_PERMISSIONS.get(self.role, {}).get("documents", [])

    def _toast(self, message: str, kind: str = "info") -> None:
        WaltToast(self.winfo_toplevel(), message, kind).show()

    def _build(self) -> None:
        header = tk.Frame(self, bg=PALETTE.window_bg)
        header.pack(fill="x", padx=20, pady=(16, 10))

        tk.Label(header, text="Documents", bg=PALETTE.window_bg, fg=PALETTE.text_primary, font=("SF Pro Rounded", 22, "bold")).pack(side="left")

        controls = tk.Frame(header, bg=PALETTE.window_bg)
        controls.pack(side="right")

        self.ref_type_var = tk.StringVar(value="")
        ttk.Combobox(controls, values=[""] + REFERENCE_TYPES, textvariable=self.ref_type_var, width=10, state="readonly", style="Walt.TCombobox").pack(side="left", padx=(0, 8))

        self.doc_type_var = tk.StringVar(value="")
        ttk.Combobox(controls, values=[""] + DOCUMENT_TYPES, textvariable=self.doc_type_var, width=14, state="readonly", style="Walt.TCombobox").pack(side="left", padx=(0, 8))

        WaltButton(controls, text="Apply Filters", style="secondary", command=self.refresh).pack(side="left", padx=(0, 8))

        upload_btn = WaltButton(controls, text="Upload Document", style="primary", command=self._open_upload_modal)
        upload_btn.pack(side="left")
        if not self._can("create"):
            upload_btn.configure(state="disabled")

        upload_zone = WaltCard(self, padding=0, radius=14, border_color=PALETTE.divider, card_bg=PALETTE.input_bg, outer_bg=PALETTE.window_bg)
        upload_zone.pack(fill="x", padx=20, pady=(0, 10))
        tk.Label(upload_zone.content, text="Drop files here or click Upload Document", bg=PALETTE.input_bg, fg=PALETTE.text_secondary, font=("SF Pro Rounded", 11), pady=12).pack()

        grid_wrap = tk.Frame(self, bg=PALETTE.window_bg)
        grid_wrap.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.canvas = tk.Canvas(grid_wrap, bg=PALETTE.window_bg, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        scroll = tk.Scrollbar(grid_wrap, orient="vertical", command=self.canvas.yview)
        scroll.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=scroll.set)

        self.grid_frame = tk.Frame(self.canvas, bg=PALETTE.window_bg)
        self.window_id = self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")

        self.grid_frame.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.window_id, width=e.width))

    def refresh(self) -> None:
        ref_type = self.ref_type_var.get().strip()
        doc_type = self.doc_type_var.get().strip()

        self.documents_cache = DOCUMENT_MODEL.list_documents(reference_type=ref_type, document_type=doc_type)
        self._render_cards()

    def _render_cards(self) -> None:
        for child in self.grid_frame.winfo_children():
            child.destroy()

        if not self.documents_cache:
            tk.Label(self.grid_frame, text="No documents found", bg=PALETTE.window_bg, fg=PALETTE.text_secondary, font=("SF Pro Rounded", 12)).pack(anchor="w", pady=8)
            return

        columns = 3
        for index, doc in enumerate(self.documents_cache):
            row = index // columns
            col = index % columns

            card = WaltCard(self.grid_frame, padding=0, radius=14, border_color=PALETTE.divider, card_bg=PALETTE.window_bg, outer_bg=PALETTE.window_bg, width=250, height=170)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            card.grid_propagate(False)

            icon = "PDF" if str(doc.get("file_name", "")).lower().endswith(".pdf") else "IMG"
            tk.Label(card.content, text=icon, bg=PALETTE.input_bg, fg=PALETTE.primary, font=("SF Pro Rounded", 11, "bold"), padx=8, pady=4).pack(anchor="w", padx=10, pady=(10, 6))
            tk.Label(card.content, text=doc.get("document_name") or doc.get("file_name"), bg=PALETTE.window_bg, fg=PALETTE.text_primary, font=("SF Pro Rounded", 11, "bold"), wraplength=220, justify="left").pack(anchor="w", padx=10)
            tk.Label(card.content, text=f"{doc.get('document_type', '-')}", bg=PALETTE.window_bg, fg=PALETTE.text_secondary, font=("SF Pro Rounded", 10)).pack(anchor="w", padx=10, pady=(4, 0))
            tk.Label(card.content, text=f"Uploaded: {doc.get('uploaded_at', '-')}", bg=PALETTE.window_bg, fg=PALETTE.text_secondary, font=("SF Pro Rounded", 9)).pack(anchor="w", padx=10, pady=(2, 8))

            actions = tk.Frame(card.content, bg=PALETTE.window_bg)
            actions.pack(fill="x", padx=10, pady=(0, 10))
            WaltButton(actions, text="View", style="secondary", command=lambda d=doc: self._view_document(d)).pack(side="left")
            WaltButton(actions, text="Download", style="secondary", command=lambda d=doc: self._download_document(d)).pack(side="left", padx=(6, 0))
            if self._can("delete"):
                WaltButton(actions, text="Delete", style="destructive", command=lambda d=doc: self._delete_document(d)).pack(side="left", padx=(6, 0))

        for col in range(columns):
            self.grid_frame.grid_columnconfigure(col, weight=1)

    def _open_upload_modal(self) -> None:
        selected = filedialog.askopenfilename(title="Choose file to upload")
        if not selected:
            return

        modal = WaltModal(self.winfo_toplevel(), "Upload Document", width=560, height=430)

        name_input = WaltInput(modal.content, placeholder="Document Name")
        name_input.pack(fill="x", pady=6)
        name_input.set(Path(selected).name)

        tk.Label(modal.content, text="Reference Type", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(anchor="w")
        ref_var = tk.StringVar(value=REFERENCE_TYPES[0])
        ttk.Combobox(modal.content, values=REFERENCE_TYPES, textvariable=ref_var, state="readonly", style="Walt.TCombobox").pack(fill="x", pady=(2, 8))

        reference_id = WaltInput(modal.content, placeholder="Reference ID (Customer or Loan ID)")
        reference_id.pack(fill="x", pady=6)

        tk.Label(modal.content, text="Document Type", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(anchor="w")
        dtype_var = tk.StringVar(value=DOCUMENT_TYPES[0])
        ttk.Combobox(modal.content, values=DOCUMENT_TYPES, textvariable=dtype_var, state="readonly", style="Walt.TCombobox").pack(fill="x", pady=(2, 8))

        tk.Label(modal.content, text=f"Selected file: {Path(selected).name}", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(anchor="w", pady=(10, 0))

        def upload_now() -> None:
            try:
                doc_name = name_input.get() or Path(selected).name
                DOCUMENT_MODEL.upload_document(
                    reference_type=ref_var.get(),
                    reference_id=int(reference_id.get()),
                    document_name=doc_name,
                    document_type=dtype_var.get(),
                    file_path=selected,
                    uploaded_by=self.current_user_id,
                )
                modal.destroy()
                self.refresh()
                self._toast("Document uploaded", "success")
            except Exception as error:
                self._toast(str(error), "danger")

        WaltButton(modal.footer, text="Cancel", style="secondary", command=modal.destroy).pack(side="right", padx=(8, 0))
        WaltButton(modal.footer, text="Upload", style="primary", command=upload_now).pack(side="right")

    def _view_document(self, doc: dict) -> None:
        row = DOCUMENT_MODEL.get_document(int(doc["id"]))
        if not row:
            self._toast("Document not found", "danger")
            return

        viewer = WaltModal(self.winfo_toplevel(), f"View: {row.get('document_name', row.get('file_name'))}", width=700, height=560)

        data = row.get("file_data")
        name = str(row.get("file_name", "")).lower()

        if data and any(name.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]):
            try:
                image = Image.open(io.BytesIO(data)).convert("RGB")
                image.thumbnail((640, 480))
                photo = ImageTk.PhotoImage(image)
                preview = tk.Label(viewer.content, image=photo, bg=PALETTE.window_bg)
                preview.image = photo
                preview.pack(pady=10)
            except Exception:
                tk.Label(viewer.content, text="Unable to render image preview", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(anchor="w")
        else:
            info = tk.Text(viewer.content, bg=PALETTE.input_bg, fg=PALETTE.text_primary, relief="flat", height=14)
            info.pack(fill="both", expand=True)
            info.insert(
                "1.0",
                f"Document ID: {row.get('document_id')}\n"
                f"Name: {row.get('document_name')}\n"
                f"Type: {row.get('document_type')}\n"
                f"Reference: {row.get('reference_type')} #{row.get('reference_id')}\n"
                f"File Name: {row.get('file_name')}\n"
                f"File Size: {row.get('file_size')} bytes\n"
                f"Uploaded At: {row.get('uploaded_at')}\n"
                "\nBinary preview unavailable for this file type.",
            )
            info.configure(state="disabled")

        WaltButton(viewer.footer, text="Close", style="secondary", command=viewer.destroy).pack(side="right")

    def _download_document(self, doc: dict) -> None:
        row = DOCUMENT_MODEL.get_document(int(doc["id"]))
        if not row:
            self._toast("Document not found", "danger")
            return

        target = filedialog.asksaveasfilename(title="Save Document", initialfile=row.get("file_name") or "document.bin")
        if not target:
            return

        try:
            Path(target).write_bytes(row.get("file_data") or b"")
            self._toast("Document downloaded", "success")
        except Exception as error:
            self._toast(str(error), "danger")

    def _delete_document(self, doc: dict) -> None:
        def delete_now():
            try:
                DOCUMENT_MODEL.delete_document(int(doc["id"]), self.current_user_id)
                self.refresh()
                self._toast("Document deleted", "success")
            except Exception as error:
                self._toast(str(error), "danger")

        WaltConfirmDialog(self.winfo_toplevel(), "Delete Document", "Delete this document permanently?", delete_now)
