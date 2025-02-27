import segno
import base64
from io import BytesIO


def generate_rezume_qr(rezume, rezume_jobs, time):
    # Формируем информацию для QR-кода
    info = f"Резюме №{rezume.id}\nОписание: {rezume.description}\n\n"

    completed_at_str = time.strftime('%Y-%m-%d %H:%M:%S')
    info += f"Дата и время завершения резюме: {completed_at_str}"

    # Генерация QR-кода
    qr = segno.make(info)
    buffer = BytesIO()
    qr.save(buffer, kind='png')
    buffer.seek(0)

    # Конвертация изображения в base64
    qr_image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    return qr_image_base64