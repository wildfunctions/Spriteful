"""PySide6 GUI for TextureFall texture packer."""

import os
from enum import Enum
from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt, QMimeData, Signal, QTimer
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QLabel, QComboBox, QSpinBox, QFileDialog,
    QMessageBox, QSplitter, QScrollArea, QFrame, QAbstractItemView,
    QSlider, QGroupBox,
)

from packer import MaxRectsPacker, PackedImage
from exporter import export_atlas

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tga", ".webp"}

ATLAS_SIZES = [256, 512, 1024, 2048, 4096, 8192]


class DropZoneList(QListWidget):
    """A list widget that accepts file drops."""

    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            paths = []
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path:
                    paths.extend(self._collect_images(path))
            if paths:
                self.files_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def _collect_images(self, path: str) -> list[str]:
        """Collect image files from a path (file or directory)."""
        result = []
        p = Path(path)
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
            result.append(str(p))
        elif p.is_dir():
            for f in sorted(p.iterdir()):
                if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                    result.append(str(f))
        return result


class PreviewWidget(QLabel):
    """Widget that displays the packed atlas preview."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(200, 200)
        self.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555;")
        self.setText("Atlas Preview\n\nAdd images to begin")
        self.setStyleSheet(
            "background-color: #2b2b2b; border: 1px solid #555; "
            "color: #888; font-size: 14px;"
        )
        self._pixmap = None

    def set_preview(self, pixmap: QPixmap | None):
        if pixmap is None:
            self._pixmap = None
            self.setText("Atlas Preview\n\nAdd images to begin")
            return

        self._pixmap = pixmap
        self._update_scaled()

    def _update_scaled(self):
        if self._pixmap is None:
            return
        scaled = self._pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scaled()


class PlaybackMode(Enum):
    FORWARD = "Forward"
    REVERSE = "Reverse"
    PING_PONG = "Ping-Pong"


class AnimationPlayer(QGroupBox):
    """Animation preview player for selected sprites."""

    def __init__(self, parent=None):
        super().__init__("Animation Player", parent)
        self._frames: list[str] = []  # file paths of selected frames
        self._current_index = 0
        self._ping_pong_direction = 1  # 1 = forward, -1 = backward
        self._playing = False
        self._mode = PlaybackMode.FORWARD

        self._timer = QTimer()
        self._timer.timeout.connect(self._advance_frame)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Frame display
        self.frame_display = QLabel()
        self.frame_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.frame_display.setMinimumSize(150, 150)
        self.frame_display.setMaximumHeight(250)
        self.frame_display.setStyleSheet(
            "background-color: #2b2b2b; border: 1px solid #555; color: #888;"
        )
        self.frame_display.setText("Select images to preview")
        layout.addWidget(self.frame_display)

        # Frame counter
        self.lbl_frame = QLabel("Frame: - / -")
        self.lbl_frame.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_frame)

        # Transport controls
        transport = QHBoxLayout()

        self.btn_play = QPushButton("Play")
        self.btn_play.setCheckable(True)
        self.btn_play.setMinimumWidth(60)
        self.btn_play.clicked.connect(self._on_play_toggle)
        transport.addWidget(self.btn_play)

        self.btn_step_back = QPushButton("|<")
        self.btn_step_back.setMaximumWidth(35)
        self.btn_step_back.clicked.connect(self._step_backward)
        transport.addWidget(self.btn_step_back)

        self.btn_step_fwd = QPushButton(">|")
        self.btn_step_fwd.setMaximumWidth(35)
        self.btn_step_fwd.clicked.connect(self._step_forward)
        transport.addWidget(self.btn_step_fwd)

        transport.addSpacing(10)

        transport.addWidget(QLabel("Mode:"))
        self.combo_mode = QComboBox()
        for mode in PlaybackMode:
            self.combo_mode.addItem(mode.value, mode)
        self.combo_mode.currentIndexChanged.connect(self._on_mode_changed)
        transport.addWidget(self.combo_mode)

        layout.addLayout(transport)

        # Speed slider
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))

        self.slider_fps = QSlider(Qt.Orientation.Horizontal)
        self.slider_fps.setRange(1, 60)
        self.slider_fps.setValue(12)
        self.slider_fps.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_fps.setTickInterval(5)
        self.slider_fps.valueChanged.connect(self._on_speed_changed)
        speed_layout.addWidget(self.slider_fps)

        self.lbl_fps = QLabel("12 FPS")
        self.lbl_fps.setMinimumWidth(50)
        speed_layout.addWidget(self.lbl_fps)

        layout.addLayout(speed_layout)

    def set_frames(self, file_paths: list[str]):
        """Set the animation frames from selected image file paths."""
        self._stop()
        self._frames = file_paths
        self._current_index = 0
        self._ping_pong_direction = 1

        if self._frames:
            self._show_frame(0)
            self.lbl_frame.setText(f"Frame: 1 / {len(self._frames)}")
        else:
            self.frame_display.setPixmap(QPixmap())
            self.frame_display.setText("Select images to preview")
            self.lbl_frame.setText("Frame: - / -")

    def _show_frame(self, index: int):
        """Display a single frame."""
        if not self._frames or index < 0 or index >= len(self._frames):
            return

        try:
            pil_img = Image.open(self._frames[index]).convert("RGBA")
            data = pil_img.tobytes("raw", "RGBA")
            qimg = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)
            qimg._data = data  # prevent GC
            pixmap = QPixmap.fromImage(qimg)

            scaled = pixmap.scaled(
                self.frame_display.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.frame_display.setPixmap(scaled)
        except Exception:
            self.frame_display.setText("(error loading frame)")

        self.lbl_frame.setText(f"Frame: {index + 1} / {len(self._frames)}")

    def _advance_frame(self):
        """Move to the next frame based on playback mode."""
        if not self._frames:
            return

        n = len(self._frames)

        if self._mode == PlaybackMode.FORWARD:
            self._current_index = (self._current_index + 1) % n

        elif self._mode == PlaybackMode.REVERSE:
            self._current_index = (self._current_index - 1) % n

        elif self._mode == PlaybackMode.PING_PONG:
            if n == 1:
                self._current_index = 0
            else:
                next_idx = self._current_index + self._ping_pong_direction
                if next_idx >= n:
                    self._ping_pong_direction = -1
                    next_idx = self._current_index + self._ping_pong_direction
                elif next_idx < 0:
                    self._ping_pong_direction = 1
                    next_idx = self._current_index + self._ping_pong_direction
                self._current_index = next_idx

        self._show_frame(self._current_index)

    def _on_play_toggle(self, checked: bool):
        if checked:
            self._play()
        else:
            self._stop()

    def _play(self):
        if not self._frames:
            self.btn_play.setChecked(False)
            return
        self._playing = True
        self.btn_play.setText("Stop")
        fps = self.slider_fps.value()
        self._timer.start(1000 // fps)

    def _stop(self):
        self._playing = False
        self._timer.stop()
        self.btn_play.setText("Play")
        self.btn_play.setChecked(False)

    def _step_forward(self):
        if not self._frames:
            return
        self._stop()
        self._current_index = (self._current_index + 1) % len(self._frames)
        self._show_frame(self._current_index)

    def _step_backward(self):
        if not self._frames:
            return
        self._stop()
        self._current_index = (self._current_index - 1) % len(self._frames)
        self._show_frame(self._current_index)

    def _on_mode_changed(self, index: int):
        self._mode = self.combo_mode.currentData()
        self._ping_pong_direction = 1
        if self._mode == PlaybackMode.REVERSE and self._frames:
            self._current_index = len(self._frames) - 1
            self._show_frame(self._current_index)

    def _on_speed_changed(self, value: int):
        self.lbl_fps.setText(f"{value} FPS")
        if self._playing:
            self._timer.setInterval(1000 // value)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spriteful — Texture Packer")
        self.setMinimumSize(1000, 600)
        self.resize(1300, 750)

        self.image_entries: list[tuple[str, str, int, int]] = []  # (path, name, w, h)
        self.last_packed: list[PackedImage] = []
        self.last_atlas_size: tuple[int, int] = (0, 0)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # --- Toolbar ---
        toolbar = QHBoxLayout()
        self.btn_add = QPushButton("Add Files...")
        self.btn_add_folder = QPushButton("Add Folder...")
        self.btn_remove = QPushButton("Remove Selected")
        self.btn_clear = QPushButton("Clear All")
        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_add_folder)
        toolbar.addWidget(self.btn_remove)
        toolbar.addWidget(self.btn_clear)
        toolbar.addStretch()
        main_layout.addLayout(toolbar)

        # --- Splitter: file list | preview ---
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: file list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        list_label = QLabel("Images (drag & drop files here):")
        list_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(list_label)

        self.file_list = DropZoneList()
        self.file_list.setMinimumWidth(250)
        left_layout.addWidget(self.file_list)

        self.lbl_count = QLabel("0 images")
        left_layout.addWidget(self.lbl_count)

        splitter.addWidget(left_panel)

        # Right: preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        preview_label = QLabel("Atlas Preview:")
        preview_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(preview_label)

        self.preview = PreviewWidget()
        right_layout.addWidget(self.preview, 1)

        self.lbl_atlas_info = QLabel("")
        right_layout.addWidget(self.lbl_atlas_info)

        splitter.addWidget(right_panel)

        # Animation player panel (right of preview area)
        self.anim_player = AnimationPlayer()
        self.anim_player.setMinimumWidth(220)
        self.anim_player.setMaximumWidth(320)
        splitter.addWidget(self.anim_player)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 1)

        main_layout.addWidget(splitter, 1)

        # --- Bottom controls ---
        bottom = QHBoxLayout()

        bottom.addWidget(QLabel("Max Size:"))
        self.combo_size = QComboBox()
        for size in ATLAS_SIZES:
            self.combo_size.addItem(f"{size}x{size}", size)
        self.combo_size.setCurrentIndex(3)  # default 2048
        bottom.addWidget(self.combo_size)

        bottom.addSpacing(20)

        bottom.addWidget(QLabel("Padding:"))
        self.spin_padding = QSpinBox()
        self.spin_padding.setRange(0, 32)
        self.spin_padding.setValue(2)
        bottom.addWidget(self.spin_padding)

        bottom.addStretch()

        self.btn_export = QPushButton("Export PNG + JSON")
        self.btn_export.setMinimumWidth(160)
        self.btn_export.setStyleSheet(
            "QPushButton { background-color: #4a9eff; color: white; font-weight: bold; "
            "padding: 8px 16px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #3a8eef; }"
            "QPushButton:disabled { background-color: #666; }"
        )
        self.btn_export.setEnabled(False)
        bottom.addWidget(self.btn_export)

        main_layout.addLayout(bottom)

    def _connect_signals(self):
        self.btn_add.clicked.connect(self._on_add_files)
        self.btn_add_folder.clicked.connect(self._on_add_folder)
        self.btn_remove.clicked.connect(self._on_remove_selected)
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_export.clicked.connect(self._on_export)
        self.file_list.files_dropped.connect(self._add_image_paths)
        self.combo_size.currentIndexChanged.connect(self._repack)
        self.spin_padding.valueChanged.connect(self._repack)
        self.file_list.itemSelectionChanged.connect(self._on_selection_changed)

    def _on_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tga *.webp);;All Files (*)",
        )
        if files:
            self._add_image_paths(files)

    def _on_add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            paths = []
            for f in sorted(Path(folder).iterdir()):
                if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                    paths.append(str(f))
            if paths:
                self._add_image_paths(paths)
            else:
                QMessageBox.information(self, "No Images", "No supported image files found in that folder.")

    def _add_image_paths(self, paths: list[str]):
        existing = {entry[0] for entry in self.image_entries}

        added = 0
        for path in paths:
            if path in existing:
                continue
            try:
                img = Image.open(path)
                w, h = img.size
                img.close()
            except Exception:
                continue

            name = Path(path).name
            self.image_entries.append((path, name, w, h))
            self.file_list.addItem(f"{name}  ({w}x{h})")
            existing.add(path)
            added += 1

        if added > 0:
            self._update_count()
            self._repack()

    def _on_remove_selected(self):
        indices = sorted([idx.row() for idx in self.file_list.selectedIndexes()], reverse=True)
        for i in indices:
            self.file_list.takeItem(i)
            self.image_entries.pop(i)
        self._update_count()
        self._repack()

    def _on_clear(self):
        self.file_list.clear()
        self.image_entries.clear()
        self._update_count()
        self.preview.set_preview(None)
        self.btn_export.setEnabled(False)
        self.lbl_atlas_info.setText("")
        self.last_packed = []
        self.last_atlas_size = (0, 0)

    def _update_count(self):
        n = len(self.image_entries)
        self.lbl_count.setText(f"{n} image{'s' if n != 1 else ''}")

    def _on_selection_changed(self):
        """Update animation player with currently selected images."""
        indices = sorted(idx.row() for idx in self.file_list.selectedIndexes())
        if indices:
            paths = [self.image_entries[i][0] for i in indices]
            self.anim_player.set_frames(paths)
        else:
            self.anim_player.set_frames([])

    def _repack(self):
        if not self.image_entries:
            self.preview.set_preview(None)
            self.btn_export.setEnabled(False)
            self.lbl_atlas_info.setText("")
            return

        max_size = self.combo_size.currentData()
        padding = self.spin_padding.value()

        packer = MaxRectsPacker(max_size, max_size, padding)
        packed, atlas_w, atlas_h = packer.pack(self.image_entries)

        self.last_packed = packed
        self.last_atlas_size = (atlas_w, atlas_h)

        failed_count = len(self.image_entries) - len(packed)

        if not packed:
            self.preview.set_preview(None)
            self.btn_export.setEnabled(False)
            self.lbl_atlas_info.setText("No images could fit in the atlas. Try a larger size.")
            return

        self.btn_export.setEnabled(True)

        # Render preview
        preview_img = self._render_preview(packed, atlas_w, atlas_h)
        self.preview.set_preview(preview_img)

        info = f"Atlas: {atlas_w}x{atlas_h}  |  {len(packed)} packed"
        if failed_count > 0:
            info += f"  |  {failed_count} didn't fit!"
        self.lbl_atlas_info.setText(info)

    def _render_preview(self, packed: list[PackedImage], atlas_w: int, atlas_h: int) -> QPixmap:
        """Render a preview of the packed atlas with checkerboard background."""
        # Create checkerboard background
        img = QImage(atlas_w, atlas_h, QImage.Format.Format_ARGB32)
        img.fill(QColor(40, 40, 40))

        painter = QPainter(img)

        # Draw checkerboard
        check_size = 16
        light = QColor(50, 50, 50)
        dark = QColor(40, 40, 40)
        for cy in range(0, atlas_h, check_size):
            for cx in range(0, atlas_w, check_size):
                color = light if (cx // check_size + cy // check_size) % 2 == 0 else dark
                painter.fillRect(cx, cy, check_size, check_size, color)

        # Draw each packed sprite
        for p in packed:
            try:
                pil_img = Image.open(p.filepath).convert("RGBA")

                # Handle rotation
                if pil_img.width != p.width or pil_img.height != p.height:
                    pil_img = pil_img.rotate(90, expand=True)

                data = pil_img.tobytes("raw", "RGBA")
                qimg = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)
                # Need to keep reference to data alive
                qimg._data = data
                painter.drawImage(p.x, p.y, qimg)
            except Exception:
                # If we can't load the image, draw a placeholder
                painter.fillRect(p.x, p.y, p.width, p.height, QColor(255, 0, 100, 128))

        # Draw borders around sprites
        pen = QPen(QColor(100, 200, 255, 80))
        pen.setWidth(1)
        painter.setPen(pen)
        for p in packed:
            painter.drawRect(p.x, p.y, p.width - 1, p.height - 1)

        painter.end()
        return QPixmap.fromImage(img)

    def _on_export(self):
        if not self.last_packed:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Atlas",
            "atlas",
            "PNG Files (*.png);;All Files (*)",
        )
        if not path:
            return

        # Strip extension — exporter adds .png and .json
        base = path
        if base.lower().endswith(".png"):
            base = base[:-4]

        try:
            png_path, json_path = export_atlas(
                self.last_packed,
                self.last_atlas_size[0],
                self.last_atlas_size[1],
                base,
            )
            QMessageBox.information(
                self,
                "Export Complete",
                f"Atlas exported successfully!\n\n"
                f"PNG: {png_path}\n"
                f"JSON: {json_path}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Error exporting atlas:\n{e}")
