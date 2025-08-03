from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import re
import uuid
import httpx
from urllib.parse import urlparse

from app.services.cad_utils import convert_dwg_to_dxf, extract_dxf_info, extract_filename_from_cd

router = APIRouter()
UPLOAD_DIR = Path(__file__).parent.parent / "upload_dir"
CONVERTED_DIR = Path(__file__).parent.parent / "converted_dir"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CONVERTED_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/parse/")
async def parse(file: UploadFile = File(...)):
    """
    上传并解析 CAD 文件
    
    该接口接收 DWG 或 DXF 格式的 CAD 文件，如果是 DWG 格式会自动转换为 DXF 格式，
    然后解析 DXF 文件内容并返回结构化数据。
    
    - **file**: 上传的 CAD 文件，支持 dwg 或 dxf 格式
    
    Returns:
        JSONResponse: 包含解析结果的响应
            - success (bool): 是否成功
            - data (dict): 解析的 DXF 文件信息，包括图层和实体数据
    
    Raises:
        HTTPException: 
            - 400: 文件格式不支持
            - 500: DWG 转换失败或 DXF 解析失败
    """
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


@router.post("/parse_from_url/")
async def parse_from_url(url: str):
    """
    通过 URL 解析 CAD 文件
    
    该接口接收一个 CAD 文件的 URL，下载文件后进行处理。如果是 DWG 格式会自动转换为 DXF 格式，
    然后解析 DXF 文件内容并返回结构化数据。
    
    - **url**: CAD 文件的 URL 地址，支持 dwg 或 dxf 格式
    
    Returns:
        JSONResponse: 包含解析结果的响应
            - success (bool): 是否成功
            - data (dict): 解析的 DXF 文件信息，包括图层和实体数据
    
    Raises:
        HTTPException: 
            - 400: URL 无效或文件格式不支持
            - 502: 文件下载失败
            - 500: DWG 转换失败或 DXF 解析失败
    """
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise HTTPException(status_code=400, detail="无效的 URL")

    # 下载文件
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
            file_bytes = resp.content
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"下载文件失败: {str(e)}")

    # 获取文件名
    cd = resp.headers.get("content-disposition")
    filename = extract_filename_from_cd(cd)
    match = re.search('(^\S+)~', Path(parsed.path).name)

    if (not filename) and match:
        filename = match.group(1)

    # 统一加唯一前缀
    unique_filename = f"{uuid.uuid4()}_{filename}"
    upload_path = UPLOAD_DIR / unique_filename
    upload_path.write_bytes(file_bytes)

    # 扩展名校验（再次检查，防止 content-disposition 给的文件名后缀不对）
    suffix = upload_path.suffix.lstrip(".").lower()
    if suffix not in {"dwg", "dxf"}:
        raise HTTPException(status_code=400, detail="仅支持 dwg 或 dxf 格式")

    # 后续流程与 /upload/ 完全一致
    if suffix == "dwg":
        dxf_filename = f"{upload_path.stem}.dxf"
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