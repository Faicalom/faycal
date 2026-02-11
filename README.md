# Real-ESRGAN Tkinter GUI (Python 3.8 / Windows)

واجهة بسيطة بـ **Tkinter** لتشغيل `realesrgan-ncnn-vulkan.exe` على صورة واحدة أو على كل الصور داخل مجلد (Batch).

## هيكلة المشروع

```text
faycal/
├─ app.py
├─ README.md
└─ requirements.txt
```

## المتطلبات

- Windows + Python 3.8
- ملف Real-ESRGAN التنفيذي:
  - `D:\Real-ESRGAN-master\realesrgan-ncnn-vulkan.exe`
- (اختياري) مجلد الموديلات:
  - `D:\Real-ESRGAN-master\models`

> الواجهة تحتوي قيماً افتراضية مطابقة لمساراتك ويمكن تعديلها من الواجهة.

## التثبيت والتشغيل

1. افتح CMD أو PowerShell داخل مجلد المشروع.
2. (اختياري) أنشئ بيئة افتراضية.
3. شغّل البرنامج:

```bash
python app.py
```

## الميزات المنفذة

1. **GUI بـ Tkinter**
   - اختيار ملف exe
   - اختيار مجلد models
   - اختيار Input كصورة واحدة أو مجلد
   - اختيار Output folder
   - زر Start وزر Stop

2. **Batch processing**
   - عند اختيار مجلد Input يتم معالجة كل الصور المدعومة داخله.

3. **اختيار الموديل**
   - `realesrgan-x4plus`
   - `realesrgan-x4plus-anime`

4. **Scale (2x / 4x / Auto)**
   - البرنامج يفحص هل `-s` مدعوم في نسخة exe عبر `-h`.
   - إذا غير مدعوم، يرجع تلقائياً للوضع الافتراضي للموديل.

5. **Progress + Log داخل الواجهة + log.txt**
   - شريط تقدم ونص حالة.
   - سجل مباشر داخل الواجهة.
   - إنشاء/تحديث `log.txt` داخل مجلد النتائج.

6. **الحفاظ على الامتداد**
   - PNG يبقى PNG، JPG يبقى JPG ... إلخ.
   - اسم الملف الناتج يكون بالشكل: `originalname_upscaled.ext`.

7. **التحقق من المسارات وإنشاء المجلدات**
   - التحقق من exe و input.
   - إنشاء output تلقائياً إذا غير موجود.

## الامتدادات المدعومة

- `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tif`, `.tiff`

## ملاحظات

- إذا كان مجلد `models` غير موجود، سيتم التشغيل بدون `-m` مع تسجيل تنبيه في الـ Log.
- زر **Stop** يوقف المعالجة بين الملفات (بعد إنهاء الملف الجاري معالجته حالياً).
