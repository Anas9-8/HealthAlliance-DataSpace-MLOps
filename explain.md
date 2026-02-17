# 📋 الشرح الكامل للمشروع — HealthAlliance DataSpace MLOps
### شرح كل مجلد وكل ملف وكل سطر من الكود بأبسط طريقة ممكنة

---

## 🧠 ما هو هذا المشروع بكلمة واحدة؟

هذا المشروع هو **نظام ذكاء اصطناعي طبي** يعمل على السحابة (AWS). يأخذ بيانات مريض ويحسب **احتمالية عودته للمستشفى** خلال 30 يوم. يربط ثلاث مؤسسات بحثية ألمانية: DKFZ و UKHD و EMBL.

---
---

# 📁 الملفات في الجذر (أعلى المشروع مباشرة)

---

## 📄 ملف `Dockerfile`

**ما هو؟** وصفة لبناء "صندوق" (Container) يحتوي على تطبيقنا جاهزاً للتشغيل في أي مكان.

**تخيّل:** مثل وصفة طبخ — تقول للحاسوب "خذ هذا، أضف ذاك، وفي النهاية ستحصل على تطبيق جاهز."

### شرح كل سطر:

```dockerfile
FROM python:3.10-slim
```
↑ ابدأ من صورة Python 3.10 الصغيرة كأساس (مثل "خذ وعاء فارغاً")

```dockerfile
LABEL maintainer="anas@healthalliance.dev"
LABEL description="HealthAlliance DataSpace MLOps Platform - Production API"
```
↑ معلومات عن الصورة — من صنعها وماذا تفعل (مثل لصقة على العلبة)

```dockerfile
WORKDIR /app
```
↑ حدّد مجلد العمل داخل الصندوق ليكون `/app` (مثل "اعمل داخل هذا المجلد")

```dockerfile
RUN apt-get update && apt-get install -y gcc g++ libpq-dev curl && rm -rf /var/lib/apt/lists/*
```
↑ قم بتحميل برامج مساعدة ضرورية:
- `gcc` و `g++` → مترجمان للكود
- `libpq-dev` → للتواصل مع قاعدة بيانات PostgreSQL
- `curl` → لإرسال طلبات HTTP (للفحص الصحي لاحقاً)
- `rm -rf /var/lib/apt/lists/*` → احذف ملفات التحميل المؤقتة لتقليل الحجم

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt
```
↑ انسخ قائمة المكتبات ثم قم بتثبيتها جميعاً

```dockerfile
COPY . .
```
↑ انسخ كامل كود المشروع داخل الصندوق

```dockerfile
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
```
↑ **أمان:** أنشئ مستخدماً عادياً اسمه `appuser` وشغّل التطبيق بدلاً من المستخدم الجذر (root). هذا ممارسة أمنية مهمة — إذا اخترق أحد التطبيق لن يحصل على صلاحيات كاملة.

```dockerfile
EXPOSE 8000
```
↑ أخبر الخارج أن التطبيق يستمع على المنفذ 8000

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```
↑ كل 30 ثانية، تحقق أن التطبيق يعمل عن طريق إرسال طلب إلى `/health`. إذا فشل 3 مرات متتالية — أعلن أن الحاوية "مريضة"

```dockerfile
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```
↑ عند تشغيل الصندوق، شغّل الـ API بـ 4 عمال متوازيين على المنفذ 8000

---

## 📄 ملف `docker-compose.yml`

**ما هو؟** يشغّل **5 خدمات دفعة واحدة** بأمر واحد: `docker compose up -d`

**تخيّل:** مثل مدير مطعم يقول: "أشعل الموقد، افتح الثلاجة، شغّل الكاشير، افتح الباب" — كل شيء دفعة واحدة.

### شرح كل خدمة:

**خدمة 1 — قاعدة البيانات `postgres`:**
```yaml
image: postgres:15-alpine       # استخدم PostgreSQL الإصدار 15
container_name: healthalliance-postgres
environment:
  POSTGRES_USER: healthalliance               # اسم المستخدم
  POSTGRES_PASSWORD: healthalliance_password_change_in_production  # كلمة المرور
  POSTGRES_DB: healthalliance_db             # اسم قاعدة البيانات
ports:
  - "5432:5432"                 # المنفذ الخارجي:الداخلي
volumes:
  - postgres_data:/var/lib/postgresql/data   # احفظ البيانات حتى بعد إيقاف الخدمة
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U healthalliance"]  # تحقق أن القاعدة تعمل
```

**خدمة 2 — تتبع النماذج `mlflow`:**
```yaml
command: bash -c "pip install mlflow==2.8.0 ... && mlflow server --host 0.0.0.0 --port 5000 ..."
ports:
  - "5000:5000"
depends_on:
  postgres:
    condition: service_healthy   # لا تبدأ إلا بعد أن تكون قاعدة البيانات جاهزة
```
↑ MLflow هو نظام يحفظ كل تجربة تدريب (النتائج، المعايير، النموذج) حتى تستطيع المقارنة بينها لاحقاً

