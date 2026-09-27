"""Electronics: audio, TVs and streaming, chargers and cables, power banks, smart home, computer
accessories, tablets and e-readers, printers and ink, and phone cases.

Every brand and model is invented, and connectors are named generically (USB-C, 3.5 mm,
HDMI). Electronics returns need inspection, so specs are precise enough to check a claim.
"""

from __future__ import annotations

from collections.abc import Iterable

from commerce.seed.data import ProductSeed
from commerce.seed.gen.common import Size, cents, item, options, slugify

CAT = "electronics"
SONORA = "Sonora Audio"  # mid to premium audio
CRESTONE = "Crestone Audio"  # value audio
LUMEN = "Lumen Labs"  # speakers, tablets, e-readers, power
NOVAVIEW = "Novaview"  # TVs, monitors, streaming, soundbars
VOLTWAVE = "Voltwave"  # chargers, cables, power banks, phone cases
KEYLOFT = "Keyloft"  # keyboards, mice, hubs, storage
BRIGHTGATE = "Brightgate"  # smart home
PRESSMARK = "Pressmark"  # printers and ink

BT = ["wireless", "bluetooth", "rechargeable"]


def one(dollars: float, label: str = "Each", code: str = "EA") -> list[Size]:
    return [Size(code, label, cents(dollars))]


def sz(*rows: tuple[str, str, float]) -> list[Size]:
    return [Size(code, label, cents(price)) for code, label, price in rows]


def P(
    brand: str,
    product_type: str,
    title: str,
    description: str,
    sizes: list[Size],
    tags: Iterable[str] = (),
    specs: dict[str, str] | None = None,
) -> ProductSeed:
    return item(
        category=CAT, product_type=product_type, brand=brand, title=title,
        description=description, sizes=sizes, tags=tags, specs=specs,
    )  # fmt: skip


def colors(
    brand: str,
    product_type: str,
    title: str,
    description: str,
    names: list[str],
    dollars: float,
    tags: Iterable[str] = (),
    specs: dict[str, str] | None = None,
    attribute: str = "color",
) -> ProductSeed:
    """Same-price color (or other) options."""
    slug = slugify(brand, title)
    return item(
        category=CAT, product_type=product_type, brand=brand, title=title,
        description=description, variants_=options(CAT, slug, names, cents(dollars), attribute),
        tags=tags, specs=specs, slug=slug,
    )  # fmt: skip


