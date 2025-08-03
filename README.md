# CAD 文件转换与解析服务

## 项目概述

本项目是一个基于 FastAPI 的 CAD 文件处理服务，提供以下核心功能：
- 接收 DWG/DXF 格式文件上传
- 自动将 DWG 文件转换为 DXF 格式
- 解析 DXF 文件内容，提取图层信息和 CAD 实体数据
- 返回结构化 JSON 格式的解析结果

服务主要用于 CAD 数据的自动化处理与分析，适用于需要从 CAD 文件中提取几何信息和文本内容的场景。

## 技术栈
- Python 3.12+
- FastAPI
- uv（依赖管理）
- ezdxf
- ODAFileConverter

## 注意事项
1. 默认将 DWG 转换为 ACAD2007 格式
2. 上传的文件名会自动生成 UUID 前缀以避免多用户冲突
3. 转换后的 DXF 文件名也会使用 UUID 前缀确保唯一性
4. 为确保多用户环境下的安全性，建议定期清理 upload_dir 和 converted_dir 目录
5. macOS 需使用完整路径运行 ODAFileConverter
## 项目结构
```
cad_conver/
├── app/
│   ├── api/
│   │   └── endpoints.py    # API 路由
│   ├── services/
│   │   └── cad_utils.py    # 核心处理逻辑
│   ├── upload_dir/         # 上传文件存储
│   ├── converted_dir/      # 转换后文件存储
│   └── main.py             # 服务入口
├── pyproject.toml          # 依赖配置
└── README.md               # 本文件
```

## 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/HuiTurn/CAD-Parse.git
cd cad_conver
```

## 配置说明

### 依赖管理（uv）

本项目使用 [uv](https://docs.astral.sh/uv/) 作为依赖管理工具，具有比 pip 更快的安装速度和更好的兼容性。

#### 安装 uv
```bash
pip install uv
```

#### 安装项目依赖
```bash
uv sync
```

#### 添加新依赖
```bash
uv add <package-name>
```

#### 更新依赖
```bash
uv update
```

#### 生成或更新 pyproject.toml
```bash
uv init
```
## 启动服务

### 开发模式（带热重载）
```bash
# 使用 start.sh 脚本（推荐）
./start.sh

# 或直接使用 uv 命令
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 生产模式
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```
## 支持实体类型
| 类型           | 包含属性                     |
|----------------|------------------------------|
| TEXT/MTEXT     | 文本内容、插入点             |
| LINE           | 起点、终点坐标               |
| CIRCLE         | 圆心、半径                   |
| ARC            | 圆心、半径、起止角度         |
| LWPOLYLINE     | 多段线顶点坐标               |
| SPLINE         | 控制点、曲线度数             |
## API 接口

### 上传 CAD 文件

```
POST /cad/upload/
```

使用 multipart/form-data 格式上传文件。

#### 请求示例

```bash
curl -X POST "http://localhost:8000/cad/upload/" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/your/file.dwg"
```

#### 响应示例

```
{
  "success": true,
  "data": {
    "layers": ["图层1", "图层2"],
    "entities": [
      {
        "type": "LINE",
        "layer": "图层名",
        "color": 7,
        "linetype": "CONTINUOUS",
        "start": [0.0, 0.0, 0.0],
        "end": [100.0, 100.0, 0.0]
      },
      {
        "type": "TEXT",
        "layer": "图层名",
        "color": 7,
        "linetype": "CONTINUOUS",
        "text": "示例文本",
        "insert": [10.0, 20.0, 0.0]
      }
    ]
  }
}