**خدمة 3 — الـ API الرئيسي `api`:**
```yaml
build:
  context: .
  dockerfile: Dockerfile        # ابنِ الصورة من Dockerfile الموجود
ports:
  - "8000:8000"
volumes:
  - ./src:/app/src              # اربط مجلد src المحلي بداخل الحاوية (تحديثات فورية)
environment:
  - DATABASE_URL=postgresql://...@postgres:5432/healthalliance_db
  - MLFLOW_TRACKING_URI=http://mlflow:5000
command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```
↑ `--reload` يعني أن التطبيق يُعيد تشغيل نفسه تلقائياً عند تعديل الكود أثناء التطوير

**خدمة 4 — جمع المقاييس `prometheus`:**
```yaml
image: prom/prometheus:v2.47.0
ports:
  - "9090:9090"
volumes:
  - ./k8s/prometheus.yml:/etc/prometheus/prometheus.yml  # استخدم إعداداتنا
```
↑ Prometheus يجمع أرقام عن الأداء كل 15 ثانية ويحفظها (كم طلب وصل؟ كم ثانية أخذ الرد؟)

**خدمة 5 — لوحة المراقبة `grafana`:**
```yaml
image: grafana/grafana:10.1.5
ports:
  - "3000:3000"
environment:
  - GF_SECURITY_ADMIN_PASSWORD=admin_change_in_production
  - GF_USERS_ALLOW_SIGN_UP=false   # لا تسمح بالتسجيل العشوائي
```
↑ Grafana يحوّل أرقام Prometheus إلى رسوم بيانية جميلة على صفحة ويب

---

## 📄 ملف `requirements.txt`

**ما هو؟** قائمة بكل مكتبات Python المطلوبة مع أرقام إصداراتها الدقيقة.

**أهم المكتبات:**
| المكتبة | الاستخدام |
|---|---|
| `fastapi` | إطار عمل الـ API |
| `uvicorn` | خادم HTTP يشغّل الـ API |
| `scikit-learn` | خوارزميات التعلم الآلي |
| `mlflow` | تتبع تجارب التدريب |
| `dvc` | تتبع إصدارات البيانات والنماذج |
| `prometheus-client` | إرسال مقاييس لـ Prometheus |
| `pydantic` | التحقق من صحة البيانات المدخلة |
| `sqlalchemy` | التواصل مع قاعدة البيانات |
| `boto3` | التواصل مع خدمات AWS |
| `pytest` | تشغيل الاختبارات |
| `black` | تنسيق الكود تلقائياً |

---

## 📄 ملف `.env.example`

**ما هو؟** نموذج لملف الإعدادات السرية. يجب نسخه إلى `.env` وملء القيم الحقيقية.

**لماذا لا نضع القيم الحقيقية مباشرة؟** لأن `.env` مُدرج في `.gitignore` ولا يُرفع إلى GitHub. هكذا تظل كلمات المرور والمفاتيح سرية.

```bash
# بيانات الدخول لـ AWS
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=eu-central-1           # المنطقة: وسط أوروبا (فرانكفورت)

# رابط تخزين DVC على S3
DVC_REMOTE_URL=s3://healthalliance-dvc-storage

# رابط خادم MLflow
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=health-risk-prediction   # اسم تجربة التدريب

# مفتاح تشفير الـ API (JWT)
API_SECRET_KEY=generate_secure_key_here
API_ALGORITHM=HS256                       # خوارزمية التشفير
API_ACCESS_TOKEN_EXPIRE_MINUTES=30        # صلاحية التوكن 30 دقيقة

# قاعدة البيانات
POSTGRES_USER=healthalliance
POSTGRES_PASSWORD=change_this_password
POSTGRES_DB=healthalliance_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# مفاتيح API للمؤسسات الشريكة
DKFZ_API_KEY=dkfz_key_here
UKHD_API_KEY=ukhd_key_here
EMBL_API_KEY=embl_key_here
```

---
---

# 📁 مجلد `src/` — الكود الأساسي

---

## 📄 `src/api/main.py` — القلب النابض للمشروع

**ما هو؟** الـ API الرئيسي. يستقبل طلبات HTTP ويرد عليها. مبني بـ FastAPI.

**تخيّل:** مثل موظف استقبال في المستشفى — يستقبل الطلبات، يعالجها، ويرد.

### شرح كل قسم:

**القسم 1 — الاستيراد والإعداد:**
```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
```
↑ استيراد المكتبات المطلوبة:
- `FastAPI` → إطار بناء الـ API
- `CORSMiddleware` → للسماح لمتصفحات الويب بالوصول للـ API
- `BaseModel` → لتعريف شكل البيانات المقبولة والمرسلة
- `List` → نوع بيانات "قائمة"