# fmt: off
def audio() -> list[ProductSeed]:
    return [
        # Earbuds
        P(CRESTONE, "earbuds", "Wired Earbuds with Microphone, 3.5 mm",
          "Lightweight wired in-ear earbuds with an in-line microphone and play/pause button, 3.5 mm plug, and three ear tip sizes.",
          one(14.99), [], {"Connection": "Wired, 3.5 mm", "Microphone": "Yes", "Noise cancelling": "No", "Cable length": "4 ft"}),
        P(CRESTONE, "earbuds", "USB-C Wired Earbuds with Microphone",
          "Wired earbuds with a USB-C plug for phones and tablets without a headphone jack, with in-line volume controls and mic.",
          one(19.99), ["usb-c"], {"Connection": "Wired, USB-C", "Microphone": "Yes", "Noise cancelling": "No", "Cable length": "4 ft"}),
        colors(CRESTONE, "earbuds", "True Wireless Earbuds with Charging Case",
               "Bluetooth true wireless earbuds with 6 hours of playback per charge and 24 hours total with the case. Touch controls and USB-C charging.",
               ["Black", "White"], 29.99, [*BT, "usb-c"],
               {"Connection": "Bluetooth 5.3", "Battery life": "6 hours (24 with case)", "Noise cancelling": "No", "Water resistance": "IPX4 (splash resistant)", "Charging": "USB-C"}),
        P(CRESTONE, "earbuds", "Sport Wireless Earbuds with Ear Hooks",
          "Secure-fit wireless earbuds with flexible ear hooks for running and the gym. IPX5 sweat and water resistant; 9 hours per charge.",
          one(39.99), [*BT, "water-resistant", "usb-c"],
          {"Connection": "Bluetooth 5.3", "Battery life": "9 hours (36 with case)", "Noise cancelling": "No", "Water resistance": "IPX5", "Fit": "Ear hooks"}),
        P(CRESTONE, "earbuds", "Noise Cancelling Wireless Earbuds",
          "Wireless earbuds with active noise cancelling and a transparency mode. 7 hours with ANC on, 28 hours with the case; wireless charging case.",
          one(59.99), [*BT, "noise-cancelling", "water-resistant", "usb-c"],
          {"Connection": "Bluetooth 5.3", "Battery life": "7 hours ANC on (28 with case)", "Noise cancelling": "Active (ANC)", "Water resistance": "IPX4", "Charging": "USB-C or wireless"}),
        colors(SONORA, "earbuds", "Pulse Pro Noise Cancelling Wireless Earbuds",
               "Premium wireless earbuds with adaptive active noise cancelling, spatial audio, multipoint pairing, and a wireless charging case. IPX4.",
               ["Graphite", "Frost"], 149.99, [*BT, "noise-cancelling", "water-resistant", "usb-c"],
               {"Connection": "Bluetooth 5.4, multipoint", "Battery life": "8 hours ANC on (30 with case)", "Noise cancelling": "Adaptive active (ANC)", "Water resistance": "IPX4", "Charging": "USB-C or wireless"}),
        P(SONORA, "earbuds", "Pulse Sport Waterproof Wireless Earbuds",
          "Waterproof IPX7 sport earbuds with wing tips that stay put, a rinseable design, and 10 hours per charge.",
          one(99.99), [*BT, "waterproof", "usb-c"],
          {"Connection": "Bluetooth 5.3", "Battery life": "10 hours (30 with case)", "Noise cancelling": "No", "Water resistance": "IPX7 (waterproof)", "Fit": "Wing tips"}),
        P(SONORA, "earbuds", "Kids' Volume-Limited Wireless Earbuds",
          "Wireless earbuds sized for kids ages 6 and up with volume limited to 85 dB and small ear tips.",
          one(39.99), [*BT, "kids", "usb-c"],
          {"Connection": "Bluetooth 5.2", "Volume limit": "85 dB", "Battery life": "5 hours (20 with case)", "Ages": "6+"}),
        # Headphones
        P(CRESTONE, "headphones", "Wireless On-Ear Headphones",
          "Foldable Bluetooth on-ear headphones with 30-hour battery, built-in mic, and a 3.5 mm cable for wired listening.",
          one(34.99), [*BT, "usb-c"],
          {"Type": "On-ear", "Connection": "Bluetooth 5.3 or 3.5 mm cable", "Battery life": "30 hours", "Noise cancelling": "No"}),
        colors(CRESTONE, "headphones", "Noise Cancelling Wireless Over-Ear Headphones",
               "Over-ear Bluetooth headphones with active noise cancelling, 40-hour battery with ANC on, and soft protein-leather cushions. Folds into a travel case.",
               ["Black", "Navy"], 79.99, [*BT, "noise-cancelling", "usb-c"],
               {"Type": "Over-ear", "Connection": "Bluetooth 5.3", "Battery life": "40 hours ANC on", "Noise cancelling": "Active (ANC)", "Charging": "USB-C"}),
        P(CRESTONE, "headphones", "Kids' Wireless Headphones, Volume-Limited",
          "Colorful wireless headphones for kids ages 3 and up with an 85 dB volume limit, padded headband, and 25-hour battery.",
          one(29.99), [*BT, "kids", "usb-c"],
          {"Type": "On-ear", "Connection": "Bluetooth 5.0", "Volume limit": "85 dB", "Battery life": "25 hours", "Ages": "3+"}),
        P(SONORA, "headphones", "Arc Lite Noise Cancelling Wireless Headphones",
          "Lightweight over-ear headphones with hybrid active noise cancelling, 50-hour battery, and fast charging (10 minutes for 5 hours).",
          one(89.99), [*BT, "noise-cancelling", "usb-c"],
          {"Type": "Over-ear", "Connection": "Bluetooth 5.3, multipoint", "Battery life": "50 hours ANC on", "Noise cancelling": "Hybrid active (ANC)", "Charging": "USB-C"}),
        colors(SONORA, "headphones", "Arc Pro Noise Cancelling Wireless Over-Ear Headphones",
               "Flagship over-ear headphones with adaptive noise cancelling, eight microphones for clear calls, high-resolution audio, and a 30-hour battery.",
               ["Midnight", "Silver"], 299.99, [*BT, "noise-cancelling", "usb-c"],
               {"Type": "Over-ear", "Connection": "Bluetooth 5.4, multipoint; USB-C audio", "Battery life": "30 hours ANC on", "Noise cancelling": "Adaptive active (ANC)", "Charging": "USB-C"}),
        P(SONORA, "headphones", "Open-Ear Sport Headphones",
          "Open-ear bone conduction headphones that leave your ears free to hear traffic on runs and rides. IP67 dust and waterproof; 10-hour battery.",
          one(119.99), [*BT, "waterproof"],
          {"Type": "Open-ear (bone conduction)", "Connection": "Bluetooth 5.3", "Battery life": "10 hours", "Water resistance": "IP67 (waterproof)", "Noise cancelling": "No"}),
        P(SONORA, "headphones", "Reference Wired Over-Ear Headphones",
          "Open-back wired headphones with 50 mm drivers for critical listening, velour ear pads, and a detachable 3.5 mm cable with 6.35 mm adapter.",
          one(199.99), [], {"Type": "Over-ear, open back", "Connection": "Wired, 3.5 mm (6.35 mm adapter)", "Impedance": "32 ohm", "Noise cancelling": "No"}),
        P(SONORA, "headphones", "Wired Gaming Headset with Boom Microphone",
          "Over-ear gaming headset with a flip-to-mute boom mic, 50 mm drivers, and USB-A plus 3.5 mm connections for PC and consoles.",
          one(59.99), [], {"Type": "Over-ear", "Connection": "Wired, USB-A and 3.5 mm", "Microphone": "Detachable boom", "Noise cancelling": "No"}),
        # Speakers
        P(CRESTONE, "bluetooth-speaker", "Mini Bluetooth Speaker",
          "Palm-size Bluetooth speaker with 10 hours of playback, a carabiner clip, and IPX5 splash resistance.",
          one(19.99), [*BT, "water-resistant", "usb-c"], {"Battery life": "10 hours", "Water resistance": "IPX5", "Output": "5 W"}),
        P(CRESTONE, "bluetooth-speaker", "Waterproof Shower Speaker",
          "IPX7 waterproof shower speaker with a suction cup mount and built-in mic for calls.",
          one(24.99), [*BT, "waterproof"], {"Battery life": "8 hours", "Water resistance": "IPX7 (waterproof)", "Output": "5 W"}),
        colors(LUMEN, "bluetooth-speaker", "Beam Go Waterproof Bluetooth Speaker",
               "Compact waterproof and dustproof (IP67) speaker with 12 hours of playback and a built-in strap.",
               ["Black", "Teal", "Coral"], 34.99, [*BT, "waterproof", "usb-c"],
               {"Battery life": "12 hours", "Water resistance": "IP67 (waterproof)", "Output": "8 W"}),
        P(LUMEN, "bluetooth-speaker", "Beam Max Waterproof Party Speaker",
          "Large portable party speaker with 24 hours of playback, deep bass, light show, and IP67 waterproofing. Doubles as a power bank.",
          one(149.99), [*BT, "waterproof", "usb-c"], {"Battery life": "24 hours", "Water resistance": "IP67 (waterproof)", "Output": "60 W"}),
        P(SONORA, "bluetooth-speaker", "Room Wi-Fi & Bluetooth Home Speaker",
          "Plug-in home speaker with room-filling sound over Wi-Fi or Bluetooth, multi-room grouping, and voice assistant support.",
          one(199.99), ["wireless", "bluetooth", "smart-home"], {"Power": "AC (plug-in)", "Connection": "Wi-Fi, Bluetooth 5.2", "Water resistance": "None"}),
    ]


