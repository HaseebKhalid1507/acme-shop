# Acme Shop 🛒

A small, stdlib-only Python shop used as the **product repo** for the
[synaps-switch](https://github.com/adityapat958/synaps-switch) hackathon — a
simulation of an AI-run company where LangGraph agents act as board, finance,
marketing, and engineering departments.

The *market* (customers, demand, churn) is simulated. Engineering work is real:
bugs are filed as GitHub issues, an AI coding agent opens PRs to fix them, and
the board approves merges.

## Package layout

```
shop/
  catalog.py    — product catalog (load, search, sort)
  cart.py       — line items, coupons, totals
  pricing.py    — tax, coupon codes, discount logic
  checkout.py   — inventory reservation, payment stub, order records
  api.py        — stdlib http.server HTTP API (no external deps)
  cli.py        — simple CLI (list / add / coupon / total / checkout)
tests/
  test_catalog.py
  test_cart.py
  test_checkout.py
  test_pricing.py
```

## Running the shop

```bash
# list products
python -m shop.cli list

# add to cart, apply coupon, check out
python -m shop.cli add SKU-001 2
python -m shop.cli coupon SAVE10
python -m shop.cli total
python -m shop.cli checkout --card-token tok_test

# start the HTTP server (default port 8080)
python -m shop.api
```

## Running tests

```bash
pip install pytest          # only test dep
python -m pytest tests/ -q
```

## Open incidents & features

Bugs are labelled `incident` (sev1/sev2/sev3). Features are labelled `feature`.
See the [Issues tab](../../issues).

## Hackathon context

This repo is part of the **synaps-switch** hackathon. AI agents (LangGraph +
Synaps) run the company: they triage incidents, approve engineering PRs, run
marketing campaigns, and evolve their own org structure via a fitness function.
