# AI Features -- Tinh nang AI nang cao

Cac tinh nang AI tao su khac biet cho Legal Intelligence Platform. Moi tinh nang duoc thiet ke de tan dung nen tang RAG hien co (hierarchical chunking, cross-reference graph, Vietnamese NLP).

---

## 1. Legal Impact Analysis -- Phan tich tac dong phap ly

### Muc dich

Khi van ban phap luat moi ban hanh (vd: Nghi dinh sua doi), tu dong phan tich van ban noi bo nao bi anh huong, o muc clause-level.

### Kien truc

```mermaid
graph TD
    Input["VB moi ban hanh\n(upload hoac auto-crawl)"]

    subgraph Analysis["Impact Analysis Engine"]
        Parse["Parse VB moi\n→ DocumentTree"]
        Diff["Clause-level Diff\nSo sanh tung Dieu/Khoan\nvoi VB cu da index"]
        Graph["Cross-ref Traversal\nDuyet graph: VB nao\ntham chieu toi VB bi sua?"]
        Score["Impact Scoring\nKHAN CAP / CAN RA SOAT\n/ KHONG ANH HUONG"]
    end

    subgraph Output["Impact Report"]
        Urgent["KHAN CAP\nDieu khoan bi thay the\nhoan toan"]
        Review["CAN RA SOAT\nDieu khoan lien quan\ngian tiep"]
        Safe["KHONG ANH HUONG\nCac VB khac"]
    end

    Input --> Parse --> Diff --> Graph --> Score
    Score --> Urgent & Review & Safe
```

### Implementation

```python
class LegalImpactAnalyzer:
    """Phan tich tac dong cua VB moi len VB noi bo da index."""

    async def analyze(
        self,
        new_doc_tree: DocumentTree,
        new_doc_meta: DocumentMetadata,
    ) -> ImpactReport:
        # 1. Tim VB cu ma VB moi thay the/sua doi (tu metadata hoac header)
        old_doc_refs = self._extract_amended_targets(new_doc_tree)

        # 2. Clause-level diff: moi Dieu trong VB moi vs VB cu
        clause_diffs = []
        for article in self._extract_articles(new_doc_tree):
            old_article = await self._find_matching_article(
                article.number, old_doc_refs
            )
            if old_article:
                diff = self._diff_clauses(old_article, article)
                clause_diffs.append(diff)

        # 3. Cross-reference traversal
        affected_docs = await self._find_referencing_docs(old_doc_refs)

        # 4. Score impact per affected document
        impacts = []
        for doc in affected_docs:
            score = self._score_impact(doc, clause_diffs)
            impacts.append(score)

        return ImpactReport(
            new_document=new_doc_meta,
            clause_diffs=clause_diffs,
            affected_documents=impacts,
        )
```

### Data requirements

- Cross-reference graph (da co tu ingestion pipeline)
- Document relationships table (PostgreSQL)
- Qdrant article-level search (da co payload indexes)

---

## 2. Compliance Gap Detector -- Phat hien lo hong tuan thu

### Muc dich

So sanh VB noi bo cua doanh nghiep voi yeu cau phap luat bat buoc, phat hien dieu khoan thieu hoac chua day du.

### Kien truc

```mermaid
graph TD
    subgraph Input["Input"]
        Internal["VB noi bo\n(da index trong Qdrant)"]
        Legal["VB phap luat bat buoc\n(da index hoac upload)"]
    end

    subgraph Engine["Compliance Engine"]
        Extract["Requirement Extraction\nLLM trich xuat yeu cau\nbat buoc tu luat goc\n(PHAI, bat buoc, it nhat)"]
        Match["Coverage Matching\nSemantic search: moi yeu cau\n→ tim dieu khoan tuong ung\ntrong VB noi bo"]
        Assess["Gap Assessment\nDu — Thieu — Lech\nConfidence score per match"]
    end

    subgraph Output["Compliance Report"]
        Covered["DA TUAN THU\nDieu khoan + dan chieu"]
        Missing["THIEU\nYeu cau luat\nchua co VB noi bo"]
        Partial["LECH\nCo nhung khong\nday du/dung"]
        Score["Ti le tuan thu: X%"]
    end

    Internal & Legal --> Engine
    Extract --> Match --> Assess
    Assess --> Covered & Missing & Partial & Score
```

### Requirement extraction prompt

```
Trich xuat tat ca yeu cau bat buoc tu van ban phap luat sau.
Chi lay nhung quy dinh co tu khoa: "phai", "bat buoc", "it nhat",
"khong duoc", "cam", "toi thieu", "toi da".

Voi moi yeu cau, tra ve:
- Dieu/Khoan/Diem cu the
- Noi dung yeu cau (tom tat 1-2 cau)
- Doi tuong ap dung (ai phai tuan thu)
- Muc do bat buoc (bat_buoc / khuyen_nghi)

Tra ve JSON array.
```