def tv_and_streaming() -> list[ProductSeed]:
    tvs = [  # (size, resolution, panel, price, refresh, extra title)
        (32, "HD 720p", "LED", 139.99, "60 Hz", ""),
        (43, "4K UHD", "LED", 249.99, "60 Hz", ""),
        (50, "4K UHD", "LED", 299.99, "60 Hz", ""),
        (55, "4K UHD", "LED", 379.99, "60 Hz", ""),
        (55, "4K UHD", "Quantum dot", 499.99, "120 Hz", "Quantum Dot "),
        (65, "4K UHD", "LED", 549.99, "60 Hz", ""),
        (65, "4K UHD", "OLED", 1499.99, "120 Hz", "OLED "),
        (75, "4K UHD", "Quantum dot", 899.99, "120 Hz", "Quantum Dot "),
    ]
    out = []
    for inches, res, panel, price, refresh, extra in tvs:
        four_k = res.startswith("4K")
        title = f"{inches}-Inch {extra}{'4K UHD' if four_k else 'HD'} Smart TV"
        out.append(P(
            NOVAVIEW, "tv", title,
            f"{inches}-inch {res} {panel} smart TV with built-in streaming apps, voice remote, and {refresh} refresh rate"
            f"{', HDR10 and HLG support' if four_k else ''}. Three HDMI ports and Wi-Fi.",
            one(price), ["wireless"] + (["energy-efficient"] if inches <= 43 else []),
            {"Screen size": f"{inches} in", "Resolution": res, "Panel": panel, "Refresh rate": refresh,
             "HDR": "HDR10, HLG" if four_k else "None", "HDMI ports": "3", "Smart platform": "Built-in streaming apps"},
        ))
    return out + [
        P(NOVAVIEW, "streaming-device", "Stream Stick HD",
          "Plug-in HDMI streaming stick for 1080p HD streaming with a voice remote and Wi-Fi.",
          one(29.99), ["wireless"], {"Resolution": "1080p HD", "Connection": "HDMI, Wi-Fi 5", "Remote": "Voice remote"}),
        P(NOVAVIEW, "streaming-device", "Stream Stick 4K",
          "Plug-in HDMI streaming stick for 4K HDR streaming with a voice remote and fast Wi-Fi 6.",
          one(49.99), ["wireless"], {"Resolution": "4K HDR", "Connection": "HDMI, Wi-Fi 6", "Remote": "Voice remote"}),
        P(NOVAVIEW, "streaming-device", "Stream Box 4K Pro",
          "Streaming box for 4K HDR with an Ethernet port, 32 GB storage for apps and games, and a backlit voice remote.",
          one(99.99), ["wireless"], {"Resolution": "4K HDR", "Connection": "HDMI, Wi-Fi 6E, Ethernet", "Storage": "32 GB"}),
        P(NOVAVIEW, "soundbar", "2.0 Channel Soundbar, 32 in",
          "Compact 32-inch soundbar with dialogue enhancement that connects by HDMI ARC, optical, or Bluetooth.",
          one(79.99), ["bluetooth"], {"Channels": "2.0", "Subwoofer": "None", "Connection": "HDMI ARC, optical, Bluetooth", "Width": "32 in"}),
        P(SONORA, "soundbar", "2.1 Channel Soundbar with Wireless Subwoofer",
          "Soundbar with a wireless subwoofer for deep bass, night mode, and HDMI eARC, optical, and Bluetooth connections.",
          one(199.99), ["bluetooth", "wireless"], {"Channels": "2.1", "Subwoofer": "Wireless, 6.5 in", "Connection": "HDMI eARC, optical, Bluetooth", "Width": "36 in"}),
        P(SONORA, "soundbar", "5.1 Channel Surround Soundbar with Wireless Subwoofer and Rear Speakers",
          "Home theater soundbar system with a wireless subwoofer and two wireless rear speakers for true surround sound. HDMI eARC and Wi-Fi.",
          one(349.99), ["bluetooth", "wireless"], {"Channels": "5.1", "Subwoofer": "Wireless, 8 in", "Connection": "HDMI eARC, optical, Bluetooth, Wi-Fi", "Width": "40 in"}),
    ]