```python
app = FastAPI(
    title="HealthAlliance DataSpace API",
    description="MLOps Platform for Healthcare Data Sharing - DKFZ, UKHD, EMBL",
    version="1.0.0",
    docs_url="/docs",         # رابط صفحة التوثيق التفاعلية
    redoc_url="/redoc"        # رابط صفحة التوثيق البديلة
)
```
↑ إنشاء تطبيق FastAPI بمعلوماته الأساسية

```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```
↑ اسمح لأي موقع ويب بالتواصل مع الـ API (مهم للتطوير)

**القسم 2 — نماذج البيانات (Pydantic Models):**
```python
class PatientRiskRequest(BaseModel):
    patient_id: str           # رقم هوية المريض (نص)
    age: int                  # العمر (رقم صحيح)
    gender: str               # الجنس (نص)
    conditions: List[str]     # قائمة الأمراض المزمنة
    medications: List[str]    # قائمة الأدوية
    recent_encounters: int    # عدد الزيارات الأخيرة
```
↑ هذا "العقد" — يحدد بالضبط ما يجب أن يرسله المستخدم. إذا أرسل بيانات ناقصة أو خاطئة يرد الـ API بخطأ 422 تلقائياً.

```python
class PatientRiskResponse(BaseModel):
    patient_id: str
    readmission_risk: float   # رقم من 0 إلى 1 (الاحتمالية)
    risk_level: str           # LOW أو MEDIUM أو HIGH
    confidence: float         # مستوى ثقة النموذج
    recommendations: List[str] # قائمة التوصيات
```
↑ هذا شكل الرد الذي سيستلمه المستخدم

**القسم 3 — نقاط النهاية (Endpoints):**

```python
@app.get("/")
async def root():
    return {"message": "HealthAlliance DataSpace MLOps Platform", ...}
```
↑ عند زيارة الرابط الرئيسي — أعد معلومات عامة عن الخدمة

```python
@app.get("/health", response_model=HealthCheck)
async def health_check():
    return {"status": "healthy", "version": "1.0.0",
            "services": {"api": "running", "database": "connected", "mlflow": "available"}}
```
↑ نقطة فحص صحة النظام — تستخدمها Kubernetes كل 10 ثواني للتأكد أن التطبيق يعمل

```python
@app.post("/api/v1/predict", response_model=PatientRiskResponse)
async def predict_readmission_risk(request: PatientRiskRequest):
    risk_score = 0.0

    if request.age > 65:              # إذا عمر المريض فوق 65: أضف 0.3 للخطر
        risk_score += 0.3
    if request.recent_encounters > 3: # إذا زار المستشفى أكثر من 3 مرات: أضف 0.2
        risk_score += 0.2
    if len(request.conditions) > 2:   # إذا لديه أكثر من مرضين: أضف 0.25
        risk_score += 0.25
    if len(request.medications) > 5:  # إذا يأخذ أكثر من 5 أدوية: أضف 0.15
        risk_score += 0.15

    risk_score = min(risk_score, 1.0) # لا تتجاوز 1.0 (100%)

    if risk_score < 0.3:
        risk_level = "LOW"
        recommendations = ["Regular follow-up in 3 months"]
    elif risk_score < 0.6:
        risk_level = "MEDIUM"
        recommendations = ["Schedule follow-up in 2 weeks", "Monitor medication adherence"]
    else:
        risk_level = "HIGH"
        recommendations = ["Immediate follow-up within 48 hours", ...]
```
↑ الدالة الأهم — تحسب درجة الخطر بناءً على 4 عوامل وتعيد مستوى الخطر والتوصيات

```python
@app.get("/api/v1/institutions")
async def list_institutions():
    return {"institutions": [
        {"id": "dkfz", "name": "German Cancer Research Center", "patient_count": 500},
        {"id": "ukhd", "name": "University Hospital Heidelberg", "patient_count": 700},
        {"id": "embl", "name": "European Molecular Biology Laboratory", "patient_count": 300}
    ]}
```
↑ يعيد قائمة المؤسسات الشريكة وعدد مرضاها

---

## 📄 `src/data/__init__.py` — معالجة البيانات

**ما هو؟** مكتبة Python لتحميل بيانات FHIR ومعالجتها وتحويلها لشكل يفهمه النموذج.

```python
def load_patient_data(filepath: str) -> pd.DataFrame:
    return pd.read_csv(filepath)
```
↑ بسيطة: اقرأ ملف CSV وأعده كجدول DataFrame

```python
def preprocess_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "gender" in df.columns:
        df["gender_encoded"] = (df["gender"].str.lower() == "male").astype(int)
    # ↑ حوّل "male"/"female" إلى 1/0 لأن النموذج لا يفهم النصوص

    feature_cols = ["age", "num_conditions", "num_medications", "recent_encounters", "gender_encoded"]
    available_cols = [c for c in feature_cols if c in df.columns]
    return df[available_cols].fillna(0)
    # ↑ خذ فقط الأعمدة المطلوبة وامْلأ القيم المفقودة بـ 0
```
↑ تحويل البيانات الخام إلى ميزات جاهزة للنموذج

