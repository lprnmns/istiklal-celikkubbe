# Phase 58: Cinematic Pre-Flight Layout

## Layout Structure
- **Top-left**: İSTİKLAL C2 brand + subtitle
- **Top-right**: Live clock + DRY-RUN mode badge
- **Left floating panel**: "BAĞLANTI KONTROLLERİ" — 7 diagnostic rows with LED dots, expandable details
- **Right top panel**: "HIZLI SİSTEM ÖZETİ" — system profile, mode, camera, model, 3D status
- **Right bottom panel**: "GÜVENLİK DURUMU" — 5 safety gate confirmations with green LEDs
- **Bottom center**: Primary glowing "SİSTEMİ BAŞLAT" CTA + secondary "SADECE 3D DÜNYAYI AÇ"

## Glassmorphism Spec
```css
background: rgba(5, 12, 24, 0.72);
backdrop-filter: blur(14px);
border: 1px solid rgba(0, 220, 255, 0.18);
border-radius: 14px;
```

## LED Semantics
| Color | Meaning |
|-------|---------|
| Green | Confirmed OK |
| Yellow | Expected offline / warning |
| Red (blinking) | Confirmed failure |
