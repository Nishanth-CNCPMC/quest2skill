import socket
import threading
from typing import Callable, Optional


LineCallback = Callable[[str], None]
ErrorCallback = Callable[[Exception], None]
StatusCallback = Callable[[str], None]


class LineTcpServer:
    """Small reconnecting TCP server for newline-delimited text messages."""

    def __init__(
        self,
        host: str,
        port: int,
        on_line: LineCallback,
        on_status: Optional[StatusCallback] = None,
        on_error: Optional[ErrorCallback] = None,
        recv_size: int = 4096,
    ) -> None:
        self._host = host
        self._port = port
        self._on_line = on_line
        self._on_status = on_status
        self._on_error = on_error
        self._recv_size = recv_size
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._server: Optional[socket.socket] = None
        self._conn: Optional[socket.socket] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._close_socket(self._conn)
        self._close_socket(self._server)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _serve(self) -> None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                self._server = server
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind((self._host, self._port))
                server.listen(1)
                server.settimeout(0.5)
                self._emit_status(f"listening on {self._host}:{self._port}")

                while not self._stop_event.is_set():
                    try:
                        conn, addr = server.accept()
                    except socket.timeout:
                        continue

                    self._emit_status(f"client connected from {addr[0]}:{addr[1]}")
                    with conn:
                        self._conn = conn
                        self._handle_connection(conn)
                    self._conn = None
                    self._emit_status("client disconnected")
        except OSError as exc:
            if not self._stop_event.is_set():
                self._emit_error(exc)
        finally:
            self._server = None

    def _handle_connection(self, conn: socket.socket) -> None:
        buffer = ""
        conn.settimeout(0.5)

        while not self._stop_event.is_set():
            try:
                data = conn.recv(self._recv_size)
            except socket.timeout:
                continue
            except OSError as exc:
                self._emit_error(exc)
                return

            if not data:
                return

            buffer += data.decode("utf-8", errors="ignore")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line:
                    self._on_line(line)

    def _emit_status(self, message: str) -> None:
        if self._on_status:
            self._on_status(message)

    def _emit_error(self, exc: Exception) -> None:
        if self._on_error:
            self._on_error(exc)

    @staticmethod
    def _close_socket(sock: Optional[socket.socket]) -> None:
        if sock is None:
            return
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            sock.close()
        except OSError:
            pass