### Use cases

1. **Kiem tra Noi quy lao dong vs Bo luat Lao dong 2019 Dieu 118**
   - Dieu 118 liet ke 7 noi dung bat buoc trong noi quy
   - System check tung noi dung da co trong noi quy chua

2. **Kiem tra quy che tai chinh vs Luat Ke toan 2015**
   - Cac yeu cau ve so sach, bao cao, luu tru

3. **Kiem tra HD mau vs BLLD 2019 Dieu 21**
   - Dieu 21 liet ke noi dung bat buoc trong HDLD

---

## 3. Multi-document Legal Reasoning (Agentic RAG)

### Muc dich

Tra loi cau hoi phuc tap can tong hop tu nhieu van ban, voi kha nang tu phan ra cau hoi va truy xuat nhieu nguon.

### Kien truc

```mermaid
graph TD
    Q["Cau hoi phuc tap"]

    subgraph Agent["Agentic Pipeline"]
        Decompose["Decomposer\nPhan ra thanh sub-questions\n(LLM)"]
        Parallel["Parallel Retriever\nMoi sub-question → rieng\nretrieval pipeline"]
        Judge["Sufficiency Judge\nDa du context chua?\n(LLM evaluate)"]
        Extra["Additional Retrieval\nNeu thieu → them 1 round"]
        Synthesize["Synthesizer\nTong hop co cau truc\nvoi citations xuyen suot"]
    end

    Q --> Decompose
    Decompose --> Parallel
    Parallel --> Judge
    Judge -->|Chua du| Extra --> Judge
    Judge -->|Du| Synthesize

    style Agent fill:#dbeafe,stroke:#2563eb
```

### Vi du

**Cau hoi:** "Cong ty muon cho NV nghi viec do tai co cau. Can thuc hien nhung buoc gi, bao gom nghia vu tai chinh?"

**Decomposition:**
1. "Can cu phap ly cho nghi viec do tai co cau?" → BLLD Dieu 42
2. "Nghia vu thong bao truoc bao lau?" → BLLD Dieu 45 + ND 145
3. "Tro cap thoi viec tinh the nao?" → BLLD Dieu 46, 48
4. "Quy trinh noi bo cong ty?" → Noi quy Dieu 28

**Sufficiency check:** "Da cover tai co cau, thong bao, tro cap. Thieu: nghia vu voi cong doan (Dieu 42 K.3)" → Trigger them retrieval

### Implementation notes

- Max decomposition: 5 sub-questions
- Max retrieval rounds: 2 (tranh loop)
- Parallel retrieval per sub-question (asyncio.gather)
- Final synthesis temperature 0.05 (strict grounding)

---

## 4. Contract Risk Scoring + Clause Anomaly Detection

### Muc dich

Review hop dong tu doi tac, phat hien dieu khoan bat loi, thieu, hoac vi pham phap luat.

### Kien truc

```mermaid
graph TD
    Upload["Upload HD can review"]

    subgraph Parse["Parsing"]
        Extract["Clause Extraction\nParse HD thanh tung dieu khoan\n(Legal Structure Parser)"]
    end

    subgraph Analysis["4 Dimensions"]
        Legal["Legal Compliance\nMoi clause vs luat hien hanh\n(RAG query)"]
        Benchmark["Market Benchmark\nSo sanh voi HD cung loai\ntrong clause library"]
        Missing["Missing Clause\nDetect dieu khoan thieu\n(Force Majeure, bao mat...)"]
        Anomaly["Anomaly Detection\nPhat quá cao, thoi han\nbat hop ly, bat can xung"]
    end

    subgraph Output["Risk Report"]
        Score["Diem rui ro tong: X/10"]
        High["RUI RO CAO\nVi pham + bat loi"]
        Medium["RUI RO TB\nLech benchmark"]
        Low["RUI RO THAP\nCo the chap nhan"]
        Suggest["DE XUAT\nSua/bo sung cu the"]
    end

    Upload --> Extract
    Extract --> Legal & Benchmark & Missing & Anomaly
    Legal & Benchmark & Missing & Anomaly --> Score
    Score --> High & Medium & Low & Suggest
```

### Benchmark database

Clause library duoc xay dung tu:
- Template hop dong chuan cua doanh nghiep
- Hop dong da review truoc do (anonymized)
- Dieu khoan mau tu cac nguon phap ly

