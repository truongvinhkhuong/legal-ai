"""Form wizard step definitions per template type."""

from __future__ import annotations

from src.api.models import FormFieldDef, FormStep

# ---------------------------------------------------------------------------
# Shared field sets
# ---------------------------------------------------------------------------

_EMPLOYER_FIELDS = [
    FormFieldDef(field_key="employer_name", label_vi="Ten doanh nghiep / Ho kinh doanh", field_type="text"),
    FormFieldDef(field_key="employer_address", label_vi="Dia chi", field_type="text"),
    FormFieldDef(field_key="employer_representative", label_vi="Nguoi dai dien", field_type="text"),
    FormFieldDef(field_key="employer_position", label_vi="Chuc vu", field_type="text", required=False, placeholder_vi="Giam doc"),
]

_EMPLOYEE_FIELDS = [
    FormFieldDef(field_key="employee_name", label_vi="Ho va ten nguoi lao dong", field_type="text"),
    FormFieldDef(field_key="employee_dob", label_vi="Ngay sinh", field_type="date"),
    FormFieldDef(field_key="employee_id_number", label_vi="So CCCD/CMND", field_type="text"),
    FormFieldDef(field_key="employee_address", label_vi="Dia chi thuong tru", field_type="text"),
]

_REGION_FIELD = FormFieldDef(
    field_key="region", label_vi="Vung luong toi thieu", field_type="select",
    options=[
        {"value": "vung_1", "label": "Vung I (TP.HCM, Ha Noi, Binh Duong, Dong Nai...)"},
        {"value": "vung_2", "label": "Vung II (Hai Phong, Da Nang, Can Tho...)"},
        {"value": "vung_3", "label": "Vung III"},
        {"value": "vung_4", "label": "Vung IV"},
    ],
)


# ---------------------------------------------------------------------------
# HDLD Xac dinh thoi han
# ---------------------------------------------------------------------------

HDLD_XDTH_STEPS = [
    FormStep(step_number=1, title_vi="Thong tin doanh nghiep", fields=_EMPLOYER_FIELDS),
    FormStep(step_number=2, title_vi="Thong tin nguoi lao dong", fields=_EMPLOYEE_FIELDS),
    FormStep(
        step_number=3, title_vi="Cong viec & dia diem",
        fields=[
            FormFieldDef(field_key="job_title", label_vi="Vi tri / chuc danh", field_type="text"),
            FormFieldDef(field_key="work_location", label_vi="Dia diem lam viec", field_type="text"),
            FormFieldDef(field_key="job_description", label_vi="Mo ta cong viec chinh", field_type="textarea", required=False),
        ],
    ),
    FormStep(
        step_number=4, title_vi="Thoi han & thu viec",
        fields=[
            FormFieldDef(field_key="contract_duration_months", label_vi="Thoi han hop dong (thang)", field_type="number", placeholder_vi="12"),
            FormFieldDef(field_key="start_date", label_vi="Ngay bat dau lam viec", field_type="date"),
            FormFieldDef(field_key="probation_days", label_vi="Thoi gian thu viec (ngay)", field_type="number", required=False, help_text_vi="De trong neu khong co thu viec"),
            FormFieldDef(
                field_key="job_level", label_vi="Cap bac cong viec", field_type="select", required=False,
                options=[
                    {"value": "quan_ly", "label": "Quan ly / Giam doc (thu viec toi da 180 ngay)"},
                    {"value": "chuyen_mon", "label": "Chuyen mon cao dang tro len (toi da 60 ngay)"},
                    {"value": "trung_cap", "label": "Trung cap / cong nhan ky thuat (toi da 30 ngay)"},
                    {"value": "khac", "label": "Cong viec khac (toi da 6 ngay)"},
                ],
                help_text_vi="Anh huong toi thoi gian thu viec toi da",
            ),
        ],
    ),
    FormStep(
        step_number=5, title_vi="Luong & phuc loi",
        fields=[
            FormFieldDef(field_key="salary", label_vi="Muc luong (VND/thang)", field_type="number"),
            FormFieldDef(field_key="probation_salary", label_vi="Luong thu viec (VND/thang)", field_type="number", required=False, help_text_vi="Toi thieu 85% luong chinh thuc"),
            FormFieldDef(field_key="salary_payment_day", label_vi="Ngay tra luong hang thang", field_type="number", placeholder_vi="5"),
            _REGION_FIELD,
        ],
    ),
    FormStep(
        step_number=6, title_vi="Thoi gio lam viec",
        fields=[
            FormFieldDef(field_key="hours_per_week", label_vi="So gio lam / tuan", field_type="number", placeholder_vi="48"),
            FormFieldDef(field_key="working_days", label_vi="So ngay lam / tuan", field_type="number", placeholder_vi="6"),
            FormFieldDef(field_key="work_schedule", label_vi="Gio lam viec cu the", field_type="text", required=False, placeholder_vi="8:00 - 17:00"),
        ],
    ),
    FormStep(step_number=7, title_vi="Xac nhan & tao hop dong", fields=[]),
]


