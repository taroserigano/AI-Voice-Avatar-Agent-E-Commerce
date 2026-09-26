"""Ten Larkspur stores around Dallas-Fort Worth, for the store locator and map.

These are demo locations: the street addresses are made up for this project (on real
streets, so the map pins land somewhere sensible) and the phone numbers use the 555-01xx
range reserved for fiction. Hours are local time (America/Chicago).
"""

from __future__ import annotations

from dataclasses import dataclass, field

DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _daily(open_: str, close: str, **overrides: tuple[str, str]) -> dict[str, list[str]]:
    hours = {d: [open_, close] for d in DAYS}
    hours.update({d: list(v) for d, v in overrides.items()})
    return hours


@dataclass(frozen=True)
class StoreSeed:
    code: str
    name: str
    address_line1: str
    city: str
    postal_code: str
    latitude: float
    longitude: float
    phone: str
    hours: dict[str, list[str]]
    services: tuple[str, ...] = field(default=("Grocery", "Return drop-off"))
    state: str = "TX"


_CORE = ("Grocery", "Fresh bakery", "Deli", "Return drop-off")

STORES: tuple[StoreSeed, ...] = (
    StoreSeed(
        "DAL-UPTOWN", "Larkspur Uptown", "2850 McKinney Ave", "Dallas", "75204",
        32.8003, -96.8009, "(214) 555-0101", _daily("06:00", "23:00"),
        (*_CORE, "Coffee bar", "Electronics"),
    ),
    StoreSeed(
        "DAL-LAKEWOOD", "Larkspur Lakewood", "6320 Gaston Ave", "Dallas", "75214",
        32.8131, -96.7536, "(214) 555-0102", _daily("07:00", "22:00"),
        (*_CORE, "Garden center"),
    ),
    StoreSeed(
        "DAL-BISHOP-ARTS", "Larkspur Bishop Arts", "410 W Davis St", "Dallas", "75208",
        32.7490, -96.8282, "(214) 555-0103", _daily("07:00", "21:00", sun=("08:00", "20:00")),
        _CORE,
    ),
    StoreSeed(
        "PLN-LEGACY", "Larkspur Plano Legacy", "5800 Legacy Dr", "Plano", "75024",
        33.0768, -96.8236, "(972) 555-0104", _daily("07:00", "22:00"),
        (*_CORE, "Electronics", "Home & kitchen", "EV charging"),
    ),
    StoreSeed(
        "FRI-MAIN", "Larkspur Frisco", "7100 Main St", "Frisco", "75034",
        33.1510, -96.8230, "(469) 555-0105", _daily("07:00", "22:00"),
        (*_CORE, "Electronics", "Garden center", "EV charging"),
    ),
    StoreSeed(
        "RCH-CAMPBELL", "Larkspur Richardson", "1300 E Campbell Rd", "Richardson", "75081",
        32.9760, -96.7045, "(972) 555-0106", _daily("07:00", "22:00"),
        _CORE,
    ),
    StoreSeed(
        "IRV-LAS-COLINAS", "Larkspur Las Colinas", "5200 N O'Connor Blvd", "Irving", "75039",
        32.8785, -96.9420, "(972) 555-0107", _daily("07:00", "22:00"),
        (*_CORE, "Coffee bar"),
    ),
    StoreSeed(
        "GAR-DOWNTOWN", "Larkspur Garland", "600 W Garland Ave", "Garland", "75040",
        32.9135, -96.6420, "(972) 555-0108", _daily("07:00", "21:00"),
        ("Grocery", "Deli", "Return drop-off"),
    ),
    StoreSeed(
        "ARL-ABRAM", "Larkspur Arlington", "700 W Abram St", "Arlington", "76013",
        32.7359, -97.1150, "(817) 555-0109", _daily("07:00", "22:00"),
        (*_CORE, "Sports & outdoor"),
    ),
    StoreSeed(
        "MCK-VIRGINIA", "Larkspur McKinney", "2200 W Virginia Pkwy", "McKinney", "75071",
        33.2074, -96.6620, "(469) 555-0110", _daily("07:00", "22:00", sun=("08:00", "21:00")),
        (*_CORE, "Garden center", "Home & kitchen"),
    ),
)  # fmt: skip
