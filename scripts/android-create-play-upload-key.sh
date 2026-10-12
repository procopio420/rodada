#!/usr/bin/env bash
set -euo pipefail

# This helper runs ONLY on the operator's workstation, never in CI.
# Never commit keystores or paste their passwords into chat/issue comments.
keystore="${1:-$HOME/.config/rodada/play-upload.jks}"
if [[ -e "$keystore" ]]; then
  echo "Upload keystore already exists: $keystore; refusing to overwrite." >&2
  exit 1
fi

mkdir -p "$(dirname "$keystore")"
chmod 700 "$(dirname "$keystore")"
umask 077
echo "Generating a new Google Play UPLOAD key at: $keystore"
echo "Choose and securely back up the keystore and password. Play App Signing manages the app signing key."
keytool -genkeypair -v -storetype PKCS12 \
  -keystore "$keystore" -alias rodada-upload \
  -keyalg RSA -keysize 4096 -validity 10000 \
  -dname "CN=Rodada Upload, O=Rodada, C=BR"
chmod 600 "$keystore"
echo "Created upload keystore. Store a separate encrypted backup."
echo "Certificate fingerprints (you will be asked for the keystore password):"
keytool -list -v -keystore "$keystore" -alias rodada-upload
