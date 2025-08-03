from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import uuid

from app.services.cad_utils import convert_dwg_to_dxf, extract_dxf_info

router = APIRouter()
UPLOAD_DIR = Path(__file__).parent.parent / "upload_dir"
CONVERTED_DIR = Path(__file__).parent.parent / "converted_dir"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CONVERTED_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload/")
async def upload(file: UploadFile = File(...)):
    suffix = file.filename.split(".")[-1].lower()
    if suffix not in ["dwg", "dxf"]:
        raise HTTPException(status_code=400, detail="仅支持 dwg 或 dxf 格式")

    # 生成唯一文件名避免冲突
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    upload_path = UPLOAD_DIR / unique_filename
    with open(upload_path, "wb") as f:
        f.write(await file.read())

    if suffix == "dwg":
        # 转换后的文件也使用唯一文件名
        dxf_filename = f"{uuid.uuid4()}_{upload_path.stem}.dxf"
        dxf_path = CONVERTED_DIR / dxf_filename
        if not convert_dwg_to_dxf(str(upload_path), str(dxf_path)):
            raise HTTPException(status_code=500, detail="DWG 转换失败")
    else:
        dxf_path = upload_path

    try:
        info = extract_dxf_info(str(dxf_path))
        return JSONResponse(content={"success": True, "data": info})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DXF 解析失败: {str(e)}")