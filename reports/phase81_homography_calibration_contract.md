# P1 — Gerçek homography kalibrasyon sözleşmesi

Tarih: 2026-07-15. Kapsam: OPS-04 kamera düzlemi/nişan kalibrasyonunun identity placeholder yerine gerçek proje dönüşümü üretmesi.

## Davranış

`CalibrationPoint(world_x_m, world_y_m, image_x_px, image_y_px) → cv2.findHomography(RANSAC) → world_plane_to_image_px matrix`

- En az dört benzersiz, eş düzlemde olmayan (kollinear olmayan) nokta gerekir.
- Gerçek RANSAC inlier sayısı ve RMS reprojection error hesaplanır.
- RMS `3 px` üstündeyse veya inlier sayısı dört altındaysa çözüm geçersizdir; matrix/hash yayınlanmaz.
- Nokta veya config değiştiğinde önceki matrix, hata, inlier sayısı ve hash hemen geçersiz kılınır.
- Matrix, config ve noktalar kanonik JSON ile hash'lenir. Bu, saha run kaydına bağlanacak kalibrasyon kimliğidir.

## Otomatik kanıt

`backend/tests/test_phase81_homography_calibration_contract.py`:

1. Identity olmayan dört noktalı trapezden gerçek matrix, dört inlier, düşük reprojection error ve hash üretildiğini;
2. Kollinear noktaların `homography_degenerate_points` ile fail-closed kaldığını ve önceki çözümün taşınmadığını

doğrular.

Gerçek kamera/namlu paralaks ve 5/10/15 m saha residualı HIL-13 uygulanmadan henüz kanıtlanmış değildir.