```python
def validate_fhir_record(record: Dict) -> bool:
    required_fields = ["resourceType", "id", "gender", "birthDate"]
    return all(field in record for field in required_fields)
```
↑ تحقق أن سجل FHIR يحتوي على الحقول الأساسية قبل معالجته

```python
def parse_institution_data(institution_id: str, records: List[Dict]) -> pd.DataFrame:
    rows = []
    for record in records:
        if not validate_fhir_record(record):
            continue  # تجاهل السجلات الغير صالحة
        rows.append({"patient_id": record.get("id"), "institution": institution_id, ...})
    return pd.DataFrame(rows)
```
↑ تحويل قائمة سجلات FHIR من مؤسسة معينة إلى جدول موحد

---

## 📄 `src/models/__init__.py` — نموذج التعلم الآلي

**ما هو؟** كود تدريب النموذج والتنبؤ به.

```python
FEATURE_COLUMNS = ["age", "num_conditions", "num_medications", "recent_encounters", "gender_encoded"]
```
↑ الميزات التي يستخدمها النموذج (5 ميزات)

```python
def train_model(df, target_col="readmitted"):
    X = df[available_features]      # المدخلات (الميزات)
    y = df[target_col]              # الهدف (هل أُعيد المريض؟ 1=نعم 0=لا)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    # ↑ قسّم البيانات: 80% للتدريب، 20% للاختبار. stratify=y يضمن توزيعاً متوازناً

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)  # حوّل الأرقام لمقياس موحد
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(n_estimators=100, max_depth=10, class_weight="balanced")
    # ↑ نموذج "غابة عشوائية": 100 شجرة قرار، عمق أقصاه 10، متوازن للبيانات غير المتوازنة
    model.fit(X_train_scaled, y_train)

    metrics = {"roc_auc": roc_auc_score(y_test, y_prob), ...}
    # ↑ ROC-AUC: مقياس جودة النموذج (1.0 = مثالي، 0.5 = عشوائي)

    return model, scaler, metrics
```

```python
def predict_risk(model, scaler, features):
    row = [features.get(col, 0) for col in FEATURE_COLUMNS]  # استخرج الميزات بالترتيب
    X = np.array(row).reshape(1, -1)   # حوّل لمصفوفة بصف واحد
    X_scaled = scaler.transform(X)     # طبّق نفس التحجيم
    return float(model.predict_proba(X_scaled)[0][1])  # أعد احتمالية الفئة 1 (إعادة الدخول)
```

```python
def save_model(model, scaler, path):
    with open(path, "wb") as f:
        pickle.dump({"model": model, "scaler": scaler}, f)  # احفظ النموذج والمحجّم معاً
```

---

## 📄 `src/monitoring/__init__.py` — المراقبة

**ما هو؟** يعرّف المقاييس التي تُجمع وتُرسل لـ Prometheus.

```python
REQUEST_COUNT = Counter(
    "http_requests_total",          # اسم المقياس في Prometheus
    "Total number of HTTP requests",
    ["method", "endpoint", "status"] # تصنّف حسب: الطريقة، المسار، حالة الاستجابة
)
```
↑ عداد: يزيد فقط، لا ينقص. يحسب إجمالي الطلبات.

```python
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]  # "دلاء" زمنية
)
```
↑ Histogram: يوزّع القيم في "دلاء". مثلاً: كم طلباً أخذ أقل من 0.1 ثانية؟

```python
PREDICTION_COUNT = Counter("predictions_total", ..., ["status", "risk_level"])
PREDICTION_DURATION = Histogram("prediction_duration_seconds", ...)
MODEL_CONFIDENCE = Histogram("model_confidence_score", ...)
```
↑ مقاييس خاصة بالنموذج: عدد التنبؤات، مدة كل تنبؤ، توزيع درجات الثقة

```python
def record_prediction(risk_level, duration, confidence, success=True):
    PREDICTION_COUNT.labels(status="success", risk_level=risk_level).inc()
    PREDICTION_DURATION.observe(duration)
    MODEL_CONFIDENCE.observe(confidence)
```
↑ دالة مساعدة تُسجّل مقاييس تنبؤ واحد بسطر واحد

---

## 📄 `src/pipelines/__init__.py` — خط أنابيب التدريب

**ما هو؟** يشغّل كامل عملية التدريب من البداية للنهاية ويسجّل كل شيء في MLflow.

```python
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
```
↑ رابط MLflow من متغيرات البيئة، أو القيمة الافتراضية إذا لم يوجد

```python
def run_training_pipeline(data_path: str) -> str:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT)

    with mlflow.start_run(run_name=run_name) as run:
        # الخطوة 1: تحميل البيانات
        df = load_patient_data(data_path)

        # الخطوة 2: معالجة الميزات
        features_df = preprocess_features(df)
        features_df["readmitted"] = df["readmitted"]

        # الخطوة 3: تدريب النموذج
        model, scaler, metrics = train_model(features_df)

        # الخطوة 4: تسجيل في MLflow
        mlflow.log_param("n_samples", len(df))        # عدد العينات
        mlflow.log_metric("roc_auc", metrics["roc_auc"])  # جودة النموذج
        mlflow.sklearn.log_model(model, artifact_path="model")  # حفظ النموذج

        return run.info.run_id  # أعد معرّف التجربة
```
↑ كل تشغيل لهذه الدالة يُنشئ "تجربة" في MLflow مع كل التفاصيل