# ---------------------------------------------------------------------------
# HDLD Khong xac dinh thoi han
# ---------------------------------------------------------------------------

HDLD_KXDTH_STEPS = [
    FormStep(step_number=1, title_vi="Thong tin doanh nghiep", fields=_EMPLOYER_FIELDS),
    FormStep(step_number=2, title_vi="Thong tin nguoi lao dong", fields=_EMPLOYEE_FIELDS),
    FormStep(
        step_number=3, title_vi="Cong viec & dia diem",
        fields=[
            FormFieldDef(field_key="job_title", label_vi="Vi tri / chuc danh", field_type="text"),
            FormFieldDef(field_key="work_location", label_vi="Dia diem lam viec", field_type="text"),
        ],
    ),
    FormStep(
        step_number=4, title_vi="Luong & phuc loi",
        fields=[
            FormFieldDef(field_key="start_date", label_vi="Ngay bat dau lam viec", field_type="date"),
            FormFieldDef(field_key="salary", label_vi="Muc luong (VND/thang)", field_type="number"),
            FormFieldDef(field_key="salary_payment_day", label_vi="Ngay tra luong hang thang", field_type="number", placeholder_vi="5"),
            _REGION_FIELD,
        ],
    ),
    FormStep(
        step_number=5, title_vi="Thoi gio lam viec",
        fields=[
            FormFieldDef(field_key="hours_per_week", label_vi="So gio lam / tuan", field_type="number", placeholder_vi="48"),
            FormFieldDef(field_key="working_days", label_vi="So ngay lam / tuan", field_type="number", placeholder_vi="6"),
        ],
    ),
    FormStep(step_number=6, title_vi="Xac nhan & tao hop dong", fields=[]),
]


# ---------------------------------------------------------------------------
# HD Thu viec
# ---------------------------------------------------------------------------

HD_THU_VIEC_STEPS = [
    FormStep(step_number=1, title_vi="Thong tin doanh nghiep", fields=_EMPLOYER_FIELDS),
    FormStep(step_number=2, title_vi="Thong tin nguoi lao dong", fields=_EMPLOYEE_FIELDS),
    FormStep(
        step_number=3, title_vi="Noi dung thu viec",
        fields=[
            FormFieldDef(field_key="job_title", label_vi="Vi tri thu viec", field_type="text"),
            FormFieldDef(field_key="work_location", label_vi="Dia diem", field_type="text"),
            FormFieldDef(field_key="probation_days", label_vi="Thoi gian thu viec (ngay)", field_type="number"),
            FormFieldDef(field_key="salary", label_vi="Luong thu viec (VND/thang)", field_type="number"),
            _REGION_FIELD,
        ],
    ),
    FormStep(step_number=4, title_vi="Xac nhan & tao hop dong", fields=[]),
]


# ---------------------------------------------------------------------------
# HD Thue mat bang
# ---------------------------------------------------------------------------