def power_and_cables() -> list[ProductSeed]:
    return [
        P(VOLTWAVE, "usb-c-charger", "20W USB-C Fast Wall Charger",
          "Compact 20 W USB-C wall charger with Power Delivery that fast charges phones to 50% in about 30 minutes. Cable not included.",
          one(14.99), ["usb-c"], {"Wattage": "20 W", "Ports": "1 x USB-C", "Fast charging": "USB Power Delivery", "Cable included": "No"}),
        P(VOLTWAVE, "usb-c-charger", "30W USB-C Wall Charger with Cable",
          "30 W USB-C Power Delivery wall charger for phones, tablets, and small laptops, with a 3 ft USB-C to USB-C cable.",
          one(19.99), ["usb-c"], {"Wattage": "30 W", "Ports": "1 x USB-C", "Fast charging": "USB Power Delivery", "Cable included": "Yes, 3 ft USB-C to USB-C"}),
        P(VOLTWAVE, "usb-c-charger", "65W 2-Port GaN USB-C Wall Charger",
          "Compact GaN wall charger with two USB-C ports and 65 W total output, enough to charge a laptop and phone together. Folding prongs.",
          one(39.99), ["usb-c"], {"Wattage": "65 W total", "Ports": "2 x USB-C", "Fast charging": "USB Power Delivery", "Cable included": "No"}),
        P(VOLTWAVE, "usb-c-charger", "100W 4-Port GaN Charging Station",
          "Desktop GaN charger with three USB-C ports and one USB-A port, 100 W total, for charging a laptop, tablet, and phones at once.",
          one(59.99), ["usb-c"], {"Wattage": "100 W total", "Ports": "3 x USB-C, 1 x USB-A", "Fast charging": "USB Power Delivery", "Cable included": "No"}),
        P(VOLTWAVE, "car-charger", "Dual USB-C Car Charger, 45W",
          "Flush-fit car charger with two USB-C ports that share 45 W for fast charging two phones on the road.",
          one(17.99), ["usb-c"], {"Wattage": "45 W total", "Ports": "2 x USB-C", "Input": "12-24 V car socket"}),
        P(VOLTWAVE, "car-charger", "USB-C and USB-A Car Charger, 30W",
          "Car charger with one USB-C and one USB-A port for newer and older devices.",
          one(12.99), ["usb-c"], {"Wattage": "30 W total", "Ports": "1 x USB-C, 1 x USB-A", "Input": "12-24 V car socket"}),
        P(VOLTWAVE, "wireless-charger", "15W Wireless Charging Pad",
          "Slim wireless charging pad for phones and earbuds, up to 15 W, with a non-slip surface. Works through cases up to 5 mm.",
          one(19.99), ["wireless", "usb-c"], {"Wattage": "15 W max", "Standard": "Universal wireless charging", "Input": "USB-C (adapter not included)"}),
        P(VOLTWAVE, "wireless-charger", "3-in-1 Magnetic Wireless Charging Stand",
          "Magnetic wireless stand that charges a phone, earbuds, and a smartwatch at once. Includes a 30 W wall adapter.",
          one(49.99), ["wireless", "usb-c"], {"Charging output": "15 W phone, 5 W earbuds, 2.5 W watch", "Standard": "Magnetic wireless charging", "Adapter included": "Yes, 30 W"}),
        P(VOLTWAVE, "usb-c-cable", "USB-C to USB-C Cable, 60W",
          "Durable nylon-braided USB-C to USB-C cable for charging at up to 60 W and USB 2.0 data. Choose your length.",
          sz(("3FT", "3 ft", 8.99), ("6FT", "6 ft", 10.99), ("10FT", "10 ft", 13.99)), ["usb-c"],
          {"Connectors": "USB-C to USB-C", "Max power": "60 W", "Data speed": "USB 2.0 (480 Mbps)", "Jacket": "Nylon braided"}),
        P(VOLTWAVE, "usb-c-cable", "USB-C to USB-C Cable, 240W, 6 ft",
          "Heavy-duty 6 ft USB-C cable rated for 240 W charging, for high-power laptops and gaming handhelds.",
          one(16.99, "6 ft", "6FT"), ["usb-c"],
          {"Connectors": "USB-C to USB-C", "Max power": "240 W", "Data speed": "USB 2.0 (480 Mbps)", "Length": "6 ft"}),
        P(VOLTWAVE, "usb-c-cable", "USB-C to USB-A Cable",
          "Braided USB-A to USB-C cable for charging and syncing USB-C devices from older chargers and computers.",
          sz(("3FT", "3 ft", 7.99), ("6FT", "6 ft", 9.99), ("10FT", "10 ft", 12.99)), ["usb-c"],
          {"Connectors": "USB-A to USB-C", "Max power": "15 W (3 A)", "Data speed": "USB 2.0 (480 Mbps)", "Jacket": "Nylon braided"}),
        P(VOLTWAVE, "hdmi-cable", "High Speed HDMI Cable, 4K 60Hz, 6 ft",
          "High speed HDMI cable that supports 4K at 60 Hz, HDR, and audio return channel.",
          one(9.99, "6 ft", "6FT"), [], {"Supports": "4K @ 60 Hz, HDR, ARC", "Length": "6 ft"}),
        P(VOLTWAVE, "power-bank", "10,000 mAh Slim Power Bank",
          "Pocket-size 10,000 mAh power bank with USB-C in/out at 20 W, charging a typical phone about twice.",
          one(19.99), ["rechargeable", "usb-c"], {"Capacity": "10,000 mAh", "Output": "20 W USB-C, 12 W USB-A", "Weight": "7.4 oz"}),
        P(VOLTWAVE, "power-bank", "5,000 mAh Magnetic Wireless Power Bank",
          "Snap-on magnetic wireless power bank that charges compatible phones without a cable. USB-C for wired charging too.",
          one(29.99), ["rechargeable", "wireless", "usb-c"], {"Capacity": "5,000 mAh", "Output": "7.5 W wireless, 20 W USB-C", "Weight": "4.8 oz"}),
        P(LUMEN, "power-bank", "Charge 26K Laptop Power Bank, 100W",
          "High-capacity 26,800 mAh power bank with 100 W USB-C output that can recharge most laptops once, plus two more ports. Carry-on approved.",
          one(79.99), ["rechargeable", "usb-c"], {"Capacity": "26,800 mAh", "Output": "100 W USB-C, 2 more ports", "Weight": "1.2 lb"}),
        P(VOLTWAVE, "surge-protector", "6-Outlet Surge Protector with 2 USB-C Ports",
          "Surge protector power strip with six outlets, two USB-C ports, and a 6 ft cord. 1,800 joules.",
          one(24.99), ["usb-c"], {"Outlets": "6 AC", "USB ports": "2 x USB-C (20 W total)", "Surge rating": "1,800 joules", "Cord": "6 ft"}),
        colors(VOLTWAVE, "phone-case", "Clear Protective Phone Case",
               "Slim, clear shock-absorbing case with raised edges to protect the screen and camera. Wireless charging compatible. Choose your phone size.",
               ["For 6.1-inch phones", "For 6.7-inch phones"], 14.99, [], {"Material": "TPU and polycarbonate", "Drop protection": "6 ft"}, attribute="fits"),
        colors(VOLTWAVE, "phone-case", "Rugged Dual-Layer Phone Case",
               "Heavy-duty two-layer case with a built-in kickstand and 12 ft drop protection. Choose your phone size.",
               ["For 6.1-inch phones", "For 6.7-inch phones"], 24.99, [], {"Material": "Polycarbonate shell, silicone inner layer", "Drop protection": "12 ft"}, attribute="fits"),
        colors(VOLTWAVE, "screen-protector", "Tempered Glass Screen Protector, 2-Pack",
               "Two 9H tempered glass screen protectors with an installation frame for bubble-free application. Choose your phone size.",
               ["For 6.1-inch phones", "For 6.7-inch phones"], 9.99, [], {"Hardness": "9H", "Count": "2"}, attribute="fits"),
    ]


