import pandas as pd


def decode_arinc_coordinate(coord_str: str) -> float | None:
    if not isinstance(coord_str, str):
        return None

    coord_str = coord_str.strip()
    if len(coord_str) < 9:
        return None

    hemi = coord_str[0]
    if hemi not in ("N", "S", "E", "W"):
        return None

    try:
        if hemi in ("N", "S"):
            # LAT: NDDMMSSss (9 chars minimum, e.g., N48073012 -> N + 2 deg + 2 min + 2 sec + 2 hundredths)
            deg = float(coord_str[1:3])
            min_ = float(coord_str[3:5])
            sec = float(coord_str[5:7] + "." + coord_str[7:])
        else:
            # LON: EDDDMMSSss (10 chars standard, or 9 if truncated: E + 3 deg + 2 min + rest for sec)
            deg = float(coord_str[1:4])
            min_ = float(coord_str[4:6])
            sec = float(coord_str[6:8] + "." + coord_str[8:])

        decimal = deg + (min_ / 60.0) + (sec / 3600.0)

        if hemi in ("S", "W"):
            decimal = -decimal

        return round(decimal, 6)

    except Exception:
        return None


def decode_magvar(s: str) -> float | None:
    if not isinstance(s, str) or len(s) < 5:
        return None

    hemi = s[0]
    if hemi not in ("E", "W"):
        return None

    try:
        deg = float(s[1:3])
        min_ = float(s[3:5])
        decimal = deg + (min_ / 60.0)
        return decimal if hemi == "E" else -decimal
    except Exception:
        return None


def apply_decoders(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    for col in df.columns:
        if col.endswith(("Latitude", "Longitude")):
            out[col + "_decimal"] = (
                df[col]
                .apply(lambda v: decode_arinc_coordinate(v) if pd.notna(v) else None)
                .astype("object")
            )
        elif col in ("DynamicMagneticVariation", "MagneticVariation"):
            out[col + "_decimal"] = (
                df[col]
                .apply(lambda v: decode_magvar(v) if pd.notna(v) else None)
                .astype("object")
            )

    return out
