"""Which tools each assistant may use. Neither has a tool that confirms, pays, or refunds.

Xena reads everything the store has about products (details, ratings, reviews) and about the
signed-in customer (orders, returns, cart, support cases, account activity), read-only except
pricing and proposing a return and opening a support case. She can't add to the cart.
"""

from __future__ import annotations

from langchain_core.tools import BaseTool

from assistant.account_tools import get_my_account_activity, get_my_cart, list_my_support_cases
from assistant.return_tools import (
    get_refund_status,
    get_return_options,
    propose_return,
    quote_return,
)
from assistant.tools import (
    STEPH_TOOLS,
    get_order_status,
    get_product_details,
    get_product_reviews,
    handoff_to_person,
    list_my_orders,
    list_stores,
    search_policies,
    search_products,
)

XANA_TOOLS: list[BaseTool] = [
    search_products,
    list_my_orders,
    get_order_status,
    get_return_options,
    quote_return,
    propose_return,
    get_refund_status,
    search_policies,
    list_stores,
    get_product_details,
    get_product_reviews,
    get_my_cart,
    list_my_support_cases,
    get_my_account_activity,
    handoff_to_person,
]

ALL_TOOLS: list[BaseTool] = list({t.name: t for t in [*STEPH_TOOLS, *XANA_TOOLS]}.values())


def tools_for(agent: str) -> list[BaseTool]:
    return XANA_TOOLS if agent == "xana" else STEPH_TOOLS