HD_THUE_MAT_BANG_STEPS = [
    FormStep(
        step_number=1, title_vi="Thong tin ben cho thue",
        fields=[
            FormFieldDef(field_key="lessor_name", label_vi="Ten ben cho thue", field_type="text"),
            FormFieldDef(field_key="lessor_id_number", label_vi="So CCCD/CMND", field_type="text"),
            FormFieldDef(field_key="lessor_address", label_vi="Dia chi", field_type="text"),
        ],
    ),
    FormStep(
        step_number=2, title_vi="Thong tin ben thue",
        fields=[
            FormFieldDef(field_key="lessee_name", label_vi="Ten ben thue", field_type="text"),
            FormFieldDef(field_key="lessee_id_number", label_vi="So CCCD/CMND hoac DKKD", field_type="text"),
            FormFieldDef(field_key="lessee_address", label_vi="Dia chi", field_type="text"),
        ],
    ),
    FormStep(
        step_number=3, title_vi="Thong tin mat bang",
        fields=[
            FormFieldDef(field_key="property_address", label_vi="Dia chi mat bang cho thue", field_type="text"),
            FormFieldDef(field_key="property_area", label_vi="Dien tich (m2)", field_type="number", required=False),
            FormFieldDef(field_key="usage_purpose", label_vi="Muc dich su dung", field_type="text", placeholder_vi="Kinh doanh quan an"),
        ],
    ),
    FormStep(
        step_number=4, title_vi="Gia thue & thanh toan",
        fields=[
            FormFieldDef(field_key="rental_price", label_vi="Gia thue (VND/thang)", field_type="number"),
            FormFieldDef(field_key="deposit_amount", label_vi="Tien dat coc (VND)", field_type="number"),
            FormFieldDef(field_key="payment_method", label_vi="Phuong thuc thanh toan", field_type="text", placeholder_vi="Chuyen khoan hang thang"),
            FormFieldDef(field_key="rental_duration_months", label_vi="Thoi han thue (thang)", field_type="number"),
            FormFieldDef(field_key="start_date", label_vi="Ngay bat dau thue", field_type="date"),
        ],
    ),
    FormStep(step_number=5, title_vi="Xac nhan & tao hop dong", fields=[]),
]


# ---------------------------------------------------------------------------
# HD Dich vu
# ---------------------------------------------------------------------------

HD_DICH_VU_STEPS = [
    FormStep(
        step_number=1, title_vi="Thong tin ben cung cap",
        fields=[
            FormFieldDef(field_key="provider_name", label_vi="Ten ben cung cap dich vu", field_type="text"),
            FormFieldDef(field_key="provider_address", label_vi="Dia chi", field_type="text"),
            FormFieldDef(field_key="provider_representative", label_vi="Nguoi dai dien", field_type="text"),
        ],
    ),
    FormStep(
        step_number=2, title_vi="Thong tin ben su dung",
        fields=[
            FormFieldDef(field_key="client_name", label_vi="Ten ben su dung dich vu", field_type="text"),
            FormFieldDef(field_key="client_address", label_vi="Dia chi", field_type="text"),
            FormFieldDef(field_key="client_representative", label_vi="Nguoi dai dien", field_type="text"),
        ],
    ),
    FormStep(
        step_number=3, title_vi="Noi dung dich vu",
        fields=[
            FormFieldDef(field_key="service_description", label_vi="Mo ta dich vu", field_type="textarea"),
            FormFieldDef(field_key="service_fee", label_vi="Phi dich vu (VND)", field_type="number"),
            FormFieldDef(field_key="payment_terms", label_vi="Dieu khoan thanh toan", field_type="text", placeholder_vi="Thanh toan 50% truoc, 50% sau khi hoan thanh"),
            FormFieldDef(field_key="service_duration", label_vi="Thoi han thuc hien", field_type="text", placeholder_vi="30 ngay"),
        ],
    ),
    FormStep(step_number=4, title_vi="Xac nhan & tao hop dong", fields=[]),
]


# ---------------------------------------------------------------------------
# QD Cham dut HDLD
# ---------------------------------------------------------------------------

QD_CHAM_DUT_HDLD_STEPS = [
    FormStep(step_number=1, title_vi="Thong tin doanh nghiep", fields=_EMPLOYER_FIELDS),
    FormStep(
        step_number=2, title_vi="Thong tin nguoi lao dong",
        fields=[
            FormFieldDef(field_key="employee_name", label_vi="Ho va ten", field_type="text"),
            FormFieldDef(field_key="employee_position", label_vi="Chuc danh", field_type="text"),
            FormFieldDef(field_key="employee_department", label_vi="Phong ban", field_type="text", required=False),
        ],
    ),
    FormStep(
        step_number=3, title_vi="Noi dung cham dut",
        fields=[
            FormFieldDef(field_key="termination_reason", label_vi="Ly do cham dut", field_type="textarea"),
            FormFieldDef(field_key="termination_date", label_vi="Ngay cham dut", field_type="date"),
            FormFieldDef(field_key="original_contract_date", label_vi="Ngay ky HDLD goc", field_type="date"),
        ],
    ),
    FormStep(step_number=4, title_vi="Xac nhan & tao quyet dinh", fields=[]),
]


