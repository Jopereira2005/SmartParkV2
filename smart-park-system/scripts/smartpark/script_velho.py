import os
import cv2
import numpy as np
import requests

# Configuração do endpoint
ENDPOINT = "end-point"

# Ativa/desativa janela de debug
DEBUG = False  # True = mostra vídeo processado, False = só resultado final

# Lista de vagas (cada uma é um polígono)
vagas = [
    #        X1           Y1         X2           Y2
    np.array([(223, 147), (406, 149), (353, 429), (157, 426)]),  # Vaga 1
    np.array([(414, 147), (600, 150), (566, 430), (361, 430)]),  # Vaga 2
    np.array([(607, 145), (780, 150), (740, 430), (560, 430)]),  # Vaga 3
    np.array([(830, 150), (1010, 150), (970, 430), (790, 430)]),  # Vaga 4
    np.array([(1050, 150), (1290, 150), (1300, 430), (1010, 430)]),  # Vaga 5
    np.array([(1300, 150), (1520, 150), (1560, 430), (1310, 430)]),  # Vaga 6
    np.array([(1530, 140), (1720, 140), (1780, 420), (1570, 420)]),  # Vaga 7
]

# Estado anterior das vagas
estado_vagas = [False] * len(vagas)

# Caminho dinâmico para o vídeo (relativo ao diretório do script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_PATH = os.path.join(SCRIPT_DIR, ".", "videos", "video.mp4")
video = cv2.VideoCapture(VIDEO_PATH)
while True:
    check, img = video.read()
    if not check:
        break

    # 🔹 Reduz o tamanho da imagem (50%)
    img = cv2.resize(img, (0, 0), fx=0.5, fy=0.5)

    # Conversão para escala de cinza
    imgCinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Suavização para reduzir ruído
    imgBlur = cv2.medianBlur(imgCinza, 5)

    # Dilatação (realça áreas claras/objetos)
    kernel = np.ones((3, 3), np.int8)
    imgDil = cv2.dilate(imgBlur, kernel)

    qtVagasAbertas = 0
    for i, vaga in enumerate(vagas):
        # Ajuste dos polígonos para o novo tamanho
        vaga_resized = (vaga * 0.5).astype(np.int32)

        mask = np.zeros(imgDil.shape, dtype=np.uint8)
        cv2.fillPoly(mask, [vaga_resized], 255)

        recorte = cv2.bitwise_and(imgDil, mask)
        qtPxBranco = cv2.countNonZero(recorte)

        cv2.putText(
            img,
            str(qtPxBranco),
            tuple(vaga_resized[0]),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

        ocupada = qtPxBranco > 1500  # 🔹 reduzido pois a imagem ficou menor

        if ocupada != estado_vagas[i]:
            evento = "entrada" if ocupada else "saida"
            dados = {"vaga": i + 1, "evento": evento}
            try:
                requests.post(ENDPOINT, json=dados, timeout=2)
                print(f"Enviado: {dados}")
            except Exception as e:
                print(f"Erro ao enviar para o endpoint: {e}")

            estado_vagas[i] = ocupada

        cor = (0, 0, 255) if ocupada else (0, 255, 0)
        cv2.polylines(img, [vaga_resized], True, cor, 3)

        if not ocupada:
            qtVagasAbertas += 1

    # Painel com vagas livres
    cv2.rectangle(img, (20, 0), (280, 40), (255, 0, 0), -1)
    cv2.putText(
        img,
        f"LIVRE: {qtVagasAbertas}/{len(vagas)}",
        (25, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
    )

    # Sempre mostra o resultado final
    cv2.imshow("video", img)

    # Só mostra a janela em cinza se DEBUG=True
    if DEBUG:
        cv2.imshow("video Processado", imgDil)

    if cv2.waitKey(10) & 0xFF == 27:
        break

video.release()
cv2.destroyAllWindows()
