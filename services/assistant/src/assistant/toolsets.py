"""Which tools each assistant may use. Neither has a tool that confirms, pays, or refunds."""

from __future__ import annotations

from langchain_core.tools import BaseTool

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
    handoff_to_person,
    list_my_orders,
    list_stores,
    search_policies,
)

XANA_TOOLS: list[BaseTool] = [
    list_my_orders,
    get_order_status,
    get_return_options,
    quote_return,
    propose_return,
    get_refund_status,
    search_policies,
    list_stores,
    get_product_details,
    handoff_to_person,
]

ALL_TOOLS: list[BaseTool] = list({t.name: t for t in [*STEPH_TOOLS, *XANA_TOOLS]}.values())


def tools_for(agent: str) -> list[BaseTool]:
    return XANA_TOOLS if agent == "xana" else STEPH_TOOLS
