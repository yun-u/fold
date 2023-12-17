def utf16_to_utf32(s: str) -> str:
    return b"".join(
        [ord(s[0]).to_bytes(2, "big"), ord(s[1]).to_bytes(2, "big")]
    ).decode("utf-16be")


def utf32_to_utf16(s: str) -> str:
    return "".join(
        [
            chr(int.from_bytes(s.encode("utf-16be")[i : i + 2], "big"))
            for i in range(0, 4, 2)
        ]
    )
