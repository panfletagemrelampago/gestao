import os
import cloudinary
import cloudinary.uploader
from flask import current_app


class CloudinaryService:
    @staticmethod
    def configure():
        # Alterado para ler diretamente do Sistema (Render) com os.environ.get
        cloudinary.config(
            cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
            api_key=os.environ.get('CLOUDINARY_API_KEY'),
            api_secret=os.environ.get('CLOUDINARY_API_SECRET'),
            secure=True
        )

    @staticmethod
    def upload_image(file_to_upload, folder="auditorias"):
        # Garante a configuração antes de tentar o upload
        CloudinaryService.configure()

        # Verificação de segurança para o Log do Render
        if not os.environ.get('CLOUDINARY_API_KEY'):
            current_app.logger.error("ERRO: CLOUDINARY_API_KEY não encontrada no ambiente do servidor.")
            return None

        try:
            result = cloudinary.uploader.upload(file_to_upload, folder=folder)
            return result.get("secure_url")
        except Exception as e:
            current_app.logger.error(f"Erro no upload para o Cloudinary: {e}")
            return None