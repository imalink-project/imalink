#!/bin/bash

echo "🚀 STEG 9: Opprett ny SvelteKit-applikasjon"
echo "=========================================="

# Naviger til prosjektmappen
cd /home/kjell/git_prosjekt/imalink

# Sjekk at Node.js fungerer
if ! command -v node &> /dev/null; then
    echo "❌ Node.js ikke funnet. Åpne en ny terminal og kjør:"
    echo "   source ~/.bashrc"
    echo "   nvm use --lts"
    exit 1
fi

echo "✅ Node.js versjon: $(node --version)"
echo "✅ npm versjon: $(npm --version)"

# Fjern gammel frontend-mappe hvis den finnes
if [ -d "frontend" ]; then
    echo "Fjerner gammel frontend-mappe..."
    rm -rf frontend
fi

echo ""
echo "📦 Opprett ny SvelteKit-applikasjon..."

# Opprett ny SvelteKit app
npm create svelte@latest frontend

echo ""
echo "📋 NESTE STEG:"
echo "1. cd frontend"
echo "2. npm install"
echo "3. npm run dev"

echo ""
echo "✅ SvelteKit-applikasjon opprettet!"