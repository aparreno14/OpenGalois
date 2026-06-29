#!/usr/bin/env bash
set -euo pipefail

export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

OUT_DIR="deg4_example_certs"
CERT_DIR="$OUT_DIR/certs"
SUMMARY_DIR="$OUT_DIR/summaries"
VERIFY_DIR="$OUT_DIR/verify"

mkdir -p "$CERT_DIR" "$SUMMARY_DIR" "$VERIFY_DIR"

CASES=(
  "s4_01_t4_minus_t_minus_1|1 0 0 -1 -1|S4 candidato: t^4 - t - 1"
  "s4_02_t4_plus_2t_plus_2|1 0 0 2 2|S4 candidato: t^4 + 2t + 2"

  "a4_01_t4_plus_8t_plus_12|1 0 0 8 12|A4 candidato: t^4 + 8t + 12"
  "a4_02_t4_plus_24t_plus_36|1 0 0 24 36|A4 candidato: t^4 + 24t + 36"

  "v4_01_t4_plus_36t_plus_63|1 0 0 36 63|V4 candidato: t^4 + 36t + 63"
  "v4_02_t4_plus_24t_plus_73|1 0 0 24 73|V4 candidato: t^4 + 24t + 73"

  "kw_01_c4_t4_plus_5t_plus_5|1 0 0 5 5|Kappe-Warren C4 candidato: t^4 + 5t + 5"
  "kw_02_d4_t4_plus_3t_plus_3|1 0 0 3 3|Kappe-Warren D4 candidato: t^4 + 3t + 3"
  "kw_03_d4_t4_plus_4t2_minus_2|1 0 4 0 -2|Kappe-Warren mixto candidato: t^4 + 4t^2 - 2"
  "kw_04_d4_t4_minus_5t3_minus_10t2_minus_25t_plus_25|1 -5 -10 -25 25|Kappe-Warren mixto candidato: t^4 - 5t^3 - 10t^2 - 25t + 25"
)

MANIFEST="$OUT_DIR/manifest.tsv"
printf "name\tcoeffs\tdescription\tcertificate\tverify_json\tsummary\n" > "$MANIFEST"

for entry in "${CASES[@]}"; do
  IFS='|' read -r name coeffs desc <<< "$entry"

  cert="$CERT_DIR/${name}.json"
  summary="$SUMMARY_DIR/${name}.txt"
  verify_json="$VERIFY_DIR/${name}.verify.json"

  echo "==> $desc"
  echo "    coeffs: $coeffs"

  # shellcheck disable=SC2086
  opengalois analyze --output "$cert" $coeffs > "$summary"

  opengalois verify --json "$cert" > "$verify_json"

  printf "%s\t%s\t%s\t%s\t%s\t%s\n" \
    "$name" "$coeffs" "$desc" "$cert" "$verify_json" "$summary" >> "$MANIFEST"
done

echo
echo "Listo."
echo "Certificados:      $CERT_DIR"
echo "Summaries:         $SUMMARY_DIR"
echo "Verificaciones:    $VERIFY_DIR"
echo "Manifest:          $MANIFEST"