def smart_home() -> list[ProductSeed]:
    sh = ["smart-home", "wireless"]
    return [
        P(BRIGHTGATE, "smart-plug", "Mini Wi-Fi Smart Plug",
          "Compact Wi-Fi smart plug that lets you schedule and control lamps and small appliances from your phone or by voice. No hub required.",
          sz(("2PK", "2-pack", 19.99), ("4PK", "4-pack", 34.99)), [*sh, "energy-efficient"],
          {"Connection": "2.4 GHz Wi-Fi", "Hub required": "No", "Max load": "15 A", "Energy monitoring": "Yes"}),
        P(BRIGHTGATE, "smart-plug", "Outdoor Wi-Fi Smart Plug, 2 Outlets",
          "Weatherproof outdoor smart plug with two independently controlled outlets for string lights and landscape lighting.",
          one(24.99), [*sh, "water-resistant"], {"Connection": "2.4 GHz Wi-Fi", "Hub required": "No", "Outlets": "2", "Weather rating": "IP44"}),
        P(BRIGHTGATE, "smart-bulb", "Smart LED Bulbs, Tunable White, 2-Pack",
          "Wi-Fi A19 LED bulbs that dim and change from warm to cool white on a schedule or by voice. 60 W equivalent; no hub required.",
          one(14.99, "2-pack", "2PK"), [*sh, "energy-efficient"], {"Connection": "2.4 GHz Wi-Fi", "Colors": "Tunable white 2700-6500K", "Brightness": "800 lumens", "Base": "E26"}),
        P(BRIGHTGATE, "smart-light-strip", "Smart LED Light Strip, 16.4 ft",
          "Color-changing Wi-Fi LED light strip with music sync and app control. Cuttable and adhesive-backed.",
          one(24.99), sh, {"Connection": "2.4 GHz Wi-Fi", "Length": "16.4 ft", "Colors": "16 million"}),
        P(BRIGHTGATE, "security-camera", "Indoor Security Camera, 1080p",
          "Plug-in indoor Wi-Fi camera with 1080p video, night vision, two-way talk, motion alerts, and local microSD recording.",
          one(29.99), sh, {"Resolution": "1080p", "Power": "Plug-in (USB)", "Night vision": "Yes", "Storage": "microSD or optional cloud", "Field of view": "110°"}),
        P(BRIGHTGATE, "security-camera", "Pan & Tilt Indoor Security Camera, 2K",
          "Indoor camera with 360° pan and tilt, 2K video, person and pet detection, and a privacy mode that turns the lens away.",
          one(44.99), sh, {"Resolution": "2K", "Power": "Plug-in (USB)", "Night vision": "Yes", "Pan/tilt": "360° pan, 114° tilt"}),
        P(BRIGHTGATE, "security-camera", "Wireless Outdoor Security Camera, 2K",
          "Battery-powered outdoor camera with 2K video, color night vision, a built-in spotlight, and up to 6 months per charge. IP65 weatherproof.",
          one(79.99), [*sh, "rechargeable", "water-resistant"], {"Resolution": "2K", "Power": "Rechargeable battery", "Battery life": "Up to 6 months", "Weather rating": "IP65"}),
        P(BRIGHTGATE, "video-doorbell", "Wired Video Doorbell, 1080p",
          "Wired video doorbell with 1080p HD video, head-to-toe view, two-way talk, and motion alerts. Uses existing doorbell wiring.",
          one(59.99), sh, {"Resolution": "1080p", "Power": "Hardwired (existing doorbell wiring)", "Field of view": "160° vertical"}),
        P(BRIGHTGATE, "video-doorbell", "Battery Video Doorbell, 2K",
          "Wire-free video doorbell with a removable rechargeable battery, 2K video, package detection, and a chime included.",
          one(99.99), [*sh, "rechargeable", "water-resistant"], {"Resolution": "2K", "Power": "Rechargeable battery or wired", "Chime included": "Yes"}),
        P(BRIGHTGATE, "smart-thermostat", "Smart Wi-Fi Thermostat",
          "Programmable Wi-Fi thermostat with a touch screen, geofencing, and energy reports. Requires a C-wire (adapter included).",
          one(99.99), [*sh, "energy-efficient"], {"Connection": "Wi-Fi", "C-wire": "Required (adapter included)", "Display": "Color touch screen"}),
    ]