---
---

# 📁 مجلد `tests/` — الاختبارات

---

## 📄 `tests/test_api.py`

**ما هو؟** اختبارات تلقائية تتأكد أن الـ API يعمل بشكل صحيح.

```python
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)  # عميل اختبار لا يحتاج خادماً حقيقياً
```

```python
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200  # تأكد أن الرد 200 (نجاح)
```

```python
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"  # تأكد أن الحالة "healthy"
    assert "version" in data            # تأكد أن الإصدار موجود في الرد
```

```python
def test_predict_endpoint_valid():
    payload = {
        "patient_id": "TEST001",
        "age": 65,
        "gender": "male",
        "recent_encounters": 3,
        "conditions": ["diabetes", "hypertension"],
        "medications": ["metformin", "lisinopril"]
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "readmission_risk" in data   # تأكد أن الخطر موجود في الرد
    assert "risk_level" in data         # تأكد أن مستوى الخطر موجود
    assert data["patient_id"] == "TEST001"
```

```python
def test_predict_endpoint_invalid():
    payload = {"age": 65}  # بيانات ناقصة (لا patient_id ولا gender...)
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 422  # 422 = خطأ في التحقق من البيانات
```
↑ هذا الاختبار يتأكد أن الـ API يرفض البيانات الخاطئة

```python
def test_institutions_endpoint():
    response = client.get("/api/v1/institutions")
    assert response.status_code == 200
    data = response.json()
    assert len(data["institutions"]) == 3  # يجب أن يكون 3 مؤسسات بالضبط
```

---
---

# 📁 مجلد `.github/workflows/` — الأتمتة

---

## 📄 `ci-cd.yaml` — خط أنابيب CI/CD

**ما هو؟** عند رفع كود جديد على GitHub، هذا الملف يُشغَّل تلقائياً ويمر بـ 3 مراحل.

```yaml
on:
  push:
    branches: [ main, develop ]   # شغّل عند الرفع على main أو develop
  pull_request:
    branches: [ main ]            # أو عند فتح Pull Request على main
```

**المرحلة 1 — الاختبار `test`:**
```yaml
- name: Run tests
  run: pytest tests/ -v --cov=src --cov-report=xml
```
↑ شغّل الاختبارات مع قياس نسبة تغطية الكود (Coverage) ورفع النتيجة لـ Codecov

**المرحلة 2 — البناء `build` (فقط على main):**
```yaml
needs: test  # لا تبدأ إلا بعد نجاح الاختبارات
if: github.ref == 'refs/heads/main'  # فقط على فرع main

- name: Build, tag, and push image to Amazon ECR
  run: |
    docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
    docker tag ... :latest
    docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
    docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
```
↑ ابنِ صورة Docker وارفعها إلى ECR (سجل صور AWS) بوسمين:
- رقم commit الحالي (لإمكانية الرجوع لإصدار محدد)
- `latest` (آخر إصدار)

**المرحلة 3 — النشر `deploy` (فقط على main):**
```yaml
needs: build  # لا تبدأ إلا بعد نجاح البناء

- name: Deploy to Kubernetes
  run: |
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/secrets-template.yaml
    kubectl apply -f k8s/postgres-pvc.yaml
    kubectl apply -f k8s/database-deployment.yaml
    kubectl apply -f k8s/database-service.yaml
    kubectl apply -f k8s/api-deployment.yaml
    kubectl apply -f k8s/api-service.yaml
    kubectl apply -f k8s/api-hpa.yaml

    kubectl rollout status deployment/healthalliance-api  # تحقق من نجاح النشر
```
↑ طبّق كل ملفات Kubernetes على الكلستر بالترتيب الصحيح

---

## 📄 `code-quality.yaml` — جودة الكود

```yaml
- name: Run Black
  run: black --check src/ tests/   # هل الكود منسّق؟
  continue-on-error: true          # لا توقف إذا فشل (تحذير فقط)

- name: Run Flake8
  run: flake8 src/ tests/ --max-line-length=100  # هل يوجد أخطاء أسلوب؟

- name: Run MyPy
  run: mypy src/ --ignore-missing-imports  # هل أنواع البيانات صحيحة؟
```

---
---

# 📁 مجلد `k8s/` — Kubernetes

**Kubernetes = نظام لإدارة وتشغيل التطبيقات على السحابة بشكل موثوق وقابل للتوسع**

---

## 📄 `k8s/configmap.yaml` — الإعدادات العامة

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: healthalliance-config
data:
  mlflow-uri: "http://healthalliance-mlflow-service:5000"  # رابط MLflow داخل الكلستر
  api-workers: "4"           # عدد العمال في الـ API
  log-level: "info"          # مستوى السجلات
  environment: "production"  # البيئة: إنتاج
  aws-region: "eu-central-1" # المنطقة