Moi clause luu voi metadata: `clause_type`, `typical_range` (vd: phat vi pham 5-10%), `required` (bool), `legal_basis` (Dieu/Khoan lien quan).

### Risk scoring formula

```
risk_score = (
    legal_violations * 3.0 +      # Nang nhat: vi pham luat
    missing_required * 2.0 +       # Thieu dieu khoan bat buoc
    anomaly_count * 1.5 +          # Bat thuong so voi benchmark
    unfavorable_terms * 1.0        # Dieu khoan bat loi
) / max_possible_score * 10
```

---

## 5. Legal Language Simplifier -- Dich thuat phap ly

### Muc dich

Chuyen doi ngon ngu phap ly phuc tap thanh ngon ngu thuong, giu chinh xac phap ly.

### Kien truc

```mermaid
graph LR
    Input["Dieu khoan goc\n+ metadata"]
    Simplify["Simplification Engine\nLLM simplify\nGiu so hieu, Dieu/Khoan\nThem vi du thuc te"]
    Validate["Faithfulness Validator\nSemantic similarity\ngoc vs don gian\nScore >= 0.85"]
    Output["Ban don gian\n+ Link ban goc\n+ Faithfulness score"]

    Input --> Simplify --> Validate --> Output
    Validate -->|Score < 0.85| Simplify
```

### Simplification prompt

```
Dich doan van ban phap ly sau sang ngon ngu thuong cho nguoi
khong chuyen luat hieu duoc.

QUY TAC:
1. Giu nguyen so hieu van ban, Dieu/Khoan/Diem
2. Giu nguyen y nghia phap ly chinh xac
3. Them vi du cu the neu co the
4. Dung bullet points cho nhieu muc
5. Giai thich thuat ngu phap ly trong ngoac
6. Khong them y kien ca nhan

Van ban goc ({doc_number}, {hierarchy_path}):
{original_text}

Ban don gian:
```

### Faithfulness validation

So sanh semantic giua ban goc va ban don gian:
- Embedding similarity >= 0.85 → PASS
- NER check: tat ca entity (so hieu, ngay, so tien) phai xuat hien trong ban don gian
- Negation check: khong duoc dao nghia (vd: "cam" → "duoc phep")

---

## 6. Proactive Legal Alert System

### Muc dich

Tu dong phat hien VB phap luat moi anh huong toi tenant va thong bao kip thoi.

### Kien truc

```mermaid
graph TD
    subgraph Source["Nguon VB moi"]
        Crawl["Auto-crawl\nvbpl.vn\nthuvienphapluat.vn"]
        Upload["Admin upload\nVB moi"]
        API["External API\nPartner feeds"]
    end

    subgraph Process["Processing"]
        Parse["Parse VB moi"]
        Relevance["Relevance Scoring\nvs tenant profile:\n- Nganh nghe\n- VB noi bo hien co\n- Query history (topics)"]
        Impact["Impact Analysis\n(Module 1)\nNeu relevance cao"]
    end

    subgraph Delivery["Alert Delivery"]
        InApp["In-app notification"]
        Email["Email digest\n(daily/weekly)"]
        Slack["Slack webhook"]
        Action["Action items\nper phong ban"]
    end

    Source --> Parse --> Relevance
    Relevance -->|Cao| Impact --> Delivery
    Relevance -->|Thap| Discard["Archive\n(khong alert)"]
```

### Relevance scoring

```python
def score_relevance(new_doc, tenant_profile):
    score = 0.0

    # 1. Industry match (linh_vuc)
    if overlap(new_doc.linh_vuc, tenant_profile.industries):
        score += 3.0

    # 2. Doc type match (cung loai VB noi bo da co)
    if new_doc.doc_type in tenant_profile.existing_doc_types:
        score += 2.0

    # 3. Topic similarity (embedding vs tenant's VB noi bo)
    topic_sim = cosine_similarity(
        embed(new_doc.summary),
        tenant_profile.topic_centroid,
    )
    score += topic_sim * 3.0

    # 4. Query history (tenant hay hoi ve topic nay)
    if new_doc.topics & tenant_profile.frequent_query_topics:
        score += 2.0

    return score / 10.0  # normalize 0-1
```

### Alert configuration per tenant

| Setting | Mo ta | Default |
|---------|-------|---------|
| `alert_threshold` | Score toi thieu de alert | 0.5 |
| `delivery_channels` | In-app, email, slack | in-app |
| `frequency` | Real-time, daily digest, weekly | daily |
| `departments_filter` | Chi alert cho phong ban lien quan | all |
| `doc_types_filter` | Chi theo doi loai VB nao | all |

---

## 7. Legal Scenario Simulator

### Muc dich

