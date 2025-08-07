import subprocess
import re

DISPLAYPLACER = "/opt/homebrew/bin/displayplacer"

macbook_id = "37D8832A-2D66-02CA-B9F7-8F30A301B230"
dell_id = "5225484A-6561-DA4D-0857-D6964E3302DB"
arzopa_id = "833E557A-1ED7-9DB3-0857-D6964E3302DB"

def get_connected_screens():
    output = subprocess.check_output([DISPLAYPLACER, "list"]).decode()
    return {
        "macbook": macbook_id in output,
        "dell": dell_id in output,
        "arzopa": arzopa_id in output,
        "raw": output
    }

def get_best_arzopa_mode(output: str, has_dell: bool):
    section = re.search(rf"{arzopa_id}(.+?)(\n\n|$)", output, re.DOTALL)
    if not section:
        print("🔴 Could not find Arzopa section in output")
        return "res:1280x800 hz:60 color_depth:8 scaling:on", "1280x800 (fallback)"

    modes = section.group(0)
    preferred = ["1440x900", "1280x800"] if has_dell else ["1920x1200", "1440x900", "1280x800"]

    for mode in preferred:
        if f"res:{mode}" in modes and "scaling:on" in modes:
            return f"res:{mode} hz:60 color_depth:8 scaling:on", mode

    return "res:1280x800 hz:60 color_depth:8 scaling:on", "1280x800 (fallback)"

def apply_layout(mode: str):
    info = get_connected_screens()
    connected = info["raw"]
    has_macbook, has_dell, has_arzopa = info["macbook"], info["dell"], info["arzopa"]
    arzopa_res, arzopa_label = get_best_arzopa_mode(connected, has_dell)

    if mode == "home" and has_macbook and has_dell and has_arzopa:
        print(f"🖥️  Home setup: Arzopa (left), Dell (center), MacBook (below Dell)")
        run_layout([
            f'id:{arzopa_id} {arzopa_res} origin:(-1280,200) degree:0',
            f'id:{dell_id} res:2560x1440 hz:60 color_depth:8 scaling:on origin:(0,0) degree:0',
            f'id:{macbook_id} res:1680x1050 hz:60 color_depth:8 scaling:on origin:(0,1440) degree:0',
        ])

    elif mode == "arzopa_only" and has_macbook and has_arzopa:
        print(f"💼  MacBook + Arzopa only")
        run_layout([
            f'id:{macbook_id} res:1680x1050 hz:60 color_depth:8 scaling:on origin:(0,0) degree:0',
            f'id:{arzopa_id} {arzopa_res} origin:(1680,0) degree:0',
        ])

    elif mode == "work" and has_macbook and has_dell:
        print(f"🧑‍💻  MacBook + Dell only")
        run_layout([
            f'id:{macbook_id} res:1680x1050 hz:60 color_depth:8 scaling:on origin:(0,1440) degree:0',
            f'id:{dell_id} res:2560x1440 hz:60 color_depth:8 scaling:on origin:(0,0) degree:0',
        ])

    else:
        print("🔌  Only MacBook or unknown config — skipping.")

def run_layout(commands):
    for cmd in commands:
        full = f'{DISPLAYPLACER} "{cmd}"'
        print(f"🔧  Running: {full}")
        subprocess.run(full, shell=True)
