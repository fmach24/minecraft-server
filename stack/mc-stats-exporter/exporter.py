import json
import os
import socket
import struct
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


def read_level_name(data_dir: Path) -> str:
    props_path = data_dir / "server.properties"
    if not props_path.exists():
        return "world"

    try:
        for line in props_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("level-name="):
                return line.split("=", 1)[1].strip() or "world"
    except OSError:
        pass

    return "world"


def read_user_cache(data_dir: Path) -> dict:
    cache_path = data_dir / "usercache.json"
    if not cache_path.exists():
        return {}

    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    mapping = {}
    for entry in cache:
        uuid = entry.get("uuid")
        name = entry.get("name")
        if uuid and name:
            mapping[uuid.lower()] = name
    return mapping


def read_deaths(stats_dir: Path) -> dict:
    deaths = {}
    if not stats_dir.exists():
        return deaths

    for stats_file in stats_dir.glob("*.json"):
        try:
            stats = json.loads(stats_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        uuid = stats_file.stem.lower()
        custom_stats = stats.get("stats", {}).get("minecraft:custom", {})
        death_count = custom_stats.get("minecraft:deaths", 0)
        deaths[uuid] = int(death_count)

    return deaths


def query_players(host: str, port: int, timeout: float) -> tuple[int, list[str]] | None:
    session_id = 0x12345678

    def pack_int(value: int) -> bytes:
        return struct.pack(">i", value)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)

    try:
        sock.sendto(b"\xFE\xFD\x09" + pack_int(session_id), (host, port))
        response, _ = sock.recvfrom(2048)

        if not response or response[0] != 0x09:
            return None

        token_raw = response[5:].split(b"\x00", 1)[0]
        token = int(token_raw.decode("ascii", errors="ignore"))

        payload = b"\xFE\xFD\x00" + pack_int(session_id) + pack_int(token) + b"\x00\x00\x00\x00"
        sock.sendto(payload, (host, port))
        response, _ = sock.recvfrom(8192)

        if not response or response[0] != 0x00:
            return None

        data = response[5:]
        if b"\x00\x00\x01" not in data:
            return None

        kv_raw, players_raw = data.split(b"\x00\x00\x01", 1)
        kv_parts = [p for p in kv_raw.split(b"\x00") if p]
        kv = {}
        for i in range(0, len(kv_parts) - 1, 2):
            key = kv_parts[i].decode("utf-8", errors="ignore")
            value = kv_parts[i + 1].decode("utf-8", errors="ignore")
            kv[key] = value

        players_section = players_raw.lstrip(b"\x00")
        prefix = b"player_\x00\x00"
        if players_section.startswith(prefix):
            players_section = players_section[len(prefix):]

        players = [
            p.decode("utf-8", errors="ignore")
            for p in players_section.split(b"\x00")
            if p
        ]

        num_players = int(kv.get("numplayers", "0"))
        return num_players, players
    except (OSError, ValueError):
        return None
    finally:
        sock.close()


def build_metrics(data_dir: Path) -> str:
    level_name = read_level_name(data_dir)
    stats_dir = data_dir / level_name / "stats"
    user_cache = read_user_cache(data_dir)
    deaths = read_deaths(stats_dir)

    query_host = os.environ.get("MC_QUERY_HOST", "minecraft")
    query_port = int(os.environ.get("MC_QUERY_PORT", "25565"))
    query_timeout = float(os.environ.get("QUERY_TIMEOUT", "1.0"))
    query_result = query_players(query_host, query_port, query_timeout)

    lines = []
    lines.append("# HELP minecraft_stats_exporter_up Exporter health.")
    lines.append("# TYPE minecraft_stats_exporter_up gauge")
    lines.append("minecraft_stats_exporter_up 1")

    lines.append("# HELP minecraft_query_up Query protocol reachable.")
    lines.append("# TYPE minecraft_query_up gauge")
    lines.append(f"minecraft_query_up {1 if query_result else 0}")

    if query_result:
        online_count, online_players = query_result
        lines.append("# HELP minecraft_players_online Current online player count.")
        lines.append("# TYPE minecraft_players_online gauge")
        lines.append(f"minecraft_players_online {online_count}")

        lines.append("# HELP minecraft_player_online Online player flag (1 for online players).")
        lines.append("# TYPE minecraft_player_online gauge")
        for name in sorted(online_players):
            name_sanitized = name.replace("\\", "\\\\").replace("\"", "\\\"")
            lines.append(
                f"minecraft_player_online{{player=\"{name_sanitized}\"}} 1"
            )

    lines.append("# HELP minecraft_players_total Count of players with stats files.")
    lines.append("# TYPE minecraft_players_total gauge")
    lines.append(f"minecraft_players_total {len(deaths)}")

    lines.append("# HELP minecraft_player_deaths Player deaths based on stats JSON.")
    lines.append("# TYPE minecraft_player_deaths gauge")
    for uuid, count in sorted(deaths.items()):
        name = user_cache.get(uuid, "unknown")
        name_sanitized = name.replace("\\", "\\\\").replace("\"", "\\\"")
        lines.append(
            f"minecraft_player_deaths{{player=\"{name_sanitized}\",uuid=\"{uuid}\"}} {count}"
        )

    return "\n".join(lines) + "\n"


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return

        data_dir = Path(os.environ.get("DATA_DIR", "/data"))
        body = build_metrics(data_dir).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return


def main():
    port = int(os.environ.get("PORT", "9225"))
    server = HTTPServer(("0.0.0.0", port), MetricsHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()


    #tescik - powinno zrestartowac dockery