Tra loi cau hoi dang "Neu...thi..." (what-if) bang cach phan tich nhieu VB va xay dung decision tree.

### Kien truc

```mermaid
graph TD
    Input["Mo ta tinh huong\n(ngon ngu tu nhien)"]

    subgraph Parse["Scenario Parser"]
        Extract["Trich xuat:\n- Chu the (employer/employee)\n- Hanh vi (sa thai, nghi...)\n- Dieu kien (thu viec, chinh thuc)\n- Boi canh (tai co cau, vi pham)"]
    end

    subgraph Analysis["Multi-path Analysis"]
        Retrieve["Retrieve tat ca VB lien quan\n(agentic multi-doc)"]
        Tree["Xay dung decision tree\nIF condition A → outcome X\nIF condition B → outcome Y"]
        Timeline["Timeline generator\nTruoc X ngay: lam gi\nNgay Y: lam gi\nSau Z ngay: lam gi"]
    end

    subgraph Output["Scenario Report"]
        Steps["BUOC BAT BUOC\nChecklist hanh dong\nvoi dan chieu luat"]
        Risks["RUI RO\nHau qua neu sai\nquy trinh"]
        Alt["PHUONG AN THAY THE\nCac lua chon khac"]
    end

    Input --> Extract --> Retrieve --> Tree --> Timeline
    Timeline --> Steps & Risks & Alt
```

### Vi du scenarios

1. "Cong ty muon cho NV nghi viec do tai co cau"
2. "NV nghi viec khong bao truoc, cong ty xu ly the nao"
3. "Cong ty muon thay doi gio lam viec"
4. "NV bi tai nan lao dong, trach nhiem cua cong ty"
5. "Cong ty muon ky HD thoi vu thay vi chinh thuc"

### Scenario parser prompt

```
Phan tich tinh huong phap ly sau va trich xuat:

1. CHU THE: Ai la ben thuc hien hanh vi (employer/employee/ca hai)
2. HANH VI: Hanh dong cu the (sa thai, nghi viec, ky HD, thay doi...)
3. DIEU KIEN: Trang thai hien tai (thu viec, chinh thuc, hop dong xac dinh thoi han...)
4. BOI CANH: Ly do/hoan canh (tai co cau, vi pham ky luat, thoa thuan...)
5. CAU HOI CHINH: Nguoi dung muon biet gi (quy trinh, hau qua, nghia vu tai chinh...)

Tra ve JSON.

Tinh huong: {scenario_text}
```

---

## 8. Ma tran uu tien phat trien

```mermaid
quadrantChart
    title AI Features Priority Matrix
    x-axis Low Business Value --> High Business Value
    y-axis Low Complexity --> High Complexity
    quadrant-1 Do Later
    quadrant-2 Strategic Investment
    quadrant-3 Quick Wins
    quadrant-4 High Priority

    Legal Impact Analysis: [0.85, 0.55]
    Contract Risk Scoring: [0.90, 0.70]
    Compliance Gap Detector: [0.75, 0.50]
    Agentic Multi-doc: [0.70, 0.75]
    Legal Language Simplifier: [0.50, 0.25]
    Proactive Alert: [0.65, 0.50]
    Scenario Simulator: [0.60, 0.80]
```

### Thu tu trien khai khuyen nghi

| Uu tien | Tinh nang | Ly do |
|---------|-----------|-------|
| P0 | Legal Language Simplifier | Complexity thap, wow effect cao, lam truoc |
| P0 | Legal Impact Analysis | Gia tri kinh doanh cao nhat, nen tang cross-ref da co |
| P1 | Contract Risk Scoring | Revenue driver cho contract drafting module |
| P1 | Compliance Gap Detector | Gia tri cao cho enterprise, dung RAG san co |
| P1 | Proactive Alert | Retention feature, dung Impact Analysis da build |
| P2 | Agentic Multi-doc | Complex nhung cai thien chat luong Q&A |
| P2 | Scenario Simulator | Can Agentic RAG da build truoc |

---

## 9. Shared AI Infrastructure

Cac tinh nang tren chia se chung:

| Component | Dung boi | Mo ta |
|-----------|---------|-------|
| RAG Pipeline | Tat ca | Vector search + rerank + LLM |
| Structure Parser | Impact, Risk, Gap | Parse VB thanh Dieu/Khoan tree |
| Cross-ref Graph | Impact, Alert, Agentic | Quan he giua VB |
| Embedding Service | Tat ca | Voyage AI shared client |
| LLM Service | Tat ca | DeepSeek/OpenAI shared client |
| Clause Library | Risk, Drafting | Vector DB dieu khoan mau |
| Audit Logger | Tat ca | PostgreSQL audit trail |