# ---------------------------------------------------------------------------
# Bien ban vi pham ky luat
# ---------------------------------------------------------------------------

BIEN_BAN_VI_PHAM_STEPS = [
    FormStep(step_number=1, title_vi="Thong tin doanh nghiep", fields=_EMPLOYER_FIELDS),
    FormStep(
        step_number=2, title_vi="Nguoi vi pham",
        fields=[
            FormFieldDef(field_key="employee_name", label_vi="Ho va ten", field_type="text"),
            FormFieldDef(field_key="employee_position", label_vi="Chuc danh", field_type="text"),
            FormFieldDef(field_key="employee_department", label_vi="Phong ban", field_type="text", required=False),
        ],
    ),
    FormStep(
        step_number=3, title_vi="Noi dung vi pham",
        fields=[
            FormFieldDef(field_key="violation_date", label_vi="Ngay vi pham", field_type="date"),
            FormFieldDef(field_key="violation_description", label_vi="Mo ta hanh vi vi pham", field_type="textarea"),
            FormFieldDef(field_key="violation_evidence", label_vi="Chung cu / bang chung", field_type="textarea", required=False),
            FormFieldDef(field_key="employee_explanation", label_vi="Giai trinh cua nguoi lao dong", field_type="textarea", required=False),
        ],
    ),
    FormStep(step_number=4, title_vi="Xac nhan & tao bien ban", fields=[]),
]


# ---------------------------------------------------------------------------
# Template metadata + form schema registry
# ---------------------------------------------------------------------------

TEMPLATE_METADATA = {
    "hdld_xdth": {
        "name_vi": "Hop dong lao dong xac dinh thoi han",
        "description_vi": "Hop dong lao dong co thoi han cu the (6 thang, 1 nam, 2 nam...)",
        "category": "lao_dong",
    },
    "hdld_kxdth": {
        "name_vi": "Hop dong lao dong khong xac dinh thoi han",
        "description_vi": "Hop dong lao dong khong gioi han thoi gian",
        "category": "lao_dong",
    },
    "hd_thu_viec": {
        "name_vi": "Hop dong thu viec",
        "description_vi": "Hop dong cho giai doan thu viec truoc khi ky HDLD chinh thuc",
        "category": "lao_dong",
    },
    "hd_thue_mat_bang": {
        "name_vi": "Hop dong thue mat bang",
        "description_vi": "Hop dong thue mat bang kinh doanh, cua hang, van phong",
        "category": "thue",
    },
    "hd_dich_vu": {
        "name_vi": "Hop dong dich vu",
        "description_vi": "Hop dong cung cap dich vu giua 2 ben",
        "category": "dich_vu",
    },
    "qd_cham_dut_hdld": {
        "name_vi": "Quyet dinh cham dut hop dong lao dong",
        "description_vi": "Van ban quyet dinh cham dut HDLD (khi sa thai hoac het han)",
        "category": "lao_dong",
    },
    "bien_ban_vi_pham": {
        "name_vi": "Bien ban vi pham ky luat",
        "description_vi": "Bien ban ghi nhan hanh vi vi pham ky luat cua nguoi lao dong",
        "category": "lao_dong",
    },
}

TEMPLATE_FORM_SCHEMAS: dict[str, list[FormStep]] = {
    "hdld_xdth": HDLD_XDTH_STEPS,
    "hdld_kxdth": HDLD_KXDTH_STEPS,
    "hd_thu_viec": HD_THU_VIEC_STEPS,
    "hd_thue_mat_bang": HD_THUE_MAT_BANG_STEPS,
    "hd_dich_vu": HD_DICH_VU_STEPS,
    "qd_cham_dut_hdld": QD_CHAM_DUT_HDLD_STEPS,
    "bien_ban_vi_pham": BIEN_BAN_VI_PHAM_STEPS,
}
