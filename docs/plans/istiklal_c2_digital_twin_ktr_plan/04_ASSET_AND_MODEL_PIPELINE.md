# 04 — Asset ve Model Pipeline: STEP / 3MF / .model -> GLB

## Amaç

Digital twin arayüzünün çalışması için üretim CAD dosyaları ve yarışma hedef modelleri web uyumlu, optimize edilmiş, node isimleri belli GLB/glTF varlıklarına dönüştürülmelidir.

## Neden GLB/glTF?

Web tabanlı 3D renderer’larda GLB/glTF daha uygun bir runtime formattır. STEP ve 3MF üretim/CAD/print odaklıdır; browser içinde doğrudan kullanılmaları performans ve loader karmaşıklığı doğurur.

## Kaynak varlıklar

### Cihaz CAD modeli

Mevcut sistem modelinden şunlar ayrılmalı:

| Node adı | Açıklama | Animasyon |
|---|---|---|
| `base_static` | Sabit taban | yok |
| `yaw_root` | X/pan dönen platform | pan_deg |
| `pitch_root` | Y/tilt dönen üst mekanizma | tilt_deg |
| `camera_mount` | Kamera gövdesi | pitch ile birlikte |
| `launcher_visual` | Namlu/atış yönü görsel referansı | pitch ile birlikte |
| `trigger_visual` | Servo/tetik görsel parçası | servo_angle |
| `safety_zone` | Opsiyonel güvenlik/limit hacmi | görünür/gizli |

### Yarışma hedef modelleri

Kullanıcı tarafından verilen dosyalar:

```json
[
  {
    "uploaded_name": "object_18.model",
    "path": "/mnt/data/object_18.model",
    "size_bytes": 1593671,
    "detected_format": "3MF XML model (.model extension)",
    "sha256": "5a87deb8025dc0124e24c73937edb1b261087bf78846574288d07ceef4730a08",
    "role": "competition_target_class_asset_candidate_unlabeled"
  },
  {
    "uploaded_name": "object_19.model",
    "path": "/mnt/data/object_19.model",
    "size_bytes": 50215966,
    "detected_format": "3MF XML model (.model extension)",
    "sha256": "fc1567c61bfdd49f5900f07abf327f9f45276a63dcffacd375627e9d98ea802e",
    "role": "competition_target_class_asset_candidate_unlabeled"
  },
  {
    "uploaded_name": "object_20.model",
    "path": "/mnt/data/object_20.model",
    "size_bytes": 57120249,
    "detected_format": "3MF XML model (.model extension)",
    "sha256": "20d7e7ac343e448a95db32cb886f460584539cb789860aa60986c0dc599dc9bf",
    "role": "competition_target_class_asset_candidate_unlabeled"
  },
  {
    "uploaded_name": "object_21.model",
    "path": "/mnt/data/object_21.model",
    "size_bytes": 58943183,
    "detected_format": "3MF XML model (.model extension)",
    "sha256": "2ddfac214687971b236b516aa99850970d3dce2613c0ea1c734be807e8e45f0b",
    "role": "competition_target_class_asset_candidate_unlabeled"
  }
]
```

Bu dosyalar `.model` uzantılıdır ve ilk tespit 3MF XML model formatı oldukları yönündedir. Sınıf etiketleri şu an bilinmiyor; bu yüzden agent sınıf isimlerini uydurmamalı.

Placeholder mapping:

| Dosya | Geçici ID | Not |
|---|---|---|
| object_18.model | class_01_candidate | etiket bekliyor |
| object_19.model | class_02_candidate | etiket bekliyor |
| object_20.model | class_03_candidate | etiket bekliyor |
| object_21.model | class_04_candidate | etiket bekliyor |

## Conversion pipeline

Önerilen güvenli pipeline:

1. `.model` / 3MF dosyasını Blender veya FreeCAD ile aç.
2. Gereksiz mesh detaylarını azalt.
3. Ölçek birimini milimetre/metre uyumlu hale getir.
4. Origin noktasını model merkezine al.
5. Ön yönü ve yukarı ekseni normalize et.
6. Materyal sayısını düşür.
7. GLB olarak export et.
8. Frontend public klasörüne koy.
9. Asset registry’de model path, scale, rotation offset ve label bilgisini tut.

Önerilen output:

```text
frontend/public/models/targets/
  class_01.glb
  class_02.glb
  class_03.glb
  class_04.glb
  balloon_fallback.glb
  unknown_target.glb
```

## Asset registry contract

```ts
export type TargetAsset = {
  classId: string;
  label: string;
  modelPath: string;
  sourceFile?: string;
  sourceSha256?: string;
  scale: number;
  rotationOffsetDeg: [number, number, number];
  positionOffset: [number, number, number];
  confidenceMin?: number;
  status: "ready" | "placeholder" | "missing" | "unlabeled";
};
```

Örnek:

```ts
export const targetAssetRegistry: TargetAsset[] = [
  {
    classId: "balloon",
    label: "Balloon test target",
    modelPath: "/models/targets/balloon_fallback.glb",
    scale: 1,
    rotationOffsetDeg: [0, 0, 0],
    positionOffset: [0, 0, 0],
    status: "ready"
  },
  {
    classId: "class_01",
    label: "Competition class 01 - label pending",
    modelPath: "/models/targets/class_01.glb",
    sourceFile: "object_18.model",
    status: "unlabeled",
    scale: 1,
    rotationOffsetDeg: [0, 0, 0],
    positionOffset: [0, 0, 0]
  }
];
```

## Model optimizasyon kuralları

- High-poly CAD model doğrudan UI’ya konmamalı.
- Görsel kalite güzel ama düşük polygon olmalı.
- Tek materyal veya az materyal tercih edilmeli.
- Texture boyutları düşük tutulmalı.
- Model lazy-loaded olmalı.
- GLB boyutları mümkünse:
  - cihaz modeli < 10-20 MB
  - hedef modelleri < 1-5 MB
- Asset missing durumunda UI çökmemeli.

## KTR’ye yazılacak değer

Bu pipeline, KTR’de şu iddiayı destekler:

> Üretimde kullanılan CAD verisi yalnızca imalat için değil, gerçek zamanlı operatör arayüzündeki dijital ikiz için de kullanılmıştır. Böylece mekanik tasarım, yazılım arayüzü ve test kanıtları aynı referans model etrafında birleştirilmiştir.

## Agent görevleri

- Model dosyalarının gerçek formatını doğrula.
- Sınıf etiketlerini uydurma.
- GLB conversion için script veya manuel adım raporu hazırla.
- Asset registry oluştur.
- Model yoksa placeholder ile devam et.
- KTR export’a asset inventory ekle.
