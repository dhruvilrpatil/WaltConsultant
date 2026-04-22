"""Main application orchestration for WaltConsultant."""

from __future__ import annotations

import tkinter as tk

from components.sidebar import WaltSidebar
from components.topbar import WaltTopBar
from components.toast import WaltToast
from database.migrations import run_migrations
from models.repayment import REPAYMENT_MODEL
from screens.customers import CustomersScreen
from screens.dashboard import DashboardScreen
from screens.documents import DocumentsScreen
from screens.login import LoginScreen
from screens.loans import LoansScreen
from screens.repayments import RepaymentsScreen
from screens.reports import ReportsScreen
from screens.settings import SettingsScreen
from screens.signup import SignupScreen
from screens.splash import SplashScreen
from utils.auth import AUTH_SERVICE
from utils.constants import APP_NAME
from utils.theme import PALETTE, SIZING, setup_ttk_styles


class WaltConsultantApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_NAME)
        self.root.configure(bg=PALETTE.window_bg)
        self.root.minsize(1280, 800)
        self.root.geometry("1280x800")

        setup_ttk_styles(root)

        self.current_auth_screen: tk.Frame | None = None
        self.current_main_screen: tk.Frame | None = None

        self.main_shell: tk.Frame | None = None
        self.sidebar: WaltSidebar | None = None
        self.topbar: WaltTopBar | None = None
        self.content_host: tk.Frame | None = None

        self._bootstrap_data()
        self.show_splash()

    def _bootstrap_data(self) -> None:
        run_migrations()
        REPAYMENT_MODEL.update_overdue_statuses(None)

    def _show_toast(self, message: str, kind: str = "info") -> None:
        WaltToast(self.root, message, kind).show()

    def _clear_root(self) -> None:
        for child in self.root.winfo_children():
            child.destroy()

    def show_splash(self) -> None:
        self._clear_root()
        splash = SplashScreen(self.root, on_complete=self.show_login)
        splash.pack(fill="both", expand=True)
        self.current_auth_screen = splash

    def show_login(self) -> None:
        self._clear_root()
        login = LoginScreen(self.root, on_login=self.handle_login, on_show_signup=self.show_signup)
        login.pack(fill="both", expand=True)
        self.current_auth_screen = login

    def show_signup(self) -> None:
        self._clear_root()
        signup = SignupScreen(self.root, on_create_account=self.handle_signup, on_show_login=self.show_login)
        signup.pack(fill="both", expand=True)
        self.current_auth_screen = signup

    def handle_signup(self, payload: dict) -> None:
        try:
            AUTH_SERVICE.register_user(payload)
            user = AUTH_SERVICE.login(payload["username"], payload["password"])
            if not user:
                raise ValueError("Account created but automatic sign-in failed.")
            self._show_toast("Account created successfully", "success")
            self.show_main_shell()
        except Exception as error:
            if isinstance(self.current_auth_screen, SignupScreen):
                self.current_auth_screen.show_error(str(error))
            else:
                self._show_toast(str(error), "danger")

    def handle_login(self, username_or_email: str, password: str) -> None:
        user = AUTH_SERVICE.login(username_or_email, password)
        if not user:
            if isinstance(self.current_auth_screen, LoginScreen):
                self.current_auth_screen.show_error("Invalid credentials or inactive account")
            return

        self._show_toast("Signed in successfully", "success")
        self.show_main_shell()

    def show_main_shell(self) -> None:
        self._clear_root()

        shell = tk.Frame(self.root, bg=PALETTE.window_bg)
        shell.pack(fill="both", expand=True)
        self.main_shell = shell

        self.sidebar = WaltSidebar(shell, on_navigate=self._on_navigate)
        self.sidebar.pack(side="left", fill="y")

        right = tk.Frame(shell, bg=PALETTE.window_bg)
        right.pack(side="left", fill="both", expand=True)

        self.topbar = WaltTopBar(right)
        self.topbar.pack(fill="x", side="top")
        self.topbar.set_user(AUTH_SERVICE.session.full_name)

        self.content_host = tk.Frame(right, bg=PALETTE.window_bg)
        self.content_host.pack(fill="both", expand=True)

        self._mount_screen("Dashboard")

    def _on_navigate(self, item_name: str) -> None:
        if item_name == "Logout":
            AUTH_SERVICE.logout()
            self._show_toast("Logged out", "info")
            self.show_login()
            return

        self._mount_screen(item_name)

    def _mount_screen(self, page_name: str) -> None:
        if not self.content_host:
            return

        if self.current_main_screen:
            self.current_main_screen.destroy()
            self.current_main_screen = None

        role = AUTH_SERVICE.session.role
        user_id = AUTH_SERVICE.session.user_id

        if page_name == "Dashboard":
            screen = DashboardScreen(self.content_host, current_user_id=user_id)
        elif page_name == "Customers":
            screen = CustomersScreen(self.content_host, current_user_id=user_id, role=role)
        elif page_name == "Loans":
            screen = LoansScreen(self.content_host, current_user_id=user_id, role=role)
        elif page_name == "Repayments":
            screen = RepaymentsScreen(self.content_host, current_user_id=user_id, role=role)
        elif page_name == "Reports":
            screen = ReportsScreen(self.content_host)
        elif page_name == "Documents":
            screen = DocumentsScreen(self.content_host, current_user_id=user_id, role=role)
        elif page_name == "Settings":
            screen = SettingsScreen(self.content_host, current_user_id=user_id, role=role)
        else:
            fallback = tk.Frame(self.content_host, bg=PALETTE.window_bg)
            tk.Label(fallback, text=f"{page_name} is not available", bg=PALETTE.window_bg, fg=PALETTE.text_secondary).pack(padx=20, pady=20)
            screen = fallback

        screen.pack(fill="both", expand=True)
        self.current_main_screen = screen

        if self.topbar:
            self.topbar.set_page_title(page_name)
