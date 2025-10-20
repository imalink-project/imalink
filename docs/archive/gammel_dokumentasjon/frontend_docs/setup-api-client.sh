#!/bin/bash

echo "🔧 STEG 3: Legg til API-integrasjon"
echo "=================================="

cd /home/kjell/git_prosjekt/imalink/frontend

echo "📦 Installerer axios for API-kall..."
npm install axios

echo "📂 Oppretter API-klient struktur..."
mkdir -p src/lib/api

echo "✅ Klar for å lage API-integrasjon!"