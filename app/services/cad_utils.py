import re
import subprocess
from pathlib import Path
import platform
import ezdxf

def convert_dwg_to_dxf(input_path: str, output_path: str) -> bool:
    output_dir = str(Path(output_path).parent)

    # 判断操作系统类型，选择对应的 ODAFileConverter 路径
    if platform.system() == "Darwin":  # macOS
        converter_path = "/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter"
    else:  # 默认使用 Linux 路径
        converter_path = "xvfb-run /usr/bin/ODAFileConverter"

    cmd = [
        converter_path,
        str(Path(input_path).parent),
        output_dir,
        "ACAD2007", "DXF", "0", "0", "*.dwg"
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        return result.returncode == 0
    except Exception as e:
        print(f"DWG 转换失败: {e}")
        return False


def decode_mtext_unicode(s: str) -> str:
    # 去除 {\...;} 富文本格式
    s = re.sub(r'\{\\.*?;([^}]+)\}', r'\1', s)

    def replacer(match):
        hex_str = match.group(1)
        # 若是奇数位，补前导零
        if len(hex_str) % 2 == 1:
            hex_str = "0" + hex_str
        try:
            byte_data = bytes.fromhex(hex_str)
            return byte_data.decode("gbk")
        except Exception as e:
            print(f"解码失败: \\M+{hex_str} -> {e}")
            return ''  # 跳过非法编码
    return re.sub(r'\\M\+([0-9A-Fa-f]+)', replacer, s)

def extract_dxf_info(dxf_path: str) -> dict:
    encodings = ['utf-8', 'gbk', 'gb2312']
    doc = None

    for encoding in encodings:
        try:
            doc = ezdxf.readfile(dxf_path, encoding=encoding)
            print(f"使用 {encoding} 编码成功读取文件")
            break
        except UnicodeDecodeError:
            print(f"使用 {encoding} 编码读取失败，尝试其他编码...")
            continue

    if doc is None:
        print("所有编码尝试失败，使用默认方式读取")
        doc = ezdxf.readfile(dxf_path)

    msp = doc.modelspace()

    info = {
        "layers": [decode_mtext_unicode(layer.dxf.name) for layer in doc.layers],
        "entities": []
    }

    for entity in msp:
        entity_data = {
            "type": entity.dxftype(),
            "layer": decode_mtext_unicode(entity.dxf.layer),
            "color": entity.dxf.color,
            "linetype": entity.dxf.linetype
        }

        if entity.dxftype() in ("TEXT", "MTEXT", "ATTRIB"):
            raw = ""
            if entity.dxftype() == "TEXT" or entity.dxftype() == "ATTRIB":
                raw = entity.dxf.text or ""
            elif entity.dxftype() == "MTEXT":
                raw = entity.text or ""

            # print(f"[原始] {entity.dxftype()} 文本: {repr(raw)}")
            decoded = decode_mtext_unicode(raw)
            # print(f"[解码] {entity.dxftype()} 文本: {decoded}")

            entity_data["text"] = decoded
            entity_data["insert"] = list(entity.dxf.insert)

        elif entity.dxftype() == "LINE":
            entity_data["start"] = list(entity.dxf.start)
            entity_data["end"] = list(entity.dxf.end)

        elif entity.dxftype() == "LWPOLYLINE":
            entity_data["points"] = [list(point) for point in entity.get_points()]

        elif entity.dxftype() == "CIRCLE":
            entity_data["center"] = list(entity.dxf.center)
            entity_data["radius"] = entity.dxf.radius

        elif entity.dxftype() == "ARC":
            entity_data["center"] = list(entity.dxf.center)
            entity_data["radius"] = entity.dxf.radius
            entity_data["start_angle"] = entity.dxf.start_angle
            entity_data["end_angle"] = entity.dxf.end_angle

        elif entity.dxftype() == "ELLIPSE":
            entity_data["center"] = list(entity.dxf.center)
            entity_data["major_axis"] = list(entity.dxf.major_axis)
            entity_data["ratio"] = entity.dxf.ratio
            entity_data["start_param"] = entity.dxf.start_param
            entity_data["end_param"] = entity.dxf.end_param

        elif entity.dxftype() == "SPLINE":
            entity_data["degree"] = entity.dxf.degree
            entity_data["control_points"] = [list(pt) for pt in entity.control_points]

        info["entities"].append(entity_data)

    return info