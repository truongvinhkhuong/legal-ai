"""Hard-coded compliance checklists per Vietnamese law.

Each checklist item includes keywords for deterministic matching
and a legal basis for display.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChecklistItem:
    id: str
    title_vi: str
    description_vi: str
    legal_basis: str
    keywords: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Noi quy lao dong — BLLD 2019 Dieu 118 Khoan 2
# ---------------------------------------------------------------------------

NOI_QUY_CHECKLIST: list[ChecklistItem] = [
    ChecklistItem(
        id="nq_01",
        title_vi="Thời giờ làm việc, thời giờ nghỉ ngơi",
        description_vi="Quy định về giờ làm, giờ nghỉ, ca kíp, nghỉ phép",
        legal_basis="BLLĐ 2019 Điều 118 Khoản 2 Điểm a",
        keywords=["thoi gio lam viec", "thoi gio nghi ngoi", "gio lam", "nghi phep",
                   "ca", "kip", "lam viec", "nghi ngoi", "thời giờ", "nghỉ ngơi"],
    ),
    ChecklistItem(
        id="nq_02",
        title_vi="Trật tự tại nơi làm việc",
        description_vi="Quy định về trật tự, nề nếp, kỷ luật tại nơi làm việc",
        legal_basis="BLLĐ 2019 Điều 118 Khoản 2 Điểm b",
        keywords=["trat tu", "ne nep", "ky luat", "noi lam viec", "trật tự",
                   "kỷ luật", "nề nếp"],
    ),
    ChecklistItem(
        id="nq_03",
        title_vi="An toàn, vệ sinh lao động",
        description_vi="Quy định về an toàn lao động, vệ sinh, phòng cháy chữa cháy",
        legal_basis="BLLĐ 2019 Điều 118 Khoản 2 Điểm c",
        keywords=["an toan", "ve sinh", "lao dong", "phong chay", "chua chay",
                   "an toàn", "vệ sinh", "phòng cháy"],
    ),
    ChecklistItem(
        id="nq_04",
        title_vi="Bảo vệ tài sản, bí mật công nghệ, kinh doanh",
        description_vi="Quy định về bảo vệ tài sản, bí mật kinh doanh, sở hữu trí tuệ",
        legal_basis="BLLĐ 2019 Điều 118 Khoản 2 Điểm d",
        keywords=["bao ve tai san", "bi mat", "cong nghe", "kinh doanh",
                   "so huu tri tue", "bảo vệ", "tài sản", "bí mật"],
    ),
    ChecklistItem(
        id="nq_05",
        title_vi="Vi phạm kỷ luật lao động và hình thức xử lý",
        description_vi="Quy định các hành vi vi phạm và hình thức kỷ luật tương ứng",
        legal_basis="BLLĐ 2019 Điều 118 Khoản 2 Điểm đ",
        keywords=["vi pham", "ky luat", "xu ly", "hinh thuc", "khien trach",
                   "cach chuc", "sa thai", "vi phạm", "kỷ luật", "xử lý"],
    ),
    ChecklistItem(
        id="nq_06",
        title_vi="Trách nhiệm vật chất",
        description_vi="Quy định về bồi thường thiệt hại khi vi phạm",
        legal_basis="BLLĐ 2019 Điều 118 Khoản 2 Điểm e",
        keywords=["trach nhiem vat chat", "boi thuong", "thiet hai",
                   "trách nhiệm vật chất", "bồi thường"],
    ),
    ChecklistItem(
        id="nq_07",
        title_vi="Phòng, chống quấy rối tình dục tại nơi làm việc",
        description_vi="Quy định phòng chống quấy rối tình dục, trình tự xử lý",
        legal_basis="BLLĐ 2019 Điều 118 Khoản 2 Điểm g",
        keywords=["quay roi", "tinh duc", "quấy rối", "tình dục",
                   "phong chong quay roi", "phòng chống quấy rối"],
    ),
]


# ---------------------------------------------------------------------------
# HDLD — BLLD 2019 Dieu 21 Khoan 1
# ---------------------------------------------------------------------------

HDLD_CHECKLIST: list[ChecklistItem] = [
    ChecklistItem(
        id="hdld_01",
        title_vi="Tên, địa chỉ người sử dụng lao động",
        description_vi="Tên và địa chỉ trụ sở của người sử dụng lao động",
        legal_basis="BLLĐ 2019 Điều 21 Khoản 1 Điểm a",
        keywords=["ten", "dia chi", "nguoi su dung", "cong ty", "doanh nghiep",
                   "tên", "địa chỉ", "người sử dụng"],
    ),
    ChecklistItem(
        id="hdld_02",
        title_vi="Người đại diện hợp pháp",
        description_vi="Họ tên, chức danh người đại diện ký hợp đồng",
        legal_basis="BLLĐ 2019 Điều 21 Khoản 1 Điểm a",
        keywords=["dai dien", "hop phap", "chuc danh", "nguoi ky",
                   "đại diện", "hợp pháp"],
    ),
    ChecklistItem(
        id="hdld_03",
        title_vi="Họ tên, ngày sinh người lao động",
        description_vi="Thông tin cá nhân của người lao động",
        legal_basis="BLLĐ 2019 Điều 21 Khoản 1 Điểm b",
        keywords=["ho ten", "ngay sinh", "nguoi lao dong", "cccd", "cmnd",
                   "họ tên", "ngày sinh", "người lao động"],
    ),
    ChecklistItem(
        id="hdld_04",
        title_vi="Công việc và địa điểm làm việc",
        description_vi="Mô tả công việc cụ thể và địa điểm làm việc",
        legal_basis="BLLĐ 2019 Điều 21 Khoản 1 Điểm c",
        keywords=["cong viec", "dia diem", "lam viec", "chuc danh",
                   "công việc", "địa điểm", "làm việc"],
    ),
    ChecklistItem(
        id="hdld_05",
        title_vi="Thời hạn hợp đồng",
        description_vi="Loại hợp đồng (xác định/không xác định thời hạn) và thời hạn",
        legal_basis="BLLĐ 2019 Điều 21 Khoản 1 Điểm d",
        keywords=["thoi han", "hop dong", "xac dinh", "khong xac dinh",
                   "thời hạn", "hợp đồng"],
    ),
    ChecklistItem(
        id="hdld_06",
        title_vi="Mức lương, hình thức trả lương, thời hạn trả lương",
        description_vi="Lương cơ bản, phụ cấp, hình thức và kỳ trả lương",
        legal_basis="BLLĐ 2019 Điều 21 Khoản 1 Điểm đ",
        keywords=["luong", "tra luong", "phu cap", "hinh thuc tra",
                   "lương", "trả lương", "phụ cấp"],
    ),
    ChecklistItem(
        id="hdld_07",
        title_vi="Chế độ nâng bậc, nâng lương",
        description_vi="Quy định về nâng bậc, nâng lương",
        legal_basis="BLLĐ 2019 Điều 21 Khoản 1 Điểm e",
        keywords=["nang bac", "nang luong", "nâng bậc", "nâng lương"],
    ),
    ChecklistItem(
        id="hdld_08",
        title_vi="Thời giờ làm việc, thời giờ nghỉ ngơi",
        description_vi="Giờ làm việc, ngày nghỉ, nghỉ phép",
        legal_basis="BLLĐ 2019 Điều 21 Khoản 1 Điểm g",
        keywords=["gio lam", "nghi ngoi", "nghi phep", "ca lam",
                   "giờ làm", "nghỉ ngơi", "nghỉ phép"],
    ),
    ChecklistItem(
        id="hdld_09",
        title_vi="Trang bị bảo hộ lao động",
        description_vi="Trang thiết bị bảo hộ cho người lao động",
        legal_basis="BLLĐ 2019 Điều 21 Khoản 1 Điểm h",
        keywords=["bao ho", "trang bi", "bảo hộ", "trang bị"],
    ),
    ChecklistItem(
        id="hdld_10",
        title_vi="BHXH, BHYT, BHTN",
        description_vi="Quy định về bảo hiểm xã hội, y tế, thất nghiệp",
        legal_basis="BLLĐ 2019 Điều 21 Khoản 1 Điểm i",
        keywords=["bhxh", "bhyt", "bhtn", "bao hiem", "bảo hiểm",
                   "xa hoi", "y te", "that nghiep"],
    ),
]


# ---------------------------------------------------------------------------
# Thang bang luong — BLLD 2019 Dieu 93
# ---------------------------------------------------------------------------

THANG_BANG_LUONG_CHECKLIST: list[ChecklistItem] = [
    ChecklistItem(
        id="tbl_01",
        title_vi="Nhóm chức danh, vị trí công việc",
        description_vi="Liệt kê các nhóm chức danh và vị trí trong doanh nghiệp",
        legal_basis="BLLĐ 2019 Điều 93",
        keywords=["chuc danh", "vi tri", "nhom", "chức danh", "vị trí"],
    ),
    ChecklistItem(
        id="tbl_02",
        title_vi="Mức lương theo từng bậc",
        description_vi="Bảng lương chi tiết với các bậc lương cụ thể",
        legal_basis="BLLĐ 2019 Điều 93",
        keywords=["bac luong", "muc luong", "bậc lương", "mức lương", "he so"],
    ),
    ChecklistItem(
        id="tbl_03",
        title_vi="Điều kiện nâng bậc lương",
        description_vi="Tiêu chí và điều kiện để nâng bậc lương",
        legal_basis="BLLĐ 2019 Điều 93",
        keywords=["dieu kien", "nang bac", "tieu chi", "điều kiện", "nâng bậc"],
    ),
    ChecklistItem(
        id="tbl_04",
        title_vi="Phụ cấp lương",
        description_vi="Các loại phụ cấp và mức phụ cấp",
        legal_basis="BLLĐ 2019 Điều 93",
        keywords=["phu cap", "phụ cấp", "tro cap", "trợ cấp"],
    ),
]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

CHECKLISTS: dict[str, list[ChecklistItem]] = {
    "noi_quy": NOI_QUY_CHECKLIST,
    "hdld": HDLD_CHECKLIST,
    "thang_bang_luong": THANG_BANG_LUONG_CHECKLIST,
}

CHECKLIST_LABELS: dict[str, str] = {
    "noi_quy": "Nội quy lao động",
    "hdld": "Hợp đồng lao động",
    "thang_bang_luong": "Thang bảng lương",
}