def computing() -> list[ProductSeed]:
    return [
        P(KEYLOFT, "keyboard", "Wireless Keyboard and Mouse Combo",
          "Full-size quiet wireless keyboard and mouse sharing one USB-A receiver, with a 2-year keyboard battery life.",
          one(29.99), ["wireless"], {"Connection": "2.4 GHz USB-A receiver", "Layout": "Full size with number pad", "Power": "AA/AAA batteries (included)"}),
        P(KEYLOFT, "keyboard", "Bluetooth Multi-Device Keyboard",
          "Compact rechargeable Bluetooth keyboard that switches between three devices, for computers, tablets, and phones.",
          one(39.99), ["wireless", "bluetooth", "rechargeable", "usb-c"], {"Connection": "Bluetooth, 3 devices", "Layout": "Compact (no number pad)", "Power": "Rechargeable, USB-C"}),
        P(KEYLOFT, "keyboard", "Mechanical Gaming Keyboard, Wired",
          "Wired mechanical keyboard with tactile switches, per-key RGB backlighting, and a detachable USB-C cable.",
          one(59.99), ["usb-c"], {"Connection": "Wired, USB-C to USB-A", "Switches": "Tactile mechanical", "Backlight": "RGB"}),
        colors(KEYLOFT, "mouse", "Wireless Mouse",
               "Compact wireless mouse with a USB-A nano receiver, silent clicks, and 18-month battery life.",
               ["Black", "Gray", "Blue"], 12.99, ["wireless"], {"Connection": "2.4 GHz USB-A receiver", "DPI": "1600", "Power": "1 AA battery (included)"}),
        P(KEYLOFT, "mouse", "Ergonomic Vertical Wireless Mouse",
          "Vertical mouse that keeps your wrist in a natural handshake position. Rechargeable, with Bluetooth and a USB receiver.",
          one(29.99), ["wireless", "bluetooth", "rechargeable", "usb-c"], {"Connection": "Bluetooth or 2.4 GHz receiver", "DPI": "Up to 2400", "Power": "Rechargeable, USB-C"}),
        P(KEYLOFT, "mouse", "Wired Optical Mouse",
          "Basic wired USB-A optical mouse for desktops and laptops.",
          one(8.99), [], {"Connection": "Wired, USB-A", "DPI": "1000"}),
        P(LUMEN, "webcam", "Clearview 4K Webcam with Ring Light",
          "4K webcam with a built-in dimmable ring light, autofocus, dual mics, and a privacy cover.",
          one(89.99), ["usb-c"], {"Resolution": "4K at 30 fps", "Connection": "USB-C (USB-A adapter included)", "Microphone": "Dual", "Privacy cover": "Yes"}),
        P(NOVAVIEW, "monitor", "24-Inch 1080p IPS Monitor",
          "24-inch Full HD IPS monitor with 100 Hz refresh, thin bezels, and HDMI and DisplayPort inputs. VESA mountable.",
          one(119.99), ["energy-efficient"], {"Screen size": "24 in", "Resolution": "1920 x 1080", "Panel": "IPS", "Refresh rate": "100 Hz", "Inputs": "HDMI, DisplayPort"}),
        P(NOVAVIEW, "monitor", "27-Inch QHD 165Hz Gaming Monitor",
          "27-inch 1440p IPS gaming monitor with 165 Hz refresh, 1 ms response, and adaptive sync.",
          one(219.99), [], {"Screen size": "27 in", "Resolution": "2560 x 1440", "Panel": "IPS", "Refresh rate": "165 Hz", "Inputs": "2 x HDMI, DisplayPort"}),
        P(NOVAVIEW, "monitor", "27-Inch 4K USB-C Monitor",
          "27-inch 4K IPS monitor with a single-cable USB-C connection that also charges your laptop at 65 W. Height-adjustable stand.",
          one(329.99), ["usb-c"], {"Screen size": "27 in", "Resolution": "3840 x 2160", "Panel": "IPS", "Refresh rate": "60 Hz", "Inputs": "USB-C (65 W), HDMI, DisplayPort"}),
        P(KEYLOFT, "usb-hub", "7-in-1 USB-C Hub",
          "Aluminum USB-C hub with 4K HDMI, two USB-A 3.0 ports, SD and microSD card readers, and 100 W pass-through charging.",
          one(34.99), ["usb-c"], {"Ports": "HDMI 4K, 2 x USB-A 3.0, USB-C PD 100 W, SD, microSD", "Connection": "USB-C"}),
        P(KEYLOFT, "usb-hub", "4-Port USB 3.0 Hub",
          "Slim four-port USB-A 3.0 hub with a 2 ft cable for adding ports to a desktop or laptop.",
          one(14.99), [], {"Ports": "4 x USB-A 3.0", "Connection": "USB-A"}),
        P(KEYLOFT, "ssd", "Portable External SSD, USB-C",
          "Pocket-size portable solid-state drive with read speeds up to 1,050 MB/s and a drop-resistant shell. USB-C and USB-A cables included.",
          sz(("500GB", "500 GB", 59.99), ("1TB", "1 TB", 89.99), ("2TB", "2 TB", 149.99)), ["usb-c"],
          {"Interface": "USB 3.2 Gen 2 (USB-C)", "Read speed": "Up to 1,050 MB/s", "Drop resistance": "6.5 ft"}),
        P(KEYLOFT, "ssd", "Internal NVMe M.2 SSD, PCIe 4.0",
          "M.2 2280 NVMe solid-state drive for desktops, laptops, and game consoles with read speeds up to 7,000 MB/s.",
          sz(("1TB", "1 TB", 69.99), ("2TB", "2 TB", 129.99)), [],
          {"Interface": "PCIe 4.0 x4 NVMe", "Form factor": "M.2 2280", "Read speed": "Up to 7,000 MB/s"}),
        P(KEYLOFT, "memory-card", "microSD Memory Card with Adapter",
          "U3 V30 microSDXC card for phones, cameras, drones, and handheld consoles, with a full-size SD adapter.",
          sz(("128GB", "128 GB", 14.99), ("256GB", "256 GB", 24.99)), [],
          {"Speed class": "U3, V30, A2", "Read speed": "Up to 160 MB/s"}),
        P(KEYLOFT, "flash-drive", "USB-C and USB-A Dual Flash Drive, 64 GB",
          "Two-in-one flash drive with USB-C and USB-A connectors for moving files between phones and computers.",
          one(12.99, "64 GB", "64GB"), ["usb-c"], {"Capacity": "64 GB", "Interface": "USB 3.2 Gen 1"}),
        P(KEYLOFT, "game-controller", "Wireless Game Controller for PC and Phones",
          "Rechargeable Bluetooth game controller with a phone clip, works with PCs, phones, and tablets.",
          one(39.99), ["wireless", "bluetooth", "rechargeable", "usb-c"], {"Connection": "Bluetooth or USB-C", "Battery life": "20 hours"}),
    ]


