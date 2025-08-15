def get_pool(character: dict, name: str) -> int:
    val = character.get("Other Stats", {}).get(name, 0)
    try:
        return int(val)
    except Exception:
        return 0

def set_pool(character: dict, name: str, value: int):
    character.setdefault("Other Stats", {})[name] = int(max(0, value))

def spend_pool(character: dict, name: str, amount: int = 1) -> bool:
    cur = get_pool(character, name)
    if cur >= amount:
        set_pool(character, name, cur - amount)
        return True
    return False

def list_pools(character: dict):
    # Common EP2e pools; adapt names as needed on your sheets
    pools = ["Insight", "Moxie", "Vigor", "Flex"]
    out = {}
    for p in pools:
        out[p] = get_pool(character, p)
    return out
