import uuid
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageOps

imagems_dir = Path("imagens")

def processar_imagem(contento: bytes) -> str:
    """
    Processa e redimensiona uma imagem para o tamanho padrão 512x512.
    
    Args:
        contento: bytes da imagem
        
    Returns:
        str: nome do arquivo salvo
        
    Raises:
        ValueError: se a imagem for inválida ou corrompida
    """
    # Garante que a pasta existe
    imagems_dir.mkdir(exist_ok=True)

    try:
        # Abrir e validar imagem
        with Image.open(BytesIO(contento)) as original:
            # Validar que a imagem tem dimensões válidas
            if original.width <= 0 or original.height <= 0:
                raise ValueError(f"Dimensões inválidas: {original.width}x{original.height}")
            
            # Corrigir orientação EXIF
            img = ImageOps.exif_transpose(original)
            
            # Validar novamente após transformação EXIF
            if img.width <= 0 or img.height <= 0:
                raise ValueError(f"Dimensões inválidas após EXIF: {img.width}x{img.height}")
            
            # Converter para RGB
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
            
            # Redimensionar para 512x512
            img = img.resize((512, 512), Image.Resampling.LANCZOS)
            
            # Gerar nome para o arquivo
            nome_arquivo = f"{uuid.uuid4()}.jpg"
            caminho_arquivo = imagems_dir / nome_arquivo
            
            # Salvar com otimização
            img.save(caminho_arquivo, format="JPEG", quality=95, optimize=True)

        return nome_arquivo
        
    except Image.UnidentifiedImageError as e:
        raise ValueError(f"Arquivo não é uma imagem válida: {str(e)}")
    except ValueError as e:
        # Re-raise ValueError com contexto
        raise ValueError(f"Erro ao processar imagem: {str(e)}")
    except Exception as e:
        raise ValueError(f"Erro inesperado ao processar imagem: {str(e)}")