```
↑ ConfigMap = إعدادات عامة غير سرية يمكن لأي Pod قراءتها

---

## 📄 `k8s/secrets-template.yaml` — الإعدادات السرية

```yaml
kind: Secret
stringData:
  postgres-user: "healthalliance"
  postgres-password: "CHANGE_ME_IN_PRODUCTION"   # ← يجب تغييرها قبل النشر!
  database-url: "postgresql://healthalliance:CHANGE_ME@...5432/healthalliance"
  aws-access-key-id: "CHANGE_ME"
  aws-secret-access-key: "CHANGE_ME"
```
↑ Secret = إعدادات سرية (كلمات مرور ومفاتيح) — Kubernetes يشفّرها ولا تظهر في السجلات

---

## 📄 `k8s/api-deployment.yaml` — نشر الـ API

```yaml
kind: Deployment
spec:
  replicas: 3    # شغّل 3 نسخ متوازية من الـ API

  containers:
  - name: api
    image: ACCOUNT_ID.dkr.ecr.eu-central-1.amazonaws.com/healthalliance-mlops-app:latest
    # ↑ الصورة من ECR (تُستبدل ACCOUNT_ID بالحساب الحقيقي أثناء النشر)

    resources:
      requests:
        memory: "256Mi"   # احجز 256 ميجابايت ذاكرة
        cpu: "250m"       # احجز ربع نواة معالج (250 ميلي-كور)
      limits:
        memory: "512Mi"   # لا تتجاوز 512 ميجابايت
        cpu: "500m"       # لا تتجاوز نصف نواة

    livenessProbe:
      httpGet:
        path: /health
        port: 8000
      initialDelaySeconds: 30   # انتظر 30 ثانية بعد البدء قبل الفحص
      periodSeconds: 10         # افحص كل 10 ثواني
    # ↑ Liveness: إذا فشل الفحص، أعد تشغيل الحاوية

    readinessProbe:
      httpGet:
        path: /health
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 5
    # ↑ Readiness: لا ترسل طلبات للحاوية حتى تجتاز هذا الفحص
```

---

## 📄 `k8s/api-hpa.yaml` — التوسع التلقائي

```yaml
kind: HorizontalPodAutoscaler
spec:
  minReplicas: 3    # الحد الأدنى: 3 نسخ دائماً
  maxReplicas: 10   # الحد الأقصى: 10 نسخ عند الضغط العالي

  metrics:
  - resource: cpu
    target:
      averageUtilization: 70   # إذا وصل CPU لـ 70% → أضف نسخة جديدة
  - resource: memory
    target:
      averageUtilization: 80   # إذا وصلت الذاكرة لـ 80% → أضف نسخة جديدة
```
↑ **مثال:** إذا جاء 1000 مستخدم دفعة واحدة، Kubernetes يزيد النسخ من 3 إلى 10 تلقائياً. عندما يقل الضغط، يعود لـ 3.

---

## باقي ملفات `k8s/`:

| الملف | المحتوى بإيجاز |
|---|---|
| `api-service.yaml` | يعرّض الـ API للإنترنت على المنافذ 80 و 443 |
| `database-deployment.yaml` | يشغّل PostgreSQL 15 مع حفظ البيانات على قرص دائم |
| `database-service.yaml` | يسمح للـ API بالوصول لقاعدة البيانات داخلياً على المنفذ 5432 |
| `postgres-pvc.yaml` | يحجز 10 جيجابايت على القرص لقاعدة البيانات |
| `monitoring-deployment.yaml` | يشغّل Prometheus و Grafana في مساحة `monitoring` |
| `prometheus.yml` | يخبر Prometheus: اجمع بيانات من API وPostgres وMLflow كل 15 ثانية |
| `servicemonitor.yaml` | يسمح لـ Prometheus Operator باكتشاف الخدمات تلقائياً |

---
---

# 📁 مجلد `monitoring/` — المراقبة

---

## 📄 `monitoring/prometheus-rules.yaml` — قواعد التنبيه

```yaml
groups:
  - name: healthalliance.api
    rules:
      - alert: APIDown
        expr: up{job="healthalliance-api"} == 0  # إذا كان الـ API غير متاح
        for: 2m                                   # لمدة دقيقتين متواصلتين
        labels:
          severity: critical                      # مستوى الخطورة: حرج
        annotations:
          summary: "HealthAlliance API is down"
```
↑ `expr` = معادلة PromQL (لغة استعلام Prometheus). إذا تحققت → أرسل تنبيهاً

```yaml
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        # ↑ إذا كان معدل الطلبات الفاشلة (5xx) خلال 5 دقائق أكثر من 5%
        for: 5m
        labels:
          severity: warning
