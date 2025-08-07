#!/bin/zsh

displayplacer="/opt/homebrew/bin/displayplacer"
connected="$($displayplacer list)"

macbook_id="37D8832A-2D66-02CA-B9F7-8F30A301B230"
dell_id="5225484A-6561-DA4D-0857-D6964E3302DB"
arzopa_id="833E557A-1ED7-9DB3-0857-D6964E3302DB"

has_macbook=$(echo "$connected" | grep -q "$macbook_id" && echo "yes")
has_dell=$(echo "$connected" | grep -q "$dell_id" && echo "yes")
has_arzopa=$(echo "$connected" | grep -q "$arzopa_id" && echo "yes")

# --- Get best HiDPI for Arzopa ---
available_modes=$($displayplacer list | grep -A40 "$arzopa_id")
arzopa_res=""
arzopa_found=""

# Use 1440x900 if Dell is present, otherwise prefer 1920x1200
if [[ $has_dell == "yes" ]]; then
  preferred_modes=("1440x900" "1280x800")
else
  preferred_modes=("1920x1200" "1440x900" "1280x800")
fi

for mode in "${preferred_modes[@]}"; do
  if echo "$available_modes" | grep "res:$mode" | grep -q "scaling:on"; then
    arzopa_res="res:$mode hz:60 color_depth:8 scaling:on"
    arzopa_found="$mode"
    break
  fi
done

if [[ -z "$arzopa_res" ]]; then
  arzopa_res="res:1280x800 hz:60 color_depth:8 scaling:on"
  arzopa_found="1280x800 (forced fallback)"
  echo "🔴 HiDPI detection failed — forcing $arzopa_found"
else
  echo "🟢 Using HiDPI mode for Arzopa: $arzopa_found"
fi

# --- Layouts ---
if [[ $has_macbook && $has_dell && $has_arzopa ]]; then
  echo "🖥️  Home setup: Arzopa (left), Dell (center), MacBook (below Dell)"
  $displayplacer \
    "id:$arzopa_id $arzopa_res origin:(-1280,200) degree:0" \
    "id:$dell_id res:2560x1440 hz:60 color_depth:8 scaling:on origin:(0,0) degree:0" \
    "id:$macbook_id res:1680x1050 hz:60 color_depth:8 scaling:on origin:(0,1440) degree:0"

elif [[ $has_macbook && $has_arzopa ]]; then
  echo "💼  MacBook + Arzopa only (MacBook LEFT, Arzopa RIGHT)"
  $displayplacer \
    "id:$macbook_id res:1680x1050 hz:60 color_depth:8 scaling:on origin:(0,0) degree:0" \
    "id:$arzopa_id $arzopa_res origin:(1680,0) degree:0"

elif [[ $has_macbook && $has_dell ]]; then
  echo "🧑‍💻  MacBook + Dell only"
  $displayplacer \
    "id:$macbook_id res:1680x1050 hz:60 color_depth:8 scaling:on origin:(0,1440) degree:0" \
    "id:$dell_id res:2560x1440 hz:60 color_depth:8 scaling:on origin:(0,0) degree:0"

else
  echo "🔌  Only MacBook or unknown display config — skipping."
fi