def tablets_and_printers() -> list[ProductSeed]:
    return [
        P(LUMEN, "tablet", "Lumen Tab 8 Kids Edition Tablet, 32 GB",
          "8-inch kids' tablet with a kid-proof bumper case and stand, parental controls, and a 2-year worry-free replacement guarantee. Ages 3-7.",
          one(99.99), ["kids", "wireless", "rechargeable", "usb-c"],
          {"Screen size": "8 in", "Storage": "32 GB", "Battery life": "12 hours", "Case": "Kid-proof bumper included", "Ages": "3-7"}),
        P(LUMEN, "tablet", "Lumen Tab 11 Plus Tablet",
          "11-inch 2K tablet with an octa-core processor, quad speakers, and 8 GB of RAM for streaming, drawing, and multitasking.",
          sz(("128GB", "128 GB", 299.99), ("256GB", "256 GB", 349.99)), ["wireless", "rechargeable", "usb-c"],
          {"Screen size": "11 in", "Resolution": "2000 x 1200", "RAM": "8 GB", "Battery life": "14 hours"}),
        P(LUMEN, "e-reader", "Lumen Page 6 E-Reader",
          "Glare-free 6-inch e-ink reader with an adjustable front light, 16 GB of storage, and weeks of battery life.",
          one(99.99), ["wireless", "rechargeable", "usb-c"],
          {"Screen size": "6 in e-ink", "Storage": "16 GB", "Front light": "Adjustable", "Water resistance": "None", "Battery life": "Up to 6 weeks"}),
        P(LUMEN, "e-reader", "Lumen Page 7 Waterproof E-Reader",
          "7-inch 300 ppi e-ink reader with warm light, page-turn buttons, and IPX8 waterproofing for the bath or beach.",
          one(159.99), ["wireless", "rechargeable", "usb-c", "waterproof"],
          {"Screen size": "7 in e-ink, 300 ppi", "Storage": "32 GB", "Front light": "Adjustable warm light", "Water resistance": "IPX8 (waterproof)", "Battery life": "Up to 10 weeks"}),
        P(PRESSMARK, "printer", "All-in-One Wireless Inkjet Printer",
          "Wireless color inkjet printer that prints, scans, and copies, with automatic two-sided printing and phone printing. Uses PM-20 ink.",
          one(89.99), ["wireless"], {"Type": "Color inkjet all-in-one", "Functions": "Print, scan, copy", "Connection": "Wi-Fi, USB", "Ink": "PM-20 / PM-20XL cartridges"}),
        P(PRESSMARK, "printer", "Wireless Monochrome Laser Printer",
          "Fast black-and-white laser printer, 32 pages per minute, with auto duplex and a 250-sheet tray. Uses PM-L5 toner.",
          one(149.99), ["wireless"], {"Type": "Monochrome laser", "Functions": "Print only", "Speed": "32 ppm", "Connection": "Wi-Fi, USB, Ethernet", "Toner": "PM-L5"}),
        P(PRESSMARK, "printer-ink", "PM-20 Black Ink Cartridge",
          "Standard-yield black ink cartridge for Pressmark all-in-one printers, about 200 pages.",
          one(24.99), [], {"Color": "Black", "Yield": "About 200 pages", "Compatible with": "Pressmark PM-20 printers"}),
        P(PRESSMARK, "printer-ink", "PM-20 Tri-Color Ink Cartridge",
          "Standard-yield cyan, magenta, and yellow ink cartridge, about 165 pages.",
          one(29.99), [], {"Color": "Tri-color", "Yield": "About 165 pages", "Compatible with": "Pressmark PM-20 printers"}),
        P(PRESSMARK, "printer-ink", "PM-20XL High-Yield Black and Tri-Color Ink, Combo Pack",
          "High-yield black and tri-color ink cartridges in one pack, about 480 black and 330 color pages.",
          one(69.99), [], {"Color": "Black and tri-color", "Yield": "About 480 black / 330 color pages", "Compatible with": "Pressmark PM-20 printers"}),
        P(PRESSMARK, "printer-ink", "PM-L5 Black Toner Cartridge",
          "Black toner cartridge for Pressmark laser printers, about 2,600 pages.",
          one(64.99), [], {"Color": "Black", "Yield": "About 2,600 pages", "Compatible with": "Pressmark PM-L5 laser printers"}),
    ]
# fmt: on


def products() -> list[ProductSeed]:
    return [
        *audio(), *tv_and_streaming(), *power_and_cables(), *smart_home(), *computing(),
        *tablets_and_printers(),
    ]  # fmt: skip