```

**ملخص التنبيهات:**
| التنبيه | الشرط | الخطورة |
|---|---|---|
| APIDown | الـ API متوقف 2 دقيقة | حرج 🔴 |
| HighErrorRate | أخطاء > 5% | تحذير 🟡 |
| HighResponseTime | وقت الاستجابة p95 > 200ms | تحذير 🟡 |
| DatabaseDown | قاعدة البيانات متوقفة 1 دقيقة | حرج 🔴 |
| HighDatabaseConnections | اتصالات > 80 | تحذير 🟡 |
| HighCPUUsage | CPU > 80% لـ 10 دقائق | تحذير 🟡 |
| HighMemoryUsage | ذاكرة > 90% | تحذير 🟡 |
| HighPredictionLatency | وقت التنبؤ p95 > 2 ثانية | تحذير 🟡 |

---

## 📄 `monitoring/grafana-dashboard.json` — لوحة التحكم

ملف JSON يعرّف لوحة Grafana بـ 8 رسوم بيانية:
1. معدل طلبات الـ API
2. وقت الاستجابة (النسبة المئوية الـ 95)
3. استخدام CPU
4. استخدام الذاكرة
5. معدل نجاح التنبؤات
6. اتصالات قاعدة البيانات
7. عدد الـ Pods
8. معدل الأخطاء

---
---

# 📁 مجلد `infra/terraform/` — البنية التحتية

**Terraform = أداة لإنشاء موارد AWS بالكود بدلاً من الضغط على الأزرار يدوياً**

---

## 📄 `main.tf` — الإعداد الأساسي

```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"    # استخدم AWS provider الإصدار 5.x
    }
  }
}

provider "aws" {
  region = "eu-central-1"   # المنطقة: فرانكفورت (أقرب لهايدلبرغ)

  default_tags {
    tags = {
      Project     = "HealthAlliance-DataSpace-MLOps"
      ManagedBy   = "Terraform"   # كل مورد يُنشأ يحمل هذه التاغات تلقائياً
    }
  }
}

data "aws_availability_zones" "available" { state = "available" }
# ↑ اجلب قائمة المناطق الفرعية المتاحة في eu-central-1

data "aws_caller_identity" "current" {}
# ↑ اجلب رقم حساب AWS الحالي (نستخدمه في تسمية الموارد)
```

---

## 📄 `vpc.tf` — الشبكة الافتراضية

```hcl
resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr   # 10.0.0.0/16 = نطاق IP: من 10.0.0.0 حتى 10.0.255.255
  enable_dns_hostnames = true  # اسمح بأسماء DNS
  enable_dns_support   = true
}
```
↑ VPC = شبكة خاصة معزولة على AWS. كل موارد المشروع تعيش داخلها.

```hcl
resource "aws_subnet" "public" {
  count      = 2                                # أنشئ 2 شبكات فرعية عامة
  cidr_block = "10.0.${count.index}.0/24"      # 10.0.0.0/24 و 10.0.1.0/24
  map_public_ip_on_launch = true               # كل جهاز يحصل على IP عام
}

resource "aws_subnet" "private" {
  count      = 2                               # أنشئ 2 شبكات فرعية خاصة
  cidr_block = "10.0.${count.index + 10}.0/24" # 10.0.10.0/24 و 10.0.11.0/24
}
```
↑ **عامة** = يمكن الوصول لها من الإنترنت (للـ API). **خاصة** = معزولة (لقاعدة البيانات)

```hcl
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id   # بوابة الإنترنت — تربط VPC بالإنترنت
}

resource "aws_route_table" "public" {
  route {
    cidr_block = "0.0.0.0/0"              # أي IP خارجي
    gateway_id = aws_internet_gateway.main.id  # يمر عبر بوابة الإنترنت
  }
}
```

---

## 📄 `s3.tf` — التخزين

```hcl
resource "aws_s3_bucket" "data" {
  bucket = "${var.project_name}-healthcare-data-${data.aws_caller_identity.current.account_id}"
  # ↑ اسم فريد: healthalliance-mlops-healthcare-data-123456789012
  tags = { Compliance = "GDPR-HIPAA" }  # ملاحظة الامتثال
}

resource "aws_s3_bucket_versioning" "data" {
  versioning_configuration { status = "Enabled" }
  # ↑ احفظ كل نسخة من كل ملف — يمكن الرجوع لأي نسخة سابقة
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
  # ↑ تشفير كل الملفات المحفوظة بـ AES-256
}

resource "aws_s3_bucket_public_access_block" "data" {
  block_public_acls   = true    # منع الوصول العام — لا أحد يرى البيانات
  restrict_public_buckets = true
}
```
↑ **Bucket 1**: للبيانات الصحية (GDPR-HIPAA مشفّر ومحمي)
↑ **Bucket 2**: لنماذج MLflow (مشفّر، إصدارات ممكّنة)

---

## 📄 `ecr.tf` — سجل الصور

```hcl
resource "aws_ecr_repository" "app" {
  name = "${var.project_name}-app"   # اسم المستودع

  image_scanning_configuration {
    scan_on_push = true   # عند رفع صورة جديدة، افحصها للثغرات الأمنية تلقائياً
  }

  encryption_configuration { encryption_type = "AES256" }
}

