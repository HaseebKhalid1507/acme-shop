"""Minimal HTTP API using stdlib http.server — no external deps."""
from __future__ import annotations
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from shop.catalog import Catalog
from shop.cart import Cart
from shop.checkout import Checkout

_catalog = Catalog.default()
_carts: dict[str, Cart] = {}   # session_id -> Cart


def _get_cart(session: str) -> Cart:
    if session not in _carts:
        _carts[session] = Cart(_catalog)
    return _carts[session]


class ShopHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # silence request logs in tests
        pass

    def _send_json(self, status: int, data: dict | list):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_GET(self):
        if self.path == "/products":
            self._send_json(200, [p.to_dict() for p in _catalog.all()])
        elif self.path.startswith("/products/sort?"):
            asc = "desc" not in self.path
            self._send_json(200, [p.to_dict() for p in _catalog.sorted_by_price(asc)])
        elif self.path.startswith("/cart/"):
            session = self.path.split("/")[2]
            self._send_json(200, _get_cart(session).total())
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        body = self._read_json()
        parts = self.path.strip("/").split("/")

        if parts[0] == "cart" and len(parts) >= 3 and parts[2] == "add":
            session = parts[1]
            cart = _get_cart(session)
            try:
                cart.add(body["product_id"], body.get("qty", 1))
                self._send_json(200, cart.total())
            except (ValueError, KeyError) as e:
                self._send_json(400, {"error": str(e)})

        elif parts[0] == "cart" and len(parts) >= 3 and parts[2] == "coupon":
            session = parts[1]
            _get_cart(session).apply_coupon(body.get("code", ""))
            self._send_json(200, {"ok": True})

        elif parts[0] == "cart" and len(parts) >= 3 and parts[2] == "checkout":
            session = parts[1]
            cart = _get_cart(session)
            co = Checkout(cart, _catalog)
            try:
                order = co.place_order(
                    payment_method=body.get("payment_method", "card"),
                    card_token=body.get("card_token"),
                )
                self._send_json(200, order.to_dict())
            except Exception as e:
                self._send_json(400, {"error": str(e)})
        else:
            self._send_json(404, {"error": "not found"})


def make_server(host: str = "127.0.0.1", port: int = 8080) -> HTTPServer:
    return HTTPServer((host, port), ShopHandler)


def serve(host: str = "127.0.0.1", port: int = 8080):  # pragma: no cover
    s = make_server(host, port)
    print(f"Acme Shop listening on http://{host}:{port}")
    s.serve_forever()
