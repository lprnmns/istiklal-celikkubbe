# 15. Agent Ana Task Rapor Şablonu

Agent her ana task sonunda bu formatta rapor vermelidir.

```markdown
# Task Raporu: <Task Adı>

## 1. Özet

## 2. Tamamlanan Maddeler

- [x] ...
- [x] ...

## 3. Değiştirilen / Eklenen Dosyalar

| Dosya | Değişiklik |
|---|---|
| `...` | ... |

## 4. Çalıştırılan Testler

```bash
komutlar
```

Sonuç:

```text
çıktı özeti
```

## 5. Manuel Doğrulama

- UI ekranı açıldı mı?
- Mock telemetry geldi mi?
- Hata durumları gösterildi mi?
- Güvenlik varsayılanları korundu mu?

## 6. Bilinen Eksikler

## 7. Riskler / Uyarılar

## 8. Bir Sonraki Önerilen Task

## 9. Kullanıcı Onayı

Bu task tamamlandı. Bir sonraki ana taska geçmem için `devam` yazmanı bekliyorum.
```