resource "aws_ecr_lifecycle_policy" "app" {
  policy = jsonencode({
    rules = [{
      description = "Keep last 10 images"   # احتفظ فقط بآخر 10 صور، احذف القديمة
      selection = { countNumber = 10 }
    }]
  })
}
```
↑ ECR = Docker Registry على AWS. هنا نخزن صور الـ API.

---

## 📄 `iam.tf` — الأذونات

```hcl
resource "aws_iam_role" "eks_cluster" {
  name = "${var.project_name}-eks-cluster-role"

  assume_role_policy = jsonencode({
    Statement = [{
      Action    = "sts:AssumeRole"
      Principal = { Service = "eks.amazonaws.com" }
      # ↑ اسمح لخدمة EKS بأخذ هذا الدور
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
  # ↑ أعطِ الدور صلاحيات إدارة الكلستر
}
```
↑ **دور 1**: لكلستر EKS — يدير الكلستر
↑ **دور 2**: للـ Nodes — لكل جهاز في الكلستر (صلاحيات: تشغيل Pods، جلب صور ECR، إدارة الشبكة)

---

## 📄 `security.tf` — جدار الحماية

```hcl
resource "aws_security_group" "api" {
  ingress {
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]   # اسمح لأي IP بالوصول عبر HTTP
  }
  ingress {
    from_port   = 443
    cidr_blocks = ["0.0.0.0/0"]   # اسمح لأي IP بالوصول عبر HTTPS
  }
  ingress {
    from_port   = 8000
    cidr_blocks = ["0.0.0.0/0"]   # اسمح بالوصول المباشر للـ API
  }
  egress {
    cidr_blocks = ["0.0.0.0/0"]   # اسمح لكل الاتصالات الصادرة
  }
}

resource "aws_security_group" "database" {
  ingress {
    from_port       = 5432         # PostgreSQL
    security_groups = [aws_security_group.api.id]  # فقط من الـ API — لا أحد آخر!
  }
}
```
↑ **مجموعة الـ API**: مفتوحة للعالم على 80/443/8000
↑ **مجموعة قاعدة البيانات**: مغلقة تماماً إلا للـ API — حماية البيانات الطبية

---

## 📄 `variables.tf` — المتغيرات

```hcl
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-central-1"   # القيمة الافتراضية: فرانكفورت
}

variable "environment" {
  default = "dev"                 # بيئة التطوير
}

variable "project_name" {
  default = "healthalliance-mlops"  # اسم المشروع (يُستخدم في تسمية كل مورد)
}

variable "vpc_cidr" {
  default = "10.0.0.0/16"         # نطاق IP للشبكة الافتراضية
}
```

---

## 📄 `outputs.tf` — المخرجات

بعد تطبيق Terraform، هذه المعلومات تظهر في الطرفية:

```hcl
output "vpc_id"                  # معرّف الشبكة → نستخدمه في إعداد EKS
output "ecr_repository_url"     # رابط ECR → نستخدمه في Dockerfile و CI/CD
output "healthcare_data_bucket" # اسم Bucket البيانات → نستخدمه في DVC
output "mlflow_artifacts_bucket"# اسم Bucket النماذج → نستخدمه في MLflow
output "eks_cluster_role_arn"   # دور الكلستر → نستخدمه في إنشاء EKS
```

---
---

# 📁 مجلد `data/`

```
data/
├── raw/     ← البيانات الخام من المؤسسات (FHIR JSON) — محفوظة في S3 عبر DVC
└── README.md
```

**البيانات غير موجودة في Git** — لأنها كبيرة وسرية. بدلاً من ذلك يُستخدم DVC لتتبعها في S3.
لجلب البيانات: `dvc pull`

---

# 📁 مجلد `models/`

```
models/
└── README.md
```

النماذج المدربة تُحفظ هنا أثناء التشغيل (بصيغة `.pkl`). كذلك غير موجودة في Git — تُتبع بـ DVC أو MLflow.

---
---

# 🗺️ كيف يتدفق العمل؟ (من البداية للنهاية)

```
1. المطوّر يكتب كوداً ويرفعه على GitHub
        ↓
2. GitHub Actions يُشغَّل تلقائياً:
   - يختبر الكود (pytest)
   - يبني صورة Docker
   - يرفعها لـ ECR
   - ينشرها على Kubernetes
        ↓
3. Kubernetes يشغّل الـ API في 3 نسخ متوازية
        ↓
4. المستشفى يرسل بيانات مريض لـ POST /api/v1/predict
        ↓
5. الـ API يحسب درجة الخطر ويرد بـ: risk=0.75, level=HIGH
        ↓
6. Prometheus يجمع مقاييس الأداء كل 15 ثانية
        ↓
7. Grafana يعرض لوحة تحكم بالرسوم البيانية
        ↓
8. إذا حدثت مشكلة → Prometheus يرسل تنبيهاً
```
