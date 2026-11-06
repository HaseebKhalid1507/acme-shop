"""Simple CLI for the Acme Shop."""
from __future__ import annotations
import argparse
import json
import sys
from shop.catalog import Catalog
from shop.cart import Cart
from shop.checkout import Checkout

catalog = Catalog.default()
cart = Cart(catalog)
checkout_session = None


def cmd_list(args):
    for p in catalog.all():
        print(f"  {p.id}  {p.name:<28}  ${p.price:.2f}  stock={p.stock}")


def cmd_add(args):
    cart.add(args.product_id, args.qty)
    t = cart.total()
    print(f"Added. Cart total: ${t['total']:.2f}")


def cmd_coupon(args):
    cart.apply_coupon(args.code)
    print(f"Coupon {args.code!r} applied.")


def cmd_total(args):
    t = cart.total()
    print(json.dumps(t, indent=2))


def cmd_checkout(args):
    co = Checkout(cart, catalog)
    try:
        order = co.place_order(card_token=args.card_token)
        print(f"Order placed: {order.order_id}  total=${order.total:.2f}")
    except Exception as e:
        print(f"Checkout failed: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    p = argparse.ArgumentParser(prog="acme-shop")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list").set_defaults(func=cmd_list)

    p_add = sub.add_parser("add")
    p_add.add_argument("product_id")
    p_add.add_argument("qty", type=int, nargs="?", default=1)
    p_add.set_defaults(func=cmd_add)

    p_cpn = sub.add_parser("coupon")
    p_cpn.add_argument("code")
    p_cpn.set_defaults(func=cmd_coupon)

    sub.add_parser("total").set_defaults(func=cmd_total)

    p_co = sub.add_parser("checkout")
    p_co.add_argument("--card-token", default=None)
    p_co.set_defaults(func=cmd_checkout)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
