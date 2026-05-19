"""
GUI Controller layer.
ユーザーイベントのハンドリングと変換ロジックの実行を担当。
ViewとModel間の橋渡し。
"""
import os
import threading
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox

from .cobol_parser import CobolParser
from .oop_transformer import OopTransformer, TransformOptions
from .java_generator import JavaCodeGenerator
from .i18n import I18n
from .vendor_extensions import detect_vendor, VENDOR_DISPLAY_NAMES
from .gui_model import ConversionConfig, ConversionState
from .gui_view import CobolToJavaView


class ConversionController:
    """Controller: イベントハンドリングと変換ロジック."""

    def __init__(self, view: CobolToJavaView, i18n: I18n):
        self.view = view
        self.i18n = i18n
        self.state = ConversionState()

        self._bind_events()
        self.view.apply_language()

    def _t(self, key: str, **kwargs) -> str:
        return self.i18n.t(key, **kwargs)

    def _bind_events(self):
        self.view.bind_browse_input(self._browse_input)
        self.view.bind_browse_output(self._browse_output)
        self.view.bind_run(self._start_conversion)
        self.view.bind_cancel(self._cancel_conversion)
        self.view.bind_clear_log(self.view.clear_log)
        self.view.bind_language_change(self._on_language_change)

    # ---- Event Handlers ----

    def _browse_input(self):
        folder = filedialog.askdirectory(title=self._t("browse_input_title"))
        if folder:
            self.view.input_var.set(folder)

    def _browse_output(self):
        folder = filedialog.askdirectory(title=self._t("browse_output_title"))
        if folder:
            self.view.output_var.set(folder)

    def _on_language_change(self, lang_code: str):
        self.i18n.lang = lang_code
        self.view.apply_language()

    def _start_conversion(self):
        config = self._build_config()
        if not self._validate_config(config):
            return

        self.state.reset()
        self.state.is_running = True
        self.view.set_running_state(True)
        self.view.progress_var.set(0)

        thread = threading.Thread(
            target=self._run_conversion, args=(config,), daemon=True
        )
        thread.start()

    def _cancel_conversion(self):
        self.state.cancel_flag = True
        self.view.log(self._t("log_cancel_request"), "warning")

    # ---- Config building ----

    def _build_config(self) -> ConversionConfig:
        return ConversionConfig(
            input_dir=self.view.input_var.get().strip(),
            output_dir=self.view.output_var.get().strip(),
            package_name=self.view.package_var.get().strip() or "com.migrated",
            encoding=self.view.encoding_var.get(),
            extensions=self.view.extensions_var.get(),
            vendor=self.view.get_selected_vendor_code(),
            generate_getters_setters=self.view.getter_setter_var.get(),
            use_big_decimal=self.view.big_decimal_var.get(),
            generate_javadoc=self.view.javadoc_var.get(),
            generate_toString=self.view.toString_var.get(),
            extract_data_classes=self.view.extract_classes_var.get(),
            extract_enums=self.view.extract_enums_var.get(),
            extract_services=self.view.extract_services_var.get(),
            extract_file_handlers=self.view.extract_file_handlers_var.get(),
        )

    def _validate_config(self, config: ConversionConfig) -> bool:
        t = self._t
        if not config.input_dir:
            messagebox.showwarning(t("warn_title"), t("warn_no_input"))
            return False
        if not config.output_dir:
            messagebox.showwarning(t("warn_title"), t("warn_no_output"))
            return False
        if not os.path.isdir(config.input_dir):
            messagebox.showerror(
                t("error_title"), t("error_no_input_dir", path=config.input_dir)
            )
            return False
        return True

    # ---- Conversion Logic ----

    def _run_conversion(self, config: ConversionConfig):
        t = self._t
        log = self.view.log
        try:
            log("=" * 60, "header")
            log(t("log_starting"), "header")
            log("=" * 60, "header")
            log(t("log_input", path=config.input_dir))
            log(t("log_output", path=config.output_dir))

            extensions = config.get_extension_list()
            cobol_files = self._find_cobol_files(config.input_dir, extensions)

            if not cobol_files:
                log(t("log_no_files", ext=str(extensions)), "warning")
                self._finish()
                return

            log(t("log_found_files", count=len(cobol_files)), "info")

            options = TransformOptions(
                package_name=config.package_name,
                generate_getters_setters=config.generate_getters_setters,
                use_big_decimal=config.use_big_decimal,
                generate_javadoc=config.generate_javadoc,
                generate_toString=config.generate_toString,
                extract_data_classes=config.extract_data_classes,
                extract_enums=config.extract_enums,
                extract_file_handlers=config.extract_file_handlers,
                group_related_paragraphs=config.extract_services,
                vendor_type=config.vendor,
            )

            parser = CobolParser(encoding=config.encoding)
            transformer = OopTransformer(options)
            generator = JavaCodeGenerator(options)

            for i, filepath in enumerate(cobol_files):
                if self.state.cancel_flag:
                    log(t("log_cancelled"), "warning")
                    break

                self._process_single_file(
                    filepath, config, parser, transformer, generator, i, len(cobol_files)
                )

            log(f"\n{'=' * 60}", "header")
            log(t("log_migration_complete"), "header")
            log(f"{'=' * 60}", "header")
            log(t("log_success", count=self.state.success_count), "success")
            if self.state.error_count > 0:
                log(t("log_errors", count=self.state.error_count), "error")
            log(t("log_output", path=config.output_dir), "info")

        except Exception as e:
            log(f"Fatal error: {str(e)}", "error")
            log(traceback.format_exc(), "error")

        finally:
            self._finish()

    def _process_single_file(
        self, filepath: str, config: ConversionConfig,
        parser: CobolParser, transformer: OopTransformer,
        generator: JavaCodeGenerator,
        index: int, total: int
    ):
        t = self._t
        log = self.view.log
        root = self.view.root

        rel_path = os.path.relpath(filepath, config.input_dir)
        filename = os.path.basename(filepath)
        display_name = rel_path if os.path.dirname(rel_path) else filename

        progress = ((index + 1) / total) * 100
        root.after(0, lambda p=progress: self.view.progress_var.set(p))
        root.after(0, lambda f=display_name: self.view.status_var.set(
            t("status_processing", file=f)
        ))

        log(f"\n{t('log_processing', file=display_name)}", "header")

        try:
            log(t("log_parsing"), "info")
            program = parser.parse_file(filepath)

            # Vendor detection / assignment
            if config.vendor == "auto":
                with open(filepath, "r", encoding=config.encoding, errors="replace") as vf:
                    src_lines = vf.readlines()
                detected = detect_vendor(src_lines)
                program.vendor_type = detected.value
                log(t("log_vendor_detected",
                       vendor=VENDOR_DISPLAY_NAMES.get(detected, detected.value)), "info")
            else:
                program.vendor_type = config.vendor
                log(t("log_vendor_set", vendor=config.vendor), "info")

            log(t("log_program_id", id=program.program_id or "(unknown)"))
            log(t("log_ws_items", count=len(program.working_storage)))
            log(t("log_paragraphs", count=len(program.paragraphs)))
            log(t("log_sections", count=len(program.sections)))
            log(t("log_files", count=len(program.files)))
            if program.has_exec_sql:
                log(t("log_exec_sql", count="detected"), "info")
            if program.has_exec_cics:
                log(t("log_exec_cics", count="detected"), "info")
            if program.has_exec_dli:
                log(t("log_exec_dli"), "info")
            if program.has_class_id:
                log(t("log_oo_cobol"), "info")
            if program.screen_section:
                log(t("log_screen_section", count=len(program.screen_section)), "info")

            log(t("log_transforming"), "info")
            project = transformer.transform(program)

            if project.main_class:
                log(t("log_main_class", name=project.main_class.name))
                log(t("log_fields", count=len(project.main_class.fields)))
                log(t("log_methods", count=len(project.main_class.methods)))
            log(t("log_data_classes", count=len(project.data_classes)))
            log(t("log_enum_classes", count=len(project.enum_classes)))
            log(t("log_service_classes", count=len(project.service_classes)))
            log(t("log_file_handlers", count=len(project.file_handler_classes)))

            log(t("log_generating"), "info")
            # Preserve subfolder structure in output
            rel_dir = os.path.relpath(os.path.dirname(filepath), config.input_dir)
            if rel_dir == ".":
                file_output_dir = config.output_dir
            else:
                file_output_dir = os.path.join(config.output_dir, rel_dir)
            generator.generate_project(project, file_output_dir)

            total_classes = (
                (1 if project.main_class else 0) +
                len(project.data_classes) +
                len(project.enum_classes) +
                len(project.service_classes) +
                len(project.file_handler_classes)
            )
            log(t("log_generated", count=total_classes), "success")
            self.state.success_count += 1

        except Exception as e:
            self.state.error_count += 1
            log(f"  ERROR: {str(e)}", "error")
            log(f"  {traceback.format_exc()}", "error")

    def _find_cobol_files(self, input_dir: str, extensions: list) -> list:
        cobol_files = []
        for root_dir, dirs, files in os.walk(input_dir):
            for f in files:
                if any(f.endswith(ext) for ext in extensions):
                    cobol_files.append(os.path.join(root_dir, f))
        return cobol_files

    def _finish(self):
        self.state.is_running = False
        self.view.root.after(0, lambda: self.view.set_running_state(False))
        self.view.root.after(0, lambda: self.view.status_var.set(self._t("status_complete")))
        self.view.root.after(0, lambda: self.view.progress_var.set(